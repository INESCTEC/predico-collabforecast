"""
Data loader for market forecasting.

This module provides the DataLoader class that handles loading and validating
market data including challenges, forecasters, and measurements.
"""

from __future__ import annotations

from time import time

import pandas as pd
from loguru import logger

try:
    from conf import settings
except ImportError:
    from ...conf import settings

from .entities.buyer import BuyerClass
from ..core import NoMarketBuyersException, NoMarketUsersException


class DataLoader:
    """
    Handles loading and validation of market data.

    This class encapsulates all data loading operations for the forecast engine:
    - Loading and validating challenges
    - Loading forecaster submissions
    - Loading buyer measurements

    Example usage::

        loader = DataLoader()
        loader.load_challenges(challenges)
        loader.load_forecasters(sellers_resources, sellers_forecasts)
        loader.load_buyer_measurements(measurements)

        # Access loaded data
        buyers_data = loader.buyers_data
    """

    def __init__(self, session_id: str | None = None):
        """
        Initialize the data loader.

        :param session_id: Optional session ID for logging context
        """
        self._session_id = session_id
        self.buyers_data: dict[str, BuyerClass] = {}
        self.sellers_resources: list = []

    def load_challenges(self, challenges: list) -> "DataLoader":
        """
        Load and validate market challenges.

        Creates BuyerClass instances for each valid challenge.

        :param challenges: List of challenge dictionaries with keys:
            - id: Challenge identifier
            - resource: Resource identifier
            - user: User identifier
            - start_datetime: Forecast start datetime
            - end_datetime: Forecast end datetime
            - use_case: Challenge use case
            - submission_list: List of submissions

        :return: self for method chaining

        :raises TypeError: If challenges is not a list of dicts
        :raises NoMarketBuyersException: If no valid challenges available
        """
        if not isinstance(challenges, list) or not all(
            isinstance(x, dict) for x in challenges
        ):
            raise TypeError("Error! challenges arg. must be a list of dicts")

        if len(challenges) == 0:
            raise NoMarketBuyersException(
                "Error! No challenges available in the market session."
            )

        # Filter out challenges with empty submission lists
        valid_challenges = []
        for challenge in challenges:
            if len(challenge["submission_list"]) == 0:
                logger.warning(
                    f"Discarding challenge '{challenge['id']}' "
                    f"from session '{self._session_id}' "
                    f"due to empty submission list."
                )
            else:
                valid_challenges.append(challenge)

        if len(valid_challenges) == 0:
            raise NoMarketBuyersException(
                "Error! No challenges available in the market session."
            )

        # Create BuyerClass instances for each challenge
        for challenge in valid_challenges:
            self.buyers_data[challenge["resource"]] = BuyerClass(
                user_id=challenge["user"],
                resource_id=challenge["resource"],
                challenge_id=challenge["id"],
                challenge_start_dt=challenge["start_datetime"],
                challenge_end_dt=challenge["end_datetime"],
                challenge_usecase=challenge["use_case"],
            ).set_forecast_range()

        return self

    def load_forecasters(
        self,
        sellers_resources: list,
        sellers_forecasts: dict,
    ) -> "DataLoader":
        """
        Load seller forecasts into buyer classes.

        Validates seller submission history and filters out sellers with
        insufficient submissions.

        :param sellers_resources: List of seller resource dictionaries with keys:
            - user: User identifier
            - variable: Variable identifier (e.g., q10, q50, q90)
            - market_session_challenge_resource_id: Target resource ID

        :param sellers_forecasts: Nested dict of forecasts:
            {user_id: {resource_id: {variable_id: DataFrame}}}

        :return: self for method chaining

        :raises TypeError: If sellers_resources is not a list
        :raises NoMarketUsersException: If no seller forecasts available
        """
        t0 = time()
        logger.debug("Loading sellers data ...")

        if not isinstance(sellers_resources, list):
            raise TypeError("Error! a list of seller resources must be provided")

        if len(sellers_forecasts) == 0:
            raise NoMarketUsersException(
                "Error! No sellers forecasts available in the market session. "
                "Skipping ..."
            )

        self.sellers_resources = sellers_resources
        logger.debug(f"\nUsers resources (to load):\nSellers: {self.sellers_resources}")

        sellers_to_ignore = []
        valid_sellers = []

        for resource_data in self.sellers_resources:
            user_id = resource_data["user"]
            variable_id = resource_data["variable"]
            target_resource = resource_data["market_session_challenge_resource_id"]

            # Get forecast created by user for target resource
            forecasts = sellers_forecasts[user_id][target_resource][variable_id]

            # Rename "value" column to avoid JOIN problems
            forecast_variable = f"{user_id}_{variable_id}"
            forecasts.rename(columns={"value": forecast_variable}, inplace=True)

            # Check submission history - ignore forecasters with insufficient submissions
            lookback_start = forecasts.index[-1] - pd.DateOffset(
                days=settings.MIN_SUBMISSION_DAYS_LOOKBACK
            )
            nr_submission_records = forecasts[lookback_start:].dropna().shape[0]

            min_required = settings.MIN_SUBMISSION_DAYS * 4 * 24  # 15-min intervals
            if nr_submission_records < min_required:
                logger.warning(
                    f"Discarding seller '{user_id}' from resource "
                    f"'{target_resource}' forecasts ensemble due to less than "
                    f"1 week of submissions."
                )
                sellers_to_ignore.append((target_resource, user_id))
            else:
                valid_sellers.append((target_resource, user_id))

            # Drop data_type column if present (identifies historical/submission)
            if "data_type" in forecasts.columns:
                forecasts.drop("data_type", axis=1, inplace=True)

            # Add forecasts to buyer class
            self.buyers_data[target_resource].add_seller(
                user_id=user_id,
                forecast_variable=forecast_variable,
                forecasts=forecasts,
            )

        # Remove duplicate entries
        valid_sellers = list(set(valid_sellers))
        sellers_to_ignore = list(set(sellers_to_ignore))

        # Remove ignored sellers only if there are valid sellers remaining
        if len(valid_sellers) > 0 and len(sellers_to_ignore) > 0:
            for target_resource, user_id in sellers_to_ignore:
                self.buyers_data[target_resource].remove_seller(user_id)

        logger.debug(f"Loading sellers data ... Ok! {t0 - time():.2f}s")
        return self

    def load_buyer_measurements(self, measurements: dict) -> "DataLoader":
        """
        Load measurement data into buyer classes.

        :param measurements: Dictionary mapping resource_id to measurement DataFrame

        :return: self for method chaining

        :raises TypeError: If measurements is not a dict
        """
        if not isinstance(measurements, dict):
            raise TypeError("Error! measurements arg. must be a dict")

        buyers_resources = list(self.buyers_data.keys())
        default_df = pd.DataFrame(columns=["datetime", "value"])

        for resource_id in sorted(buyers_resources):
            df = measurements.get(resource_id, default_df)
            self.buyers_data[resource_id].set_measurements(df)

        return self

    @staticmethod
    def preprocess_buyer_data(
        data: pd.DataFrame,
        expected_dates: pd.DatetimeIndex,
    ) -> pd.DataFrame:
        """
        Resample and reindex data to expected time resolution.

        Missing dates are marked as NA.

        :param data: DataFrame with datetime index
        :param expected_dates: Expected datetime index

        :return: Resampled and reindexed DataFrame
        """
        freq = settings.MARKET_DATA_TIME_RESOLUTION
        data = data.resample(freq).mean()
        data = data.reindex(expected_dates)
        return data

    def get_valid_challenges(self) -> list:
        """
        Get list of valid challenge dictionaries.

        :return: List of challenge dicts for valid buyers
        """
        return [
            {
                "id": buyer.challenge_id,
                "resource": buyer.resource_id,
                "user": buyer.user_id,
            }
            for buyer in self.buyers_data.values()
        ]
