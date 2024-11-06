# flake8: noqa
import os
import gc

from time import time
from copy import deepcopy
from loguru import logger

# -- If needed to run via command line, add root proj to sys path:
os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from forecast.src.market import MarketClass

from simulation import SessionGenerator, AgentsLoader, SimulatorManager


if __name__ == '__main__':

    # -- Setup logger (removes existing logger + adds new sys logger):
    # logger.remove()
    # logger.add(sys.stderr, level="DEBUG")

    # Set base simulation parameters:
    N_JOBS = 1
    simulation_params = {
        "dataset_path": "files/datasets/example_elia",
        "report_name_suffix": "test",
        "nr_sessions": 10,
        "first_lt_utc": "2023-02-15T10:30:00Z",
        "session_freq": 24,
        "datetime_fmt": "%Y-%m-%d %H:%M",
        "delimiter": ","
    }

    # Load Session Configs:
    manager = SimulatorManager(**simulation_params)

    # -- Run market sessions:
    for session_id, market_lt in manager.SESSIONS_LIST:
        logger.info("/" * 79)
        logger.info("\\" * 79)
        market_lt = market_lt.to_pydatetime()
        general_t0 = time()
        # ###################################################
        # Create Mock Data Agents:
        # ###################################################
        # Create fictitious bids:
        ag = AgentsLoader(
            launch_time=market_lt,
            market_session=session_id,
            data_path=manager.DATASET_PATH,
            datetime_fmt=manager.DATETIME_FMT,
            delimiter=manager.DATA_DELIMITER
        ).load_datasets()
        # User data:
        measurements = ag.measurements
        buyers_resources = ag.buyers_resources
        sellers_resources = ag.sellers_resources
        sellers_forecasts = ag.forecasts
        # Store buyers/sellers resources for later report:
        manager.set_buyers_resources(buyers_resources)
        manager.set_sellers_resources(sellers_resources)

        # #########################################
        # Create Mock Data Session
        # #########################################
        sg = SessionGenerator()
        # Create session:
        buyers = [x for x in ag.buyers_resources]
        sg.create_session(session_id=session_id,
                          launch_time=market_lt,
                          buyers_data=buyers)
        sg.create_session_challenges()
        sg.create_submissions_to_challenges(sellers_resources=sellers_resources)
        # Session data:
        session_data = sg.session_data
        challenges = sg.challenges_data
        # ################################
        # Run Market Session
        # ################################
        mc = MarketClass(n_jobs=N_JOBS)
        # -- Initialize market session:
        mc.init_session(
            session_data=session_data,
            launch_time=market_lt
        )
        # -- Display session details:
        mc.show_session_details()
        # -- Load challenges data:
        mc.load_challenges(challenges=challenges)
        # -- Load buyers resources measurements data:
        mc.load_buyer_measurements(measurements=measurements)
        # -- Load forecasters data:
        mc.load_forecasters(sellers_resources=sellers_resources,
                            sellers_forecasts=sellers_forecasts)
        # -- Run market session:
        mc.ensemble_forecast()
        # -- Calculate weights:
        for challenge in challenges:
            # Filter measurements data for this buyer / challenge period
            measurements_ = ag.load_challenge_measurements_data(
                resource_list=[challenge["resource"]],
                start_date=challenge["start_datetime"],
                end_date=challenge["end_datetime"]
            )
            measurements_ = measurements_[challenge["resource"]]
            mc.ensemble_weights(challenge_data=challenge,
                                buyer_measurements=measurements_)
        # -- Save & validate session results (raise exception if not valid)
        mc.save_session_results(save_forecasts=True)
        #################################
        # Finalize Session
        #################################
        manager.add_session_reports(
            session_id=session_id,
            session_lt=market_lt,
            session_details=deepcopy(mc.mkt_sess.details),
            session_buyers_results=deepcopy(mc.mkt_sess.buyers_results),
            session_buyers_forecasts=deepcopy(mc.mkt_sess.buyers_forecasts),
            session_buyers_weights=deepcopy(mc.mkt_sess.buyers_weights)
        )
        # Save reports to csv:
        elapsed_time = time() - general_t0
        manager.save_reports(sess_elapsed_time=elapsed_time)

        # Delete objects to free memory
        del mc
        del ag
        del sg
        gc.collect()
