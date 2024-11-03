import gc

import pandas as pd

from time import time
from conf import settings
from loguru import logger
from joblib import Parallel, delayed

# -- Market entities classes:
from ..market.BuyerClass import BuyerClass
from ..market.SessionClass import SessionClass
from ..market.util.custom_exceptions import (
    NoMarketBuyersExceptions,
    NoMarketUsersExceptions
)

# -- Mock data imports:
# from src.market.helpers.model_helpers import create_forecast
# from src.market.helpers.model_helpers import create_forecast_mock as create_forecast

from ..market.helpers.source.ml_engine import create_ensemble_forecasts
from ..market.helpers.source.ensemble.stack_generalization.wind_ramp.detector import wind_ramp_detector
from ..market.helpers.source.assessment_contributions import compute_forecasters_contributions
from ..market.helpers.source.assessment_forecast_skill import compute_forecasters_skill_scores

class MarketClass:
    DEBUG = False
    FORECAST_HORIZON = settings.MARKET_FORECAST_HORIZON  # forecast horizon
    MARKET_TZ = "utc"

    def __init__(self, n_jobs=-1):
        self.buyers_resources = []
        self.sellers_resources = []
        self.buyers_data = {}
        self.mkt_sess = None
        self.launch_time = None
        self.buyer_outputs = []
        self.n_jobs = n_jobs

    def activate_debug_mode(self):
        self.DEBUG = True
        logger.remove()

    def init_session(self, session_data, launch_time):
        """
        Initialize market session.

        :param session_data: Dictionary with session data
        :param launch_time: Session launch time

        :return: self
        """
        self.launch_time = launch_time
        self.mkt_sess = SessionClass(
            launch_ts=launch_time,
            session_id=session_data["id"],
            status=session_data["status"],
        )
        self.mkt_sess.validate_attributes()
        self.mkt_sess.set_initial_conditions()
        return self

    def start_session(self, api_controller=None):
        """
        Start market session.

        :param api_controller: APIController instance

        :return: self
        """
        # todo: check api responses
        self.mkt_sess.start_session()
        if api_controller is not None:
            api_controller.update_market_session(
                session_id=self.mkt_sess.session_id,
                status=self.mkt_sess.status,
                launch_ts=self.mkt_sess.launch_ts
            )

    def end_session(self):
        """
        End market session.

        :return: self
        """
        self.mkt_sess.end_session()

    def show_session_details(self):
        """
        Display session details.

        :return: None
        """
        if self.mkt_sess is None:
            raise Exception("Error! Must init a session first!")
        logger.info("-" * 70)
        logger.info(">> Session details:")
        logger.info(f"Session ID: {self.mkt_sess.session_id}")
        logger.info(f"Session Launch Time: {self.mkt_sess.launch_ts}")

    def show_session_results(self):
        """
        Display session results.

        :return: None
        """
        # todo: add stats here
        logger.info("-" * 70)
        logger.info(f">> Session {self.mkt_sess.session_id} results:")
        logger.info("-" * 70)

    def load_challenges(self, challenges: list):
        """
        Init session market challenges.

        :param challenges: List of dictionaries with challenge data
        :return: self
        """
        if ((not isinstance(challenges, list)) or
                (not all([isinstance(x, dict) for x in challenges]))):
            raise TypeError("Error! challenges arg. must be a list of dicts")

        if len(challenges) == 0:
            raise NoMarketBuyersExceptions("Error! No challenges available "
                                           "in the market session.")

        # Discard challenges with "submission_list" empty and log discarded:
        challenges_ = []
        for x in challenges:
            if len(x["submission_list"]) == 0:
                logger.warning(f"Discarding challenge '{x['id']}' "
                               f"from session '{self.mkt_sess.session_id}' "
                               f"due to empty submission list.")
                continue
            else:
                challenges_.append(x)

        if len(challenges_) == 0:
            raise NoMarketBuyersExceptions("Error! No challenges available "
                                           "in the market session.")

        # Store session challenges:
        self.mkt_sess.set_session_challenges(challenges_)
        # Init buyer classes per challenge (each buyer class holds data for
        # an individual buyer resource)
        for challenge in challenges_:
            # Init Buyer class with each bid information:
            self.buyers_data[challenge["resource"]] = BuyerClass(
                user_id=challenge["user"],
                resource_id=challenge["resource"],
                challenge_id=challenge["id"],
                challenge_start_dt=challenge["start_datetime"],
                challenge_end_dt=challenge["end_datetime"],
                challenge_usecase=challenge["use_case"],
            ).set_forecast_range()  #.validate_attributes()

        return self

    def load_forecasters(self,
                         sellers_resources: list,
                         sellers_forecasts: dict):
        """
        Load sellers data into each agent class. Namely:
        - Sellers resources data (features)
        - Sellers forecasts data

        :param sellers_resources: List of dictionaries with sellers resources
        :param sellers_forecasts: Dictionary with sellers forecasts data

        :return: self
        """
        t0 = time()
        logger.info("Logging sellers data ...")
        if not isinstance(sellers_resources, list):
            raise TypeError("Error! a list of seller resources must be provided")

        if len(sellers_forecasts) == 0:
            raise NoMarketUsersExceptions("Error! No sellers forecasts "
                                          "available in the market session. "
                                          "Skipping ...")

        # Init Seller class with each seller identification:
        self.sellers_resources = sellers_resources
        logger.debug(f"\nUsers resources (to load):"
                     f"\nSellers: {self.sellers_resources}")
        # Load each user resource (measurements or features) data into
        # a sellers class:
        for resource_data in self.sellers_resources:
            user_id = resource_data["user"]
            variable_id = resource_data["variable"]
            target_resource = resource_data["market_session_challenge_resource_id"]
            # Get forecast created by 'user_id' to 'target_resource'
            forecasts = sellers_forecasts[user_id][target_resource][variable_id]
            # Rename "value" column to avoid JOIN problems:
            forecast_variable = f"{user_id}_{variable_id}"
            forecasts.rename(columns={"value": forecast_variable},
                             inplace=True)
            # Add forecasts info to buyer class
            self.buyers_data[target_resource].add_seller(
                user_id=user_id,
                forecast_variable=forecast_variable,
                forecasts=forecasts
            )
        logger.success(f"Logging sellers data ... Ok! {t0 - time()}")
        return self

    def load_buyer_measurements(self, measurements: dict):
        """
        Load measurements data into each agent class. Namely:
        - Buying agents resource measurements (forecast target datasets)
        - Selling agents resource measurements (to be used as forecast lags)

        :param measurements: Dictionary with measurements data for each
        agent resource identifier

        :return:
        """
        if not isinstance(measurements, dict):
            raise TypeError("Error! measurements arg. must be a dict")
        # Intersection - agents that are sellers & buyers
        buyers_resources_ = list(self.buyers_data.keys())
        # Assign measurements data to each agent class:
        default_df = pd.DataFrame(columns=["datetime", "value"])
        for resource_id in sorted(buyers_resources_):
            # Fetch agent data (empty dataset if key not found)
            _df = measurements.get(resource_id, default_df)
            self.buyers_data[resource_id].set_measurements(_df)
        return self

    @staticmethod
    def __preprocess_buyer_data(data, expected_dates):
        """
        Resample & Reindex data to expected time resolution.
        Missing dates are market as NA

        :param data:
        :param expected_dates:

        :return: pd.DataFrame
        """
        freq = settings.MARKET_DATA_TIME_RESOLUTION
        data = data.resample(freq).mean()
        data = data.reindex(expected_dates)
        return data

    def __process_features(self, market_x, buyer_y,
                           forecast_range,
                           imputation_strategy="drop"):
        """
        Prepare train & test datasets for forecast

        :param market_x: Market features data
        :param buyer_y: Buyer target data
        :param forecast_range: Forecast range
        :param imputation_strategy: Imputation strategy

        :return: train_features, train_targets, test_features
        """
        launch_time_ = self.launch_time.strftime("%Y-%m-%d %H:%M:%S.%f")
        # Prepare train dataset:
        train_features = market_x[:launch_time_].join(buyer_y).dropna(subset=["target"])  # noqa
        if imputation_strategy == "drop":
            train_features.dropna(inplace=True)
        elif imputation_strategy == "fill_mean":
            train_features.fillna(train_features.mean(), inplace=True)
        else:
            raise ValueError("Error! Invalid imputation strategy.")
        # Remove "target" variable from train dataset:
        train_targets = train_features.pop("target").to_frame()
        # Test features (variables available for all dates since launch time)
        test_features = market_x.loc[forecast_range]
        return train_features, train_targets, test_features

    def forecast(self, buyer_cls):
        """
        Create forecast for buyer agent resource.

        :param buyer_cls: BuyerClass instance

        :return: dict
        """
        # -- Load Buyer data
        logger.info(f"Forecasting buyer resource '{buyer_cls.resource_id}' ...")
        resource_id = buyer_cls.resource_id
        challenge_id = buyer_cls.challenge_id
        challenge_usecase = buyer_cls.challenge_usecase
        user_id = buyer_cls.user_id
        buyer_y = buyer_cls.y[["value"]].copy()
        buyer_resource_name = buyer_cls.resource_id
        buyer_y.rename(columns={"value": "target"}, inplace=True)
        market_x = buyer_cls.sellers_forecasts.copy()
        forecast_range = buyer_cls.forecast_range
        logger.info(f"Executing forecast for challenge '{challenge_id}' ... ")
        logger.debug(f"\nResource ID: {resource_id}"
                     f"\nUser ID:{user_id}"
                     f"\nlen(y):{len(buyer_y)}"
                     f"\nshape(market_x):{market_x.shape}"
                     )
        # -- Failure scenario return:
        fail_return = {"user_id": user_id,
                       "resource_id": resource_id,
                       "forecasts": None,
                       "df_ramp_clusters": None,
                       "error": True}
        # -- Check if buyer dataset (measurements) is empty:
        if buyer_y.empty:
            logger.warning(f"Buyer {user_id} resource {resource_id} "
                           f"forecast target dataset is empty "
                           f"(for the available market dataset dates). "
                           f"Aborting forecast.")
            return fail_return
        # Pre-process buyer data
        try:
            buyer_y = self.__preprocess_buyer_data(
                data=buyer_y,
                expected_dates=market_x.index
            )
        except Exception as e:
            logger.exception(f"Error! Buyer {user_id} resource {resource_id} "
                             f"preprocessing failed. Aborting forecast. "
                             f"Details: {e}")
            return fail_return

        # Check if there are sufficient number of samples in train dataset
        # to train the ML models (minimum of 30 days of samples):
        # todo: reactivate this check
        # if train_features.shape[0] < 4 * 24 * 30:
        #     logger.warning(f"Error! Challenge '{challenge_id}' "
        #                    f"User '{user_id}' resource '{resource_id}' "
        #                    f"an empty train dataset. Aborting forecast.")
        #     return fail_return

        # Get features names and indexes
        sellers_features_name = list(market_x.columns)

        # -- Create Forecasts
        logger.debug("Creating forecasts ...")
        forecast_model = settings.Stack.params["model_type"]
        # forecast_var_model = Stack.params["var_model_type"]
        df_buyer = buyer_y.copy()
        df_market = market_x.copy()

        # -- Forecasting:
        df_buyer.columns = [buyer_resource_name]
        forecasts, results_challenge_dict = create_ensemble_forecasts(
            ens_params=settings.Stack.params,
            launch_time=self.launch_time,
            forecast_range=forecast_range,
            df_buyer=df_buyer,
            df_market=df_market,
            challenge_usecase=challenge_usecase,
            challenge_id=challenge_id,
        )

        # -- Wind Ramp Detection
        logger.debug("Wind ramp detection ...")
        pred_variability_insample = results_challenge_dict['wind_power_ramp']['predictions_insample']
        pred_variability_outsample = results_challenge_dict['wind_power_ramp']['predictions_outsample']
        alarm_status, df_ramp_clusters = wind_ramp_detector(ens_params=settings.Stack.params,
                            df_pred_variability_insample=pred_variability_insample,
                            df_pred_variability_outsample=pred_variability_outsample)

        logger.info(f"Alarm status: {alarm_status}")
        if df_ramp_clusters is not None:
            logger.info(f"Ramp clusters: {df_ramp_clusters.cluster_id.unique()}")
            # log datetime of ramp clusters
            logger.info(f"Ramp clusters datetime: {df_ramp_clusters.index}")

        # round forecasts value:
        forecasts["value"] = forecasts["value"].round(6)

        logger.info(f"Processing buyer {buyer_cls.resource_id} bid ... Ok!")
        return {
            "challenge_id": challenge_id,
            "resource_id": resource_id,
            "user_id": user_id,
            "sellers_features_name": sellers_features_name,
            "forecasts": forecasts,
            "forecast_model": forecast_model,
            "df_ramp_clusters": df_ramp_clusters,
            "error": False
        }

    @staticmethod
    def __upload_forecasts(api_controller, buyer_output):
        """
        Upload forecasts and weights to the API

        :param api_controller: APIController instance
        :param buyer_output: Buyer output dictionary

        :return: None
        """
        for variable in buyer_output["forecasts"]["variable"].unique():
            forecasts_ = buyer_output["forecasts"][buyer_output["forecasts"]["variable"] == variable].copy()
            forecasts_["datetime"] = forecasts_["datetime"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            forecasts_ = forecasts_[["datetime", "value"]].to_dict(orient="records")
            # todo: check api responses
            api_controller.post_market_forecasts(
                challenge_id=buyer_output["challenge_id"],
                model_id=buyer_output["forecast_model"],
                variable_id=variable,
                forecasts=forecasts_,
            )

        # Upload ramp alerts + variability forecasts:
        ramps_ = buyer_output["df_ramp_clusters"]
        if ramps_ is not None:
            ramps_ = ramps_.copy()
            # Force column names to lower case:
            ramps_.columns = [col.lower() for col in ramps_.columns]
            # Identify quantile columns dynamically
            quantiles_ = [col for col in ramps_.columns if col.startswith("q")]
            # Create the 'variability_quantiles' column with dynamic quantile dictionary
            ramps_['variability_quantiles'] = ramps_.apply(
                lambda row: {q: round(row[q], 3) for q in quantiles_},
                axis=1)
            # Drop the original quantile columns if they’re no longer needed
            ramps_ = ramps_.drop(columns=quantiles_)
            ramps_["datetime"] = ramps_.index.strftime("%Y-%m-%dT%H:%M:%SZ")
            ramps_ = ramps_.to_dict(orient="records")
            # todo: check api responses
            api_controller.post_market_ramp_alerts(
                challenge_id=buyer_output["challenge_id"],
                model_id="idw_based",
                ramp_alerts=ramps_
            )


    @staticmethod
    def __upload_weights(api_controller,
                         challenge_id,
                         weights,
                         pending_ensemble_data):
        """
        Upload forecasts and weights to the API

        :param api_controller: APIController instance

        :return: None
        """
        for ensemble in pending_ensemble_data:
            for user_id, weight in weights[ensemble["variable"]].items():
                payload = {
                    "ensemble": ensemble["ensemble_id"],
                    "user": user_id,
                    "value": round(weight, 6)
                }
                api_controller.post_market_weights(
                    challenge_id=challenge_id,
                    weights=payload,
                )

    @staticmethod
    def __upload_scores(api_controller,
                        challenge_id,
                        scores):
        """
        Upload submission scores to the API:
        """
        for submission_score in scores:
            try:
                api_controller.post_submission_scores(
                    challenge_id=challenge_id,
                    scores=submission_score
                )
            except Exception as ex:
                print()

    def ensemble_forecast(self, api_controller=None):
        """
        Run current market session

        Steps:
            1. Process forecasts for each buyer agent. For each buyer:
                1.1. Load Buyer data
                1.2. Create Ensemble Forecasts
            2. Save session results
        """
        logger.info("-" * 70)
        logger.info(f"Running session {self.mkt_sess.session_id} ({self.launch_time})...")  # noqa
        # -- Create forecasts for each buyer resource
        self.buyer_outputs = Parallel(n_jobs=self.n_jobs)(
            delayed(self.forecast)(buyer_cls)
            for buyer_cls in self.buyers_data.values()
        )

        # -- Store results in each buyer cls:
        for out in self.buyer_outputs:
            # if api controller is available, try to post forecasts:
            if api_controller is not None:
                self.__upload_forecasts(
                    api_controller=api_controller,
                    buyer_output=out
                )
            # Store forecasts in buyer class for future call:
            self.buyers_data[out["resource_id"]].set_ensemble_forecasts(
                model=out["forecast_model"],
                forecasts=out["forecasts"]
            )

    def ensemble_weights(self, challenge_data, buyer_measurements,
                         api_controller=None):
        # --------------------------------
        # For simulator only (variable renaming):
        if "challenge" not in challenge_data:
            challenge_data["challenge"] = challenge_data["id"]
        # --------------------------------
        logger.info("-" * 70)
        logger.info(f"Calculating weights ...")
        logger.debug(f"Challenge data:\n{challenge_data}")
        # Calculate forecast range:
        challenge_forecast_range = pd.date_range(
            start=challenge_data["start_datetime"],
            end=challenge_data["end_datetime"],
            freq=settings.MARKET_DATA_TIME_RESOLUTION
        )
        # Set up y_test:
        y_test_previous_day = buyer_measurements.copy()
        # Calculate Forecasters Contributions
        results_contributions = compute_forecasters_contributions(
            buyer_resource_name=challenge_data["resource"],
            ens_params=settings.Stack.params,
            df_y_test=y_test_previous_day,
            previous_day_forecast_range=challenge_forecast_range,
            use_case=challenge_data["use_case"],
            challenge_id=challenge_data["challenge"]
        )
        # Post weights for challenge:
        logger.info("Calculating weights ... Ok!")
        if challenge_data["resource"] in self.buyers_data:
            # on operational, self.buyers_data is not initialized before
            # this method. This is only used for reporting.
            self.buyers_data[challenge_data["resource"]].set_ensemble_weights(
                weights=results_contributions,
            )
        # if api controller is available, try to post weights:
        if api_controller is not None:
            self.__upload_weights(
                api_controller=api_controller,
                challenge_id=challenge_data["challenge"],
                weights=results_contributions,
                pending_ensemble_data=challenge_data["ensemble_data"]
            )

        return results_contributions

    def forecaster_scores(self, challenge_data,
                          buyer_measurements,
                          sellers_forecasts,
                          api_controller=None):
        # --------------------------------
        # For simulator only (variable renaming):
        if "challenge" not in challenge_data:
            challenge_data["challenge"] = challenge_data["id"]
        # --------------------------------
        logger.info("-" * 70)
        logger.info(f"Calculating forecasting skill scores ...")
        # Set up y_test:
        y_test_previous_day = buyer_measurements.copy()
        # Calculate Forecaster Scores
        scores = compute_forecasters_skill_scores(
            df_y_test=y_test_previous_day,
            sellers_forecasts=sellers_forecasts
        )
        # Post weights for challenge:
        logger.info("Calculating forecasting skill scores ... Ok!")
        if challenge_data["resource"] in self.buyers_data:
            # on operational, self.buyers_data is not initialized before
            # this method. This is only used for reporting.
            self.buyers_data[challenge_data["resource"]].set_forecasters_skill_scores(
                scores=scores,
            )
        # if api controller is available, try to post scores:
        if api_controller is not None:
            self.__upload_scores(
                api_controller=api_controller,
                challenge_id=challenge_data["challenge"],
                scores=scores,
            )
        return scores

    def save_session_results(self, save_forecasts=False, free_memory=True):
        """
        Update buyer's & seller's Classes w/ session results

        :param save_forecasts: Save forecasts to API
        :param free_memory: Free memory after saving session results

        :return: None
        """
        logger.info("Saving session results ...")
        for cls in self.buyers_data.values():
            self.mkt_sess.set_buyer_result(cls)
            if save_forecasts:
                self.mkt_sess.set_buyer_forecasts(cls)
                self.mkt_sess.set_buyer_weights(cls)
        logger.info("Saving session results ... Ok!")

        if free_memory:
            del self.buyer_outputs
            del self.buyers_data
            gc.collect()

    @staticmethod
    def open_next_session(api_controller=None):
        """
        Open next market session

        :param api_controller: APIController instance

        :return: None
        """

        if api_controller is None:
            raise AttributeError("Error! Must provide an api controller "
                                 "to open new session.")
        # todo: check api responses
        api_controller.create_market_session()
