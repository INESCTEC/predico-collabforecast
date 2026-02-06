import fire

from time import time, sleep
from loguru import logger

# -- Uncomment for local development:
# from dotenv import load_dotenv
# load_dotenv(".dev.env")

from src.MarketController import MarketController  # noqa: E402
from src.core import NoMarketSessionException  # noqa: E402


def retry(
    func, max_attempts=3, delay=1, retry_if_result_false=False, exceptions=(Exception,)
):
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
    @staticmethod
    def open_session(gate_closure_hour: int = 10):
        """
        Open a market session. If there are no market sessions, creates
        1st session.

        ATTENTION:
         - this task should be run only once per session!
         - gate closure hour should be set in CET timezone!

        :param gate_closure_hour: Hour (0-23) in CET for gate closure.
            Default is 10 (10:00 CET).
            The next occurrence of this hour will be used as gate closure.
            Examples:
                python tasks.py open_session  # 10:00 CET (default)
                python tasks.py open_session --gate_closure_hour=23  # 23:00 CET
                python tasks.py open_session --gate_closure_hour=14  # 14:00 CET
        """
        if not 0 <= gate_closure_hour <= 23:
            raise ValueError("gate_closure_hour must be between 0 and 23")

        logger.info("-" * 79)
        t0 = time()
        msg_ = f"Opening session (gate closure at {gate_closure_hour:02d}:00 CET) ..."  # noqa
        logger.info(msg_)
        try:
            # Init market controller:
            market = MarketController()
            # Attempt to open market session:
            market.open_market_session(gate_closure_hour=gate_closure_hour)
            logger.success(f"{msg_} Ok! {time() - t0:.2f}s")
        except Exception:
            logger.exception(f"{msg_} Failed! {time() - t0:.2f}s")

    @staticmethod
    def calculate_scores(update_scores: bool):
        """
        Calculate forecaster submission scores for previous month(s) challenges
        1. Query submissions for previous month(s) challenges
        2. Calculate forecasting skill scores
        3. Save / update submission scores

        :param update_scores: bool, whether to update existing scores
        False: do not update existing scores
        True: update existing scores
        """
        logger.info("-" * 79)
        t0 = time()
        msg_ = "Calculating forecasting skill scores ..."
        logger.info(msg_)

        try:
            # Init market controller:
            market = MarketController()
            # Calculate submission scores for previous month(s) challenges:
            status = market.calculate_scores(update_scores=update_scores)
            if status == 0:
                logger.success(f"{msg_} Ok! {time() - t0:.2f}s")
            elif status == 1:
                logger.warning(f"{msg_} Failed for some! {time() - t0:.2f}s")
            else:
                logger.error(f"{msg_} Failed! {time() - t0:.2f}s")
        except Exception:
            logger.exception(f"{msg_} Failed! {time() - t0:.2f}s")

    @staticmethod
    def aggregate_scores(
        previous_month: bool = False, year: int = None, month: int = None
    ):
        """
        Aggregate forecaster submission scores by month and resource

        :param previous_month: bool, whether to use previous month (default: False = current month)
        :param year: int, optional specific year to aggregate (overrides previous_month)
        :param month: int, optional specific month to aggregate (1-12, overrides previous_month)

        Examples:
            python tasks.py aggregate_scores  # current month
            python tasks.py aggregate_scores --previous_month=True  # previous month
            python tasks.py aggregate_scores --year=2024 --month=11  # specific month
        """
        logger.info("-" * 79)
        t0 = time()
        msg_ = "Aggregating monthly forecasting skill scores ..."
        logger.info(msg_)

        try:
            # Init market controller:
            market = MarketController()
            # Calculate submission scores for previous month(s) challenges:
            status = market.aggregate_scores(
                previous_month=previous_month, year=year, month=month
            )
            if status == 0:
                logger.success(f"{msg_} Ok! {time() - t0:.2f}s")
            else:
                logger.error(f"{msg_} Failed! {time() - t0:.2f}s")
        except Exception:
            logger.exception(f"{msg_} Failed! {time() - t0:.2f}s")

    @staticmethod
    def calculate_payments(ignore_outstanding=True):
        """
        Calculate and upload forecasters payments to the DB
        1. Query resources
        2. Calculate forecasters payments per resource and track
        3. Save / update forecasters payments
        """

        # Add a deprecation warning
        logger.warning("calculate_payments is deprecated and will be removed "
                       "in future versions. These requests should be issued "
                       "via the RESTful API api/.")

        logger.info("-" * 79)
        t0 = time()
        msg_ = "Calculating payments ..."
        logger.info(msg_)

        try:
            # Init market controller:
            market = MarketController()
            # Run market session:
            status = market.calculate_payments(ignore_outstanding)
            if status:
                logger.success(f"{msg_} Ok! {time() - t0:.2f}s")
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
            # Prepare continuous submissions:
            market.prepare_continuous_submissions()
            # Run market session:
            status = market.run_market_session(backup_session_inputs=True)
            if status:
                logger.success(f"{msg_} Ok! {time() - t0:.2f}s")
            else:
                logger.error(f"{msg_} Failed! {time() - t0:.2f}s")

            logger.info("Finishing latest running market session ...")
            market.finish_market_session(is_running=True)
            logger.success("Finishing latest running market session ... Ok!")

        except NoMarketSessionException:
            # NoMarketSession exception is raised when there is no
            # open session to run
            logger.error(f"{msg_} Failed! {time() - t0:.2f}s")
        except Exception:
            logger.exception(f"{msg_} Failed! {time() - t0:.2f}s")
        finally:
            market = MarketController()
            logger.info("Finishing latest market session ...")
            # Close last session independently of status
            market.finish_market_session()
            logger.success("Finishing latest market session ... Ok!")


if __name__ == "__main__":
    fire.Fire(MarketTasks)
