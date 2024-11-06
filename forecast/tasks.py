import fire

from time import time, sleep
from loguru import logger
from dotenv import load_dotenv

load_dotenv(".env")

from src.MarketController import MarketController
from src.api.exception.APIException import (NoMarketSessionException)


def retry(func, max_attempts=3, delay=1, retry_if_result_false=False,
          exceptions=(Exception,)):
    for attempt in range(max_attempts):
        try:
            result = func()
            if retry_if_result_false and not result:
                raise Exception("Unable to perform operation")
            return result
        except exceptions:
            logger.debug(f"Attempt ({attempt + 1}/{max_attempts}) failed")
            if attempt < max_attempts - 1:
                logger.debug(f"Retrying after {delay}s ...")
                sleep(delay)
    raise Exception("Max attempts reached, could not get a valid result")


class MarketTasks(object):

    def __init__(self):
        self.transfer_out_validate_retry_delay = 30
        self.transfer_out_validate_retry_attempts = 15
        self.dlt_confirm_wait_time = 5

    @staticmethod
    def open_session():
        """
        Open a market session. If there are no market sessions, creates
        1st session.
        """
        logger.info("-" * 79)
        t0 = time()
        msg_ = "Opening session ..."
        logger.info(msg_)
        try:
            # Init market controller:
            market = MarketController()
            # Attempt to open market session:
            market.open_market_session()
            logger.success(f"{msg_} Ok! {time() - t0:.2f}s")
        except Exception:
            logger.exception(f"{msg_} Failed! {time() - t0:.2f}s")

    @staticmethod
    def calculate_ensemble_weights():
        """
        Calculate forecasters contributions to ensemble
        1. Query challenges with pending weight attributions
        2. Calculate forecasters weights for these challenges
        3. Save forecasters weights
        """
        logger.info("-" * 79)
        t0 = time()
        msg_ = "Calculating ensemble weights ..."
        logger.info(msg_)

        try:
            # Init market controller:
            market = MarketController()
            # Run market session:
            status = market.get_forecasters_weights()
            if status == 0:
                logger.success(f"{msg_} Ok! {time() - t0:.2f}s")
            elif status == 1:
                logger.warning(f"{msg_} Failed for some! {time() - t0:.2f}s")
            else:
                logger.error(f"{msg_} Failed! {time() - t0:.2f}s")
        except Exception:
            logger.exception(f"{msg_} Failed! {time() - t0:.2f}s")

    @staticmethod
    def run_session():
        """
        Run a market session.
        1. Closes current open market session ( stops bidding )
        2. Executes market session
        3. Opens next market session
        """
        logger.info("-" * 79)
        t0 = time()
        msg_ = "Running session ..."
        logger.info(msg_)

        try:
            # Init market controller:
            market = MarketController()
            # Close open market session (no more submissions):
            market.close_market_session()
            # Run market session:
            status = market.run_market_session(backup_session_inputs=True)
            if status:
                logger.success(f"{msg_} Ok! {time() - t0:.2f}s")
            else:
                logger.error(f"{msg_} Failed! {time() - t0:.2f}s")

            logger.info("Finishing market session ...")
            market.finish_market_session()
            logger.success("Finishing market session ... Ok!")

        except NoMarketSessionException:
            # NoMarketSession exception is raised when there is no
            # open session to run
            logger.error(f"{msg_} Failed! {time() - t0:.2f}s")
        except Exception:
            logger.exception(f"{msg_} Failed! {time() - t0:.2f}s")
        finally:
            market = MarketController()
            logger.info("Finishing market session ...")
            market.finish_market_session()
            logger.success("Finishing market session ... Ok!")


if __name__ == '__main__':
    fire.Fire(MarketTasks)
