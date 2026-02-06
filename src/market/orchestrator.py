import gc

import pandas as pd

from loguru import logger
from joblib import Parallel, delayed

# -- Configs:
try:
    from conf import settings
except ImportError:
    # this is needed for testing purposes
    from ...conf import settings

# -- Market entities classes:
from .entities.session import SessionClass
from .data_loader import DataLoader
from ..assessment.report import validate_forecasters
from ..market.engine import ForecastEngine
from ..core.config import ForecastConfig
from ..assessment.skills import compute_forecasters_skill_scores


class MarketClass:
    DEBUG = False
    FORECAST_HORIZON = settings.MARKET_FORECAST_HORIZON  # forecast horizon
    MARKET_TZ = "utc"

    def __init__(
        self,
        n_jobs=-1,
        run_benchmarks=False,
        strategies=None,
        config=None,
        export_data=False,
        export_path=None,
        export_only=False,
    ):
        """
        Initialize MarketClass.

        :param n_jobs: Number of parallel jobs for forecasting
        :param run_benchmarks: Whether to run benchmark ensembles
        :param strategies: List of strategy names to run. If None, uses
            default (weighted_avg). Benchmarks are added if run_benchmarks=True.
        :param config: ForecastConfig instance. If None, uses default config.
        :param export_data: Whether to export training data to CSV
        :param export_path: Base path for data exports (e.g., "csv_data_20251229")
        :param export_only: If True, stop after export without running forecast
        """
        self.buyers_resources = []
        self.mkt_sess = None
        self.launch_time = None
        self.buyer_outputs = []
        self.n_jobs = n_jobs
        self.nr_sellers = 0
        self.run_benchmarks = run_benchmarks
        self._strategies = strategies
        self.export_data = export_data
        self.export_path = export_path
        self.export_only = export_only
        self._config = config or ForecastConfig.from_settings()
        self._engine = ForecastEngine(self._config)
        self._data_loader = DataLoader()

    @property
    def buyers_data(self) -> dict:
        """Access buyers_data from DataLoader (backward compatibility)."""
        return self._data_loader.buyers_data

    @buyers_data.deleter
    def buyers_data(self) -> None:
        """Clear buyers_data in DataLoader (for memory cleanup)."""
        self._data_loader.buyers_data = {}

    @property
    def sellers_resources(self) -> list:
        """Access sellers_resources from DataLoader (backward compatibility)."""
        return self._data_loader.sellers_resources

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
                launch_ts=self.mkt_sess.launch_ts,
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
        logger.info("-" * 70)

    def load_challenges(self, challenges: list):
        """
        Init session market challenges.

        :param challenges: List of dictionaries with challenge data
        :return: self
        """
        # Set session ID for logging context
        session_id = self.mkt_sess.session_id if self.mkt_sess else None
        self._data_loader._session_id = session_id

        # Delegate to DataLoader
        self._data_loader.load_challenges(challenges)

        # Filter valid challenges for session storage
        valid_challenges = [
            c for c in challenges if c["resource"] in self._data_loader.buyers_data
        ]
        self.mkt_sess.set_session_challenges(valid_challenges)

        return self

    def load_forecasters(
        self,
        sellers_resources: list,
        sellers_forecasts: dict,
    ):
        """
        Load sellers data into each agent class.

        :param sellers_resources: List of dictionaries with sellers resources
        :param sellers_forecasts: Dictionary with sellers forecasts data

        :return: self
        """
        self._data_loader.load_forecasters(sellers_resources, sellers_forecasts)
        return self

    def load_buyer_measurements(self, measurements: dict):
        """
        Load measurements data into each agent class.

        :param measurements: Dictionary with measurements data for each
            agent resource identifier

        :return: self
        """
        self._data_loader.load_buyer_measurements(measurements)
        return self

    def _determine_strategies(self) -> list[str]:
        """
        Determine which strategies to run for forecasting.

        :return: List of strategy names to execute
        """
        if self._strategies:
            strategies = list(self._strategies)
        else:
            strategies = ["weighted_avg"]

        # Add benchmark strategies if requested
        if self.run_benchmarks:
            for benchmark in ["arithmetic_mean", "best_forecaster"]:
                if benchmark not in strategies:
                    strategies.append(benchmark)

        return strategies

    def _export_training_data(
        self,
        df_market: pd.DataFrame,
        df_buyer: pd.DataFrame,
        buyer_cls,
    ) -> None:
        """
        Export training data to CSV if export is enabled.

        :param df_market: Market features DataFrame
        :param df_buyer: Buyer target DataFrame
        :param buyer_cls: BuyerClass instance for metadata
        """
        import os

        dataset = df_market.join(df_buyer)
        dataset.index.name = "datetime"

        use_case = buyer_cls.challenge_usecase
        # Use middle of forecast range for date (avoids edge cases)
        mid_idx = len(buyer_cls.forecast_range) // 2
        date_str = buyer_cls.forecast_range[mid_idx].strftime("%Y-%m-%d")

        export_dir = f"{self.export_path}/{use_case}"
        os.makedirs(export_dir, exist_ok=True)

        export_file = f"{export_dir}/{date_str}_{use_case}.csv"
        dataset.to_csv(export_file)
        logger.info(f"Exported training data to {export_file}")

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
        user_id = buyer_cls.user_id
        buyer_y = buyer_cls.y[["value"]].copy()
        buyer_y.rename(columns={"value": "target"}, inplace=True)
        market_x = buyer_cls.sellers_forecasts.copy()
        forecast_range = buyer_cls.forecast_range
        logger.info(f"Executing forecast for challenge '{challenge_id}' ... ")
        logger.debug(
            f"\nResource ID: {resource_id}"
            f"\nUser ID:{user_id}"
            f"\nlen(y):{len(buyer_y)}"
            f"\nshape(market_x):{market_x.shape}"
        )

        # -- Failure scenario return:
        fail_return = {
            "challenge_id": challenge_id,
            "resource_id": resource_id,
            "user_id": user_id,
            "sellers_features_name": [],
            "sellers_features_used": [],
            "engine_results": {},
            "ensemble_weights": {},
            "error": True,
        }
        # -- Check if buyer dataset (measurements) is empty:
        if buyer_y.empty:
            logger.warning(
                f"Buyer {user_id} resource {resource_id} "
                f"forecast target dataset is empty "
                f"(for the available market dataset dates). "
                f"Aborting forecast."
            )
            return fail_return

        if market_x.empty:
            # It might happen that the market dataset is empty
            # due to the fact that sellers do not have sufficient
            # submissions for the days prior to the forecast target day
            logger.warning(
                f"Buyer {user_id} resource {resource_id} "
                f"market features dataset is empty. "
                f"Aborting forecast."
            )
            return fail_return

        # Pre-process buyer data
        try:
            buyer_y = DataLoader.preprocess_buyer_data(
                data=buyer_y,
                expected_dates=market_x.index,
            )
        except Exception as e:
            logger.exception(
                f"Error! Buyer {user_id} resource {resource_id} "
                f"preprocessing failed. Aborting forecast. "
                f"Details: {e}"
            )
            return fail_return

        # Get features names and indexes
        sellers_features_name = list(market_x.columns)

        # -- Create Forecasts
        logger.debug("Creating forecasts ...")
        df_buyer = buyer_y.copy()
        df_market = market_x.copy()

        # -- Forecasting:
        # Validate which forecasters should be considered (submitted all quantiles)
        valid_forecasters_list, forecasters_w_history = validate_forecasters(
            forecast_range=forecast_range,
            df_market=df_market,
        )

        if len(valid_forecasters_list) == 0:
            logger.warning(
                f"Buyer {user_id} resource {resource_id} "
                f"has no valid forecasters with submissions "
                f"for all required quantiles (Q10, Q50, Q90). "
                f"Aborting forecast."
            )
            return fail_return

        # Ensure we are only used forecasters that submitted Q10, Q50, Q90
        df_market = df_market[
            [
                x
                for x in df_market.columns
                if x.startswith(tuple(valid_forecasters_list))
            ]
        ]

        # -- Data export (optional) --
        if self.export_data and self.export_path:
            self._export_training_data(df_market, df_buyer, buyer_cls)
            if self.export_only:
                return fail_return

        # -- Run forecast engine --
        # Train data (up to forecast start date)
        X_train = df_market.loc[: forecast_range[0]].copy()
        y_train = df_buyer.loc[: forecast_range[0]].copy()
        # Test data (forecast range)
        X_test = df_market.loc[forecast_range].copy()
        # Get forecast strategies to run
        forecast_strategies = self._determine_strategies()
        # Note: strategies compute their own scores from X_train/y_train
        engine_results = self._engine.forecast(
            resource_id=resource_id,
            X_train=X_train,
            y_train=y_train,
            X_test=X_test,
            forecast_range=forecast_range,
            strategies=forecast_strategies,
            quantiles=list(self._config.quantiles),
        )

        logger.success(f"Forecasting buyer resource '{buyer_cls.resource_id}' ... Ok!")

        return {
            "challenge_id": challenge_id,
            "resource_id": resource_id,
            "user_id": user_id,
            "sellers_features_name": sellers_features_name,
            "sellers_features_used": valid_forecasters_list,
            "engine_results": engine_results,
            "error": False,
        }

    @staticmethod
    def __upload_forecasts(api_controller, buyer_output):
        """
        Upload all forecast results to the API.

        :param api_controller: APIController instance
        :param buyer_output: Buyer output dictionary containing engine_results

        :return: None
        """
        engine_results = buyer_output.get("engine_results", {})
        challenge_id = buyer_output["challenge_id"]
        user_id = buyer_output["user_id"]

        for strategy_name, result in engine_results.items():
            predictions = result.predictions
            if predictions is None or predictions.empty:
                continue

            for variable in predictions["variable"].unique():
                forecast_slice = predictions[predictions["variable"] == variable].copy()
                forecast_slice["datetime"] = forecast_slice["datetime"].dt.strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
                records = forecast_slice[["datetime", "value"]].to_dict(
                    orient="records"
                )
                try:
                    response = api_controller.post_market_forecasts(
                        challenge_id=challenge_id,
                        model_id=strategy_name,
                        variable_id=variable,
                        forecasts=records,
                    )
                    if response.get("code") != 201:
                        logger.error(
                            f"Failed to upload {strategy_name} forecasts for "
                            f"buyer {user_id}: {response}"
                        )
                except Exception as e:
                    logger.error(
                        f"Failed to upload {strategy_name} forecasts for "
                        f"buyer {user_id}: {e}"
                    )

    def ensemble_forecast(self, api_controller=None):
        """
        Run current market session

        Steps:
            1. Process forecasts for each buyer agent. For each buyer:
                1.1. Load Buyer data
                1.2. Create Ensemble Forecasts
            2. Save session results
        """
        logger.debug("-" * 70)
        logger.debug(
            f"Running session {self.mkt_sess.session_id} ({self.launch_time})..."
        )  # noqa
        # -- Create forecasts for each buyer resource
        self.buyer_outputs = Parallel(n_jobs=self.n_jobs)(
            delayed(self.forecast)(buyer_cls) for buyer_cls in self.buyers_data.values()
        )

        # -- Store results in each buyer cls:
        for out in self.buyer_outputs:
            # if api controller is available, try to post forecasts:
            if api_controller is not None:
                self.__upload_forecasts(
                    api_controller=api_controller,
                    buyer_output=out,
                )
            # Store sellers info used:
            self.buyers_data[out["resource_id"]].set_sellers_features_used(
                sellers_features=out["sellers_features_name"],
                sellers_features_used=out["sellers_features_used"],
            )
            # Store ensemble forecasts for future reuse (reporting):
            engine_results = out.get("engine_results", {})
            if engine_results:
                self.buyers_data[out["resource_id"]].set_strategy_forecasts(
                    engine_results
                )

    @staticmethod
    def forecaster_scores(challenge_data, buyer_measurements, sellers_forecasts):
        # --------------------------------
        # For simulator only (variable renaming):
        if "challenge" not in challenge_data:
            challenge_data["challenge"] = challenge_data["id"]
        # --------------------------------
        logger.info("-" * 70)
        logger.info("Calculating forecasting skill scores ...")
        # Set up y_test:
        y_test_previous_day = buyer_measurements.copy()
        # Calculate Forecaster Scores
        scores = compute_forecasters_skill_scores(
            df_y_test=y_test_previous_day,
            forecasts=sellers_forecasts,
            forecast_id_col="submission",
        )
        return scores

    @staticmethod
    def ensemble_scores(challenge_data, buyer_measurements, ensemble_forecasts):
        # --------------------------------
        # For simulator only (variable renaming):
        if "challenge" not in challenge_data:
            challenge_data["challenge"] = challenge_data["id"]
        # --------------------------------
        logger.info("-" * 70)
        logger.info("Calculating forecasting skill scores ...")
        # Set up y_test:
        y_test_previous_day = buyer_measurements.copy()
        # Calculate Forecaster Scores
        scores = compute_forecasters_skill_scores(
            df_y_test=y_test_previous_day,
            forecasts=ensemble_forecasts,
            forecast_id_col="ensemble",
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
            raise AttributeError(
                "Error! Must provide an api controller to open new session."
            )
        # todo: check api responses
        api_controller.create_market_session()
