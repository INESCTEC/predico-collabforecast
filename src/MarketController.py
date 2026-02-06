import json
import pytz
import pandas as pd
import datetime as dt

from loguru import logger
from collections import defaultdict

from conf import settings

from .io.database.postgres import PostgresDB
from .io.api import Controller
from .market import MarketClass, KpiClass
from .io.api.helpers import get_session_data
from .io.database.query import (
    get_measurements_data,
    get_sellers_data,
    get_sellers_submissions,
    get_ensemble_forecasts,
    get_submissions_by_resource,
    get_challenges_for_scoring,
    delete_current_month_scores_and_weights,
    get_continuous_forecasts,
    get_scores_per_resource,
    get_sellers_forecasts_by_resource,
    get_measurements_data_by_resource,
    get_resource_participation_type,
)
from .io.backup.helpers import store_session_datasets
from .market.helpers.stats_helpers import log_session_stats
from .market.helpers.report_helpers import aggregated_metrics_json


class MarketController:
    def __init__(self):
        # Market API Controller:
        self.api = Controller()
        self.api.login(email=settings.MARKET_EMAIL, password=settings.MARKET_PASSWORD)

        # Attempt to establish DB connection (if it fails, we need to stop
        # the code here to avoid interaction problems later)
        db = PostgresDB.get_db_instance(config_name="default")
        # try to connect:
        if not db.test_connection():
            raise Exception(f"Failed to connect to project database {db.engine}.")  # noqa

    def open_market_session(self, force_new=False, gate_closure_hour: int = 10):
        """
        If there are no market sessions, creates 1st session w/ default params
        Else, searches for last 'staged' session and opens it

        :param force_new: bool, whether to force a new session (closes current)
        :param gate_closure_hour: int (0-23), hour in CET for gate closure.
            The next occurrence of this hour will be used.
            Default is 10 (10:00 CET).
        :return:
        """
        if force_new:
            logger.warning("Forcing a new market session ...")
            # List last market 'open' sessions:
            current_session = self.api.list_last_session()
            logger.debug("Current session:")
            if current_session:
                logger.debug(current_session)
                logger.debug("Finishing current session ...")
                self.api.update_market_session(
                    session_id=current_session["id"],
                    status="finished",
                    finish_ts=dt.datetime.utcnow(),
                )

        # Define session gate closure time
        # Work with CET timezone for gate closure hour definition
        # to properly handle DST transitions
        # todo: review this part -- should be flexible for other tz
        now_utc = dt.datetime.utcnow().replace(tzinfo=pytz.utc)
        cet_tz = pytz.timezone("CET")
        now_cet = now_utc.astimezone(cet_tz)

        # Build naive datetime for gate closure, then localize it properly
        # to handle DST transitions correctly
        gate_closure_naive = dt.datetime(
            now_cet.year, now_cet.month, now_cet.day, gate_closure_hour, 0, 0
        )

        # Gate closure should always be in the future, so if the specified
        # hour has already passed today, schedule for tomorrow:
        now_cet_naive = now_cet.replace(tzinfo=None)
        if gate_closure_naive <= now_cet_naive:
            gate_closure_naive += dt.timedelta(days=1)

        # Localize the naive datetime to get correct DST offset for that date
        gate_closure_cet = cet_tz.localize(gate_closure_naive)
        gate_closure_utc = gate_closure_cet.astimezone(pytz.utc).replace(tzinfo=None)  # noqa

        # Get create new market session:
        session = self.api.create_market_session(gate_closure=gate_closure_utc)
        logger.debug(session)

    def finish_market_session(self, is_running=False):
        """
        Finish last open market session.
        """
        if is_running:
            # List last market 'running' session:
            current_session = self.api.list_last_session(status="running")
        else:
            # List last market session:
            # Useful in case there are sessions stuck in 'open' or 'closed' status
            current_session = self.api.list_last_session()

        logger.debug("Current session:")
        if current_session:
            logger.debug(current_session)
            logger.debug("Finishing current session ...")
            self.api.update_market_session(
                session_id=current_session["id"],
                status="finished",
                finish_ts=dt.datetime.utcnow(),
            )

    def list_last_session(self):
        """
        Request buyers bids for last 'open' session

        :return:
        """
        # Check open session:
        session = self.api.list_last_session()
        logger.info("Last session available:")
        logger.info(json.dumps(session, indent=2))
        logger.info("")
        return session

    def set_session_status(self, session_id, new_status):
        """
        Request buyers bids for last 'open' session

        :return:
        """
        status = self.api.update_market_session(
            session_id=session_id, status=new_status
        )
        logger.info(json.dumps(status, indent=2))
        logger.info("")

    def close_market_session(self):
        """
        Close current 'OPEN' market session

        :return:
        """
        # List last market 'open' sessions:
        open_session = self.api.list_last_session(status="open")
        logger.info("Current 'OPEN' session:")
        logger.info(open_session)
        logger.info("")

        # Change market session status from 'OPEN' to 'CLOSED':
        self.api.update_market_session(
            session_id=open_session["id"],
            status="closed",
            close_ts=dt.datetime.utcnow(),
        )

    def prepare_continuous_submissions(self):
        # ################################
        # Fetch session info
        # ################################
        # Fetch session info:
        session_info = get_session_data(self.api)
        challenges_data = session_info["challenges_data"]

        # ##################################################
        # Query data and prepare submissions per challenge
        # ##################################################
        for challenge in challenges_data:
            logger.info("-" * 79)
            logger.info("-" * 79)
            logger.info(f"Working on challenge:\n{challenge}")
            resource_id = challenge["resource"]
            start_dt = challenge["start_datetime"]
            end_dt = challenge["end_datetime"]
            challenge_id = challenge["id"]

            # Calculate expected number of lead times for the challenge:
            expected_leadtimes = len(
                pd.date_range(
                    start=start_dt,
                    end=end_dt,
                    freq=settings.MARKET_DATA_TIME_RESOLUTION,
                )
            )

            # Get list of users that have continuous forecasts for this
            # challenge period:
            continuous_users_list = self.api.list_user_continuous_forecasts(
                resource_id=resource_id, start_date=start_dt, end_date=end_dt
            )

            # Get list of 'normal' submissions (i.e., older endpoint)
            # These have priority over "continuous" submissions.
            # 1. Get list of quantiles per user submitted via 'normal' endpoint
            users_qt_submissions = defaultdict(list)
            for submission in challenge["submission_list"]:
                if submission["submission_type"] == "normal":
                    users_qt_submissions[submission["user"]].append(
                        submission["variable"]
                    )
                else:
                    # Ignore 'continuous' submissions (there should be none)
                    # but just to be safe on debug scenarios.
                    continue
            # 2. List users that have submitted all quantiles:
            existing_users = [
                k
                for k, v in users_qt_submissions.items()
                if sorted(v) == sorted(settings.QUANTILES)
            ]

            # Remove users that have already submitted for all quantiles:
            users_list = [x for x in continuous_users_list if x not in existing_users]  # noqa

            # For each forecaster, check if he has continuous forecasts for
            # the challenge range:
            for user_id in users_list:
                # Check if user has continuous forecasts for the challenge range:
                data = get_continuous_forecasts(
                    user_id=user_id,
                    resource_id=resource_id,
                    start_dt=start_dt,
                    end_dt=end_dt,
                )
                # If there are continuous forecasts:
                if not data.empty:
                    # Ensure that the user has the correct number of leadtimes
                    # for all the quantiles before submitting on his behalf:
                    counter = data.groupby(["variable"]).count()["value"]
                    if not sorted(counter.index.to_list()) == sorted(
                        settings.QUANTILES
                    ):
                        logger.error(
                            f"User '{user_id}' has "
                            f"continuous forecasts for resource "
                            f"'{resource_id}' but not for all "
                            f"quantiles for this challenge."
                        )
                        continue

                    elif counter.min() != expected_leadtimes:
                        logger.error(
                            f"User '{user_id}' has "
                            f"continuous forecasts for resource "
                            f"'{resource_id}' but not for all "
                            f"lead times for this challenge."
                        )
                    else:
                        for quantile in settings.QUANTILES:
                            # Get forecast for the quantile:
                            forecasts = data.loc[
                                data["variable"] == quantile, ["datetime", "value"]
                            ]
                            forecasts["datetime"] = forecasts["datetime"].dt.strftime(
                                "%Y-%m-%dT%H:%M:%SZ"
                            )
                            # Convert to dict:
                            forecasts = forecasts.to_dict(orient="records")  # noqa
                            try:
                                # Submit on behalf of the user:
                                rsp = self.api.post_user_continuous_forecast(
                                    user_id=user_id,
                                    variable_id=quantile,
                                    forecasts=forecasts,
                                    challenge_id=challenge_id,
                                )
                                logger.success(
                                    f"Submitted continuous "
                                    f"forecasts for user '{user_id}' "
                                    f"for challenge '{resource_id}' "
                                    f"and quantile '{quantile}'. "
                                    f"Submission ID: {rsp['submission_id']}"
                                )
                            except Exception:
                                logger.exception(
                                    f"Failed to submit "
                                    f"continuous forecasts for user "
                                    f"'{user_id}' for challenge "
                                    f"'{resource_id}' and quantile "
                                    f"'{quantile}'."
                                )

    def run_market_session(self, backup_session_inputs=False):
        """
        Run last 'closed' market session. Session state is updated to
        'running' during execution and to 'finished' once it is complete.

        :return:
        """
        # ################################
        # Fetch session info
        # ################################
        # Fetch session info:
        session_info = get_session_data(self.api)
        session_data = session_info["session_data"]
        challenges_data = session_info["challenges_data"]
        buyers_resources = session_info["buyers_resources"]
        sellers_resources = session_info["sellers_resources"]

        # Operational Launch time:
        launch_time = dt.datetime.utcnow()
        # -- USE THIS FOR DEBUGGING! -----------------------------------
        # Dynamic launch time -> according to market session opening
        # launch_time = pd.to_datetime(session_data["open_ts"], format="%Y-%m-%dT%H:%M:%S.%fZ", utc=True)
        # launch_time = launch_time.to_pydatetime()
        # --------------------------------------------------------------

        # ###########################################################
        # Check if there are sufficient challenges with submissions
        # ###########################################################
        if len(challenges_data) == 0:
            logger.error(
                "There are no open challenges for this session."
                "Session will be closed without running the market."
            )
            return False
        else:
            # Get challenge end date (forecasts query limiter):
            forec_end_dt = max(
                [
                    dt.datetime.strptime(x["end_datetime"], "%Y-%m-%dT%H:%M:%SZ")
                    for x in challenges_data
                ]
            )  # noqa

        try:
            log_session_stats(session_info)
        except Exception:
            logger.exception("Failed to log session stats.")

        try:
            # ################################
            # Query agents measurements:
            # ################################
            measurements = get_measurements_data(
                buyers_resources=buyers_resources,
                start_date=launch_time - pd.DateOffset(months=1),
                end_date=launch_time,
            )
            sellers_forecasts = get_sellers_data(
                sellers_resources=sellers_resources,
                start_date=launch_time - pd.DateOffset(months=1),
                end_date=forec_end_dt,
            )

            if backup_session_inputs:
                try:
                    store_session_datasets(
                        session_id=session_data["id"],
                        buyer_measurements=measurements,
                        sellers_forecasts=sellers_forecasts,
                        challenges_data=challenges_data,
                        sellers_resources=sellers_resources,
                    )
                except Exception:
                    logger.exception("Failed to backup session inputs")

            # ################################
            # Create & Run Market Session
            # ################################
            mc = MarketClass(
                n_jobs=settings.N_JOBS,
                run_benchmarks=False,
                strategies=settings.ENSEMBLE_MODELS,
            )
            mc.init_session(session_data=session_data, launch_time=launch_time)
            mc.show_session_details()
            mc.start_session(api_controller=self.api)
            # -- Load challenges data:
            mc.load_challenges(challenges=challenges_data)
            # -- Load buyers measurements data:
            mc.load_buyer_measurements(measurements=measurements)
            # -- Load forecasters data:
            mc.load_forecasters(
                sellers_resources=sellers_resources, sellers_forecasts=sellers_forecasts
            )
            # -- Run market session:
            mc.ensemble_forecast(api_controller=self.api)
            # -- Save & validate session results (raise exception if not valid)
            mc.save_session_results(save_forecasts=True)
            return True
        except Exception:
            logger.exception("Failed to run market session pipeline.")
            return False

    @staticmethod
    def __check_measurements_requirements(
        challenge_data, buyer_measurements, resource_id
    ):
        """
        Check if there are sufficient measurements samples to calculate scores
        for a specific challenge.
        :param challenge_data: dict, challenge information
        :param buyer_measurements: pd.DataFrame, buyer measurements data
        :param resource_id: str, resource ID
        :return: bool, True if there are sufficient measurements samples,
                 False otherwise
        """
        start_dt_ = pd.to_datetime(challenge_data["start_datetime"])
        end_dt_ = pd.to_datetime(challenge_data["end_datetime"])
        expected_dates = pd.date_range(
            start=start_dt_, end=end_dt_, freq=settings.MARKET_DATA_TIME_RESOLUTION
        )
        if buyer_measurements.empty:  # No measurements:
            logger.error(f"No measurements samples for resource ID {resource_id}.")
            return False
        elif buyer_measurements.reindex(expected_dates)["value"].isnull().any():
            logger.error(
                f"Insufficient measurements samples for resource ID {resource_id}."
            )
            return False
        else:
            return True

    def calculate_scores(self, update_scores=False):
        # Get today date:
        today_date = dt.datetime.utcnow().date()
        # Delete scores & contributions for the past month (if requested):
        if update_scores:
            # IF
            start_date = delete_current_month_scores_and_weights(today_date=today_date)
        else:
            # The start date should be the first day of the month
            #  which can be extracted from today date:
            start_date = today_date.replace(day=1)

        # Fetch challenges without scores since start_date:
        log_msg_ = f"[UPDATE={update_scores}] Fetching challenges without scores since {start_date} ..."
        logger.info(log_msg_)
        challenges_list = get_challenges_for_scoring(start_date=start_date)
        logger.success(f"{log_msg_} ... Ok!")

        # ###########################################################
        # Check if there are sufficient challenges with submissions
        # ###########################################################
        if len(challenges_list) == 0:
            logger.error("There are no challenges since {start_date}.")
            return False

        logger.info(f"Found {len(challenges_list)} challenges.")

        scores_status = []
        for challenge in challenges_list:
            logger.info("-" * 79)
            logger.info("-" * 79)
            logger.info(f"Working on challenge:\n{challenge} ... ")
            # Get challenge info:
            buyer_resource_id = challenge["resource"]
            challenge_id = challenge["challenge"]
            start_dt = challenge["start_datetime"]
            end_dt = challenge["end_datetime"]
            # Query agents measurements:
            measurements = get_measurements_data(
                buyers_resources=[buyer_resource_id],
                start_date=start_dt,
                end_date=end_dt,
            )[buyer_resource_id]

            # Check if there are sufficient measurements samples to continue:
            if not self.__check_measurements_requirements(
                challenge_data=challenge,
                buyer_measurements=measurements,
                resource_id=buyer_resource_id,
            ):
                logger.error(
                    f"Failed challenge {challenge['challenge']} for "
                    f"resource {buyer_resource_id} due to "
                    f"insufficient measurements samples."
                )
                scores_status.append(False)
                continue

            #################################
            # Query relevant data:
            ################################
            # Get forecasters submission list:
            submission_list = self.api.list_challenges_submissions(
                challenge_id=challenge_id
            )
            # -- Get list of unique forecasters (sellers) users:
            sellers_users = list(set([x["user"] for x in submission_list]))
            # Get sellers submissions:
            submission_forecasts = get_sellers_submissions(
                sellers_users=sellers_users, challenge_id=challenge_id
            )

            # Check if submission forecasts is an empty dict:
            if len(submission_forecasts) == 0:
                logger.error(
                    f"Failed challenge {challenge['challenge']} for "
                    f"resource {buyer_resource_id} has no "
                    f"forecaster submissions."
                )
                scores_status.append(False)
                continue

            # Get ensemble forecasts:
            ensemble_forecasts = get_ensemble_forecasts(
                challenge_id=challenge_id, ensemble_models=settings.ENSEMBLE_MODELS
            )
            #############################
            # Calculate & Upload Scores:
            #############################
            # Load Market Class and calculate Weights & Scores:
            mc = MarketClass(n_jobs=settings.N_JOBS)
            # Calculate forecasters scores:
            try:
                forecaster_scores = mc.forecaster_scores(
                    buyer_measurements=measurements,
                    sellers_forecasts=submission_forecasts,
                    challenge_data=challenge,
                )
                scores_status.append(True)
            except Exception:
                logger.exception(
                    f"Failed to calculate forecaster scores for "
                    f"challenge {buyer_resource_id}."
                )
                scores_status.append(False)
                continue

            # Post forecasters scores:
            try:
                self.api.post_submission_scores(
                    challenge_id=challenge_id, scores=forecaster_scores
                )
            except Exception:
                logger.exception("Error! Failed to upload submission scores")
                # Todo: @Ricardo - raise alert to admin

            # Calculate ensemble forecasts:
            # If the challenge has no ensemble forecasts - skip:
            if len(ensemble_forecasts) == 0:
                logger.error(
                    f"Failed challenge {challenge['challenge']} for "
                    f"resource {buyer_resource_id} has no "
                    f"ensemble forecasts."
                )
                # Important: The forecasters will not be evaluated IF
                scores_status.append(False)
                continue

            # Calculate ensemble scores:
            try:
                ensemble_scores = mc.ensemble_scores(
                    buyer_measurements=measurements,
                    ensemble_forecasts=ensemble_forecasts,
                    challenge_data=challenge,
                )
            except Exception:
                logger.exception(
                    f"Failed to calculate ensemble scores for "
                    f"challenge {buyer_resource_id}."
                )
                continue

            # Post ensemble scores:
            try:
                self.api.post_ensemble_scores(
                    challenge_id=challenge_id, scores=ensemble_scores
                )
            except Exception:
                logger.exception("Error! Failed to upload ensemble scores")
                # Todo: @Ricardo - raise alert to admin

            logger.success(f"Working on challenge:\n{challenge} ... Ok!")

        if sum(scores_status) == len(challenges_list):
            return 0
        elif sum(scores_status) > 0:
            return 1
        elif sum(scores_status) == 0:
            return 2

        return None

    @staticmethod
    def __filter_partial_submissions(submissions, scores):
        # Identify users with partial submissions:
        submission_cnt = submissions.groupby(["challenge_id", "user_id"]).count()[
            "variable"
        ]  # noqa
        # Users should always have submissions for at least 3 quantiles:
        partial_submissions = submission_cnt[submission_cnt != 3].index.to_list()
        # Log warning if partial submissions found:
        if len(partial_submissions) > 0:
            logger.warning(
                f"Found {len(partial_submissions)} partial "
                f"submissions. These will be removed from scores."
            )
        # Remove partial submissions:
        for ps in partial_submissions:
            # Remove partial submissions:
            scores = scores.loc[
                ~((scores["challenge_id"] == ps[0]) & (scores["user_id"] == ps[1]))
            ]

        return scores

    def aggregate_scores(self, previous_month=False, year=None, month=None):
        track_metrics = {
            "deterministic": "rmse",
            "probabilistic": "winkler",
        }
        # Quantile references:
        track_variable_references = {
            "deterministic": "q50",
            "probabilistic": "q90",  # considers both q10 and q90
        }

        # Add a set of expected dates to be removed from the report scores:
        dates_to_remove = []

        # If year and month are explicitly provided, use them directly
        if year is not None and month is not None:
            start_date = dt.datetime(year, month, 1).date()
            # Get last day of specified month:
            end_date = (
                pd.Timestamp(start_date)
                + pd.DateOffset(months=1)
                - pd.DateOffset(days=1)
            ).date()
        elif previous_month:
            # Get today date:
            today_date = dt.datetime.utcnow().date()
            # Get first day of previous month:
            start_date = today_date.replace(day=1) - pd.DateOffset(months=1)
            year = start_date.year
            month = start_date.month
            # Get last day of previous month:
            end_date = today_date.replace(day=1) - pd.DateOffset(days=1)
        else:
            # Use current month
            today_date = dt.datetime.utcnow().date()
            start_date = today_date.replace(day=1)
            year = start_date.year
            month = start_date.month
            # Get last day of current month:
            end_date = (start_date + pd.DateOffset(months=1)) - pd.DateOffset(days=1)

        # List user resources, registered in the platform:
        resources = self.api.list_user_resources()
        # Filter active resources only:
        resources = [x for x in resources if x["is_active"]]
        logger.info(f"Found {len(resources)} active resources.")
        request_payload = []
        # For each resource, load scores and calculate aggregated stats:
        for resource in resources:
            logger.info("-" * 79)
            logger.info(f"Working on resource:\n{resource}")

            # Get resource ID and local tz:
            resource_id = resource["id"]

            # Get forecasters participation type by resource:
            # Returns Dict with
            #   key = user_id
            #   value = true if is_fixed_payment else False
            # -- We'll use this information to disable league and ranking
            # calculation for fixed payment forecasters for now
            participation_type = get_resource_participation_type(
                resource_id=resource_id,
            )

            # Get scores per resource:
            scores = get_scores_per_resource(
                resource_id=resource_id,
                start_dt=start_date,
                end_dt=end_date,
                evaluation_metrics=list(track_metrics.values()),
                remove_fixed_payment=False,
            )
            # Get forecaster submissions:
            submissions = get_submissions_by_resource(
                resource_id=resource_id,
                start_date=start_date,
                end_date=end_date,
            )
            # Remove scores incomplete submissions (i.e., missing quantiles):
            scores = self.__filter_partial_submissions(
                submissions=submissions, scores=scores
            )

            # Forecasts & observed data:
            seller_forecasts = get_sellers_forecasts_by_resource(
                resource_id=resource_id,
                start_date=start_date,
                end_date=end_date,
            )

            # Observed:
            measurements = get_measurements_data_by_resource(
                resource_id=resource_id,
                start_date=seller_forecasts[
                    "datetime"
                ].min(),  # period alignment w/ forecasts
                end_date=seller_forecasts[
                    "datetime"
                ].max(),  # period alignment w/ forecasts
            )

            ####################################################
            # For each track, do:
            # - Daily rankings
            # - Average scores
            # - League assignments
            # - Error distributions (residuals and boxplot per power bin)
            ####################################################
            for track, metric in track_metrics.items():
                logger.info(
                    f"Calculating aggregate scores for track {track} "
                    f"and metric {metric}."
                )
                # Variable to filter:
                ref_variable = track_variable_references[track]

                # Filter by metric:
                track_scores = scores.loc[
                    (scores["metric"] == metric) & (scores["variable"] == ref_variable)
                ].copy()

                # Init KPI class and load scores (creates copy)
                kc = KpiClass().load_scores(track_scores, track=track)
                # Remove scores for user-defined dates (if any):
                kc.remove_dates(date_list=dates_to_remove)
                # Remove fixed payment (contracted) forecasters from rankings
                # & leagues calculations:
                kc.remove_fixed_payment(participation_type=participation_type)
                # Calculate daily rankings:
                kc.daily_ranking()
                # Calculate average scores:
                kc.average_scores()
                # Calculate average scores w/ penalties (for missing days):
                kc.average_scores_w_penalty()  # these are used for payments
                # Assign league positions to the avg_scores df:
                kc.find_forecaster_league()
                # Calculate league thresholds:
                kc.calculate_league_thresholds()
                kc.calculate_distributions(
                    forecasts=seller_forecasts,
                    observed=measurements,
                )
                # Prepare report JSON:
                report_json = aggregated_metrics_json(
                    year=year,
                    month=month,
                    resource_id=resource_id,
                    metric=metric,
                    track=track,
                    participation_type=participation_type,
                    nr_participants=kc.nr_participants,
                    month_scores=kc.month_scores,
                    month_scores_w_pen=kc.month_scores_w_pen,
                    month_ranks=kc.month_ranks,
                    daily_ranks=kc.daily_ranks,
                    daily_scores_w_pen=kc.daily_scores_w_pen,
                    league_assignments=kc.league,
                    n_days_w_penalties=kc.n_days_w_penalties,
                    days_wout_submissions=kc.days_wout_submissions,
                    month_scores_ranked=kc.month_scores_ranked,
                    league_thresholds=kc.league_thresholds,
                    residual_distributions=kc.residual_distributions,
                    boxplot_by_power=kc.boxplot_by_power,
                )
                request_payload.extend(report_json)

        if len(request_payload) > 0:
            try:
                for resource in resources:
                    # Delete existing monthly stats for the period & resources:
                    self.api.delete_forecaster_monthly_stats(
                        year=year,
                        month=month,
                        resource_id=resource["id"],
                    )
                    logger.info(
                        f"Deleted existing monthly stats for resource "
                        f"{resource['id']} for {year}-{month:02d}."
                    )

                # Post to API
                self.api.post_forecaster_monthly_stats(stats=request_payload)
                logger.info(
                    f"Successfully uploaded {len(request_payload)} monthly stats records"
                )
                return 0
            except Exception as e:
                logger.exception(f"Failed to publish monthly stats {e}")
                return 1
        else:
            return 0
