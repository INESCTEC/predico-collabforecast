import json
import pandas as pd
import datetime as dt

from loguru import logger

from conf import settings

from .database.PostgresDB import PostgresDB
from .api import Controller
from .market import MarketClass
from .market.helpers.api_helpers import (
    get_session_data,
)
from .market.helpers.db_helpers import (
    get_measurements_data,
    get_sellers_data,
    get_sellers_submissions,
    get_challenges_without_weights
)
from .market.helpers.backup_helpers import store_session_datasets


class MarketController:
    def __init__(self):
        # Market API Controller:
        self.api = Controller()
        self.api.login(email=settings.MARKET_EMAIL,
                       password=settings.MARKET_PASSWORD)

        # Attempt to establish DB connection (if it fails, we need to stop
        # the code here to avoid interaction problems later)
        db = PostgresDB.get_db_instance(config_name="default")
        # try to connect:
        if not db.test_connection():
            raise Exception(f"Failed to connect to project database {db.engine}.") # noqa

    def open_market_session(self, force_new=False):
        """
        If there are no market sessions, creates 1st session w/ default params
        Else, searches for last 'staged' session and opens it

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
                    finish_ts=dt.datetime.utcnow()
                )
        # Get create new market session:
        session = self.api.create_market_session()
        logger.debug(session)

    def finish_market_session(self):
        """
        Finish last open market session.
        """
        # List last market 'open' sessions:
        current_session = self.api.list_last_session()
        logger.debug("Current session:")
        if current_session:
            logger.debug(current_session)
            logger.debug("Finishing current session ...")
            self.api.update_market_session(
                session_id=current_session["id"],
                status="finished",
                finish_ts=dt.datetime.utcnow()
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
            session_id=session_id,
            status=new_status
        )
        logger.info(json.dumps(status, indent=2))
        logger.info("")

    def close_market_session(self):
        """
        Close current 'OPEN' market session

        :return:
        """
        # List last market 'open' sessions:
        open_session = self.api.list_last_session(status='open')
        logger.info("Current 'OPEN' session:")
        logger.info(open_session)
        logger.info("")

        # Change market session status from 'OPEN' to 'CLOSED':
        self.api.update_market_session(
            session_id=open_session["id"],
            status="closed",
            close_ts=dt.datetime.utcnow()
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

        # Dynamic launch time -> according to market session opening
        launch_time = pd.to_datetime(session_data["open_ts"], format="%Y-%m-%dT%H:%M:%S.%fZ", utc=True)
        launch_time = launch_time.to_pydatetime()
        # ###########################################################
        # Check if there are sufficient challenges with submissions
        # ###########################################################
        if len(challenges_data) == 0:
            logger.error("There are no open challenges for this session."
                         "Session will be closed without running the market.")
            return False
        else:
            # Get challenge end date (forecasts query limiter):
            forec_end_dt = max([dt.datetime.strptime(x["end_datetime"], "%Y-%m-%dT%H:%M:%SZ") for x in challenges_data])  # noqa

        try:
            # ################################
            # Query agents measurements:
            # ################################
            measurements = get_measurements_data(
                buyers_resources=buyers_resources,
                start_date=launch_time - pd.DateOffset(months=12),
                end_date=launch_time,
            )
            sellers_forecasts = get_sellers_data(
                sellers_resources=sellers_resources,
                start_date=launch_time - pd.DateOffset(months=12),
                end_date=forec_end_dt,
            )

            if backup_session_inputs:
                try:
                    store_session_datasets(
                        session_id=session_data["id"],
                        buyer_measurements=measurements,
                        sellers_forecasts=sellers_forecasts,
                        challenges_data=challenges_data,
                        sellers_resources=sellers_resources
                    )
                except Exception:
                    logger.exception("Failed to backup session inputs")

            # ################################
            # Create & Run Market Session
            # ################################
            mc = MarketClass(n_jobs=settings.N_JOBS)
            mc.init_session(
                session_data=session_data,
                launch_time=launch_time
            )
            mc.show_session_details()
            mc.start_session(api_controller=self.api)
            # -- Load challenges data:
            mc.load_challenges(challenges=challenges_data)
            # -- Load buyers measurements data:
            mc.load_buyer_measurements(measurements=measurements)
            # -- Load forecasters data:
            mc.load_forecasters(sellers_resources=sellers_resources,
                                sellers_forecasts=sellers_forecasts)
            # -- Run market session:
            mc.ensemble_forecast(api_controller=self.api)
            # -- Save & validate session results (raise exception if not valid)
            mc.save_session_results(save_forecasts=True)
            return True
        except Exception:
            logger.exception("Failed to run market session pipeline.")
            return False

    def get_forecasters_weights(self):
        def check_measurements_requirements(challenge, measurements):
            start_dt_ = pd.to_datetime(challenge["start_datetime"])
            end_dt_ = pd.to_datetime(challenge["end_datetime"])
            expected_dates = pd.date_range(start=start_dt_, end=end_dt_,
                                           freq=settings.MARKET_DATA_TIME_RESOLUTION)
            if measurements.empty:  # No measurements:
                logger.error(f"No measurements samples for resource ID {buyer_resource_id}.")
                return False
            elif measurements.reindex(expected_dates)["value"].isnull().any():
                logger.error(f"Insufficient measurements samples for resource ID {buyer_resource_id}.")
                return False
            else:
                return True

        # ################################
        # Fetch session info
        # ################################
        logger.info("Fetching challenges without weights data ...")
        # Get session challenges:
        challenges_list = get_challenges_without_weights()
        logger.debug(f"Found {len(challenges_list)} challenges without weights.")  # noqa
        logger.info("Fetching challenges without weights data ... Ok!")
        # ###########################################################
        # Check if there are sufficient challenges with submissions
        # ###########################################################
        if len(challenges_list) == 0:
            logger.warning("There are no challenges without weights attributed.")
            return False

        weights_status = []
        scores_status = []
        for challenge in challenges_list:
            logger.info("-" * 79)
            logger.info("-" * 79)
            logger.info(f"Working on challenge:\n{challenge}")
            buyer_resource_id = challenge["resource"]
            start_dt = challenge["start_datetime"]
            end_dt = challenge["end_datetime"]
            # Query agents measurements:
            measurements = get_measurements_data(
                buyers_resources=[buyer_resource_id],
                start_date=start_dt,
                end_date=end_dt,
            )[buyer_resource_id]
            # Check if there are sufficient measurements samples to continue:
            if not check_measurements_requirements(challenge, measurements):
                weights_status.append(False)
                scores_status.append(False)
                continue
            # Get forecasters submission list:
            submission_list = self.api.list_challenges_submissions(challenge["challenge"])
            sellers_users = list(set([x["user"] for x in submission_list]))
            submission_forecasts = get_sellers_submissions(sellers_users=sellers_users, challenge_id=challenge["challenge"])
            # Load Market Class and calculate Weights & Scores:
            mc = MarketClass(n_jobs=settings.N_JOBS)
            # -- Calculate ensemble weights (contribution of each forecaster):
            try:
                mc.ensemble_weights(
                    buyer_measurements=measurements,
                    challenge_data=challenge,
                    api_controller=self.api
                )
                weights_status.append(True)
            except FileNotFoundError:
                logger.error(f"Could not find model data for "
                             f"challenge {buyer_resource_id}.")
                weights_status.append(False)
                continue
            # -- Calculate forecasters scores:
            try:
                mc.forecaster_scores(
                    buyer_measurements=measurements,
                    sellers_forecasts=submission_forecasts,
                    challenge_data=challenge,
                    api_controller=self.api
                )
                scores_status.append(True)
            except FileNotFoundError:
                logger.error(f"Could not find model data for "
                             f"challenge {buyer_resource_id}.")
                scores_status.append(False)
                continue
        if sum(weights_status) == len(challenges_list):
            return 0
        elif sum(weights_status) > 0:
            return 1
        elif sum(weights_status) == 0:
            return 2
