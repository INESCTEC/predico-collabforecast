import uuid
import numpy as np
import pandas as pd

from typing import Union, Dict
from dataclasses import dataclass, field

try:
    from conf import settings
except ImportError:
    # this is needed for testing purposes
    from ....conf import settings

from ..helpers.class_helpers import ValidatorClass


@dataclass()
class BuyerClass(ValidatorClass):
    challenge_id: Union[int, str, uuid.UUID] = None  # Challenge identifier
    challenge_usecase: str = None  # Challenge use case
    resource_id: Union[int, str] = None  # Challenge resource identifier
    user_id: Union[int, str] = None  # Challenge user identifier
    challenge_start_dt: str = None  # Challenge forecast start datetime
    challenge_end_dt: str = None  # Challenge forecast end datetime
    y: pd.DataFrame = None  # Challenge resource measurements time-series
    ensemble_weights: dict = None  # Resource id forecast weights
    forecasters_skill_scores: list = None  # Resource id forecast weights
    sellers_metadata: Dict = field(default_factory=dict)  # Sellers data
    sellers_forecasts: pd.DataFrame = None  # Sellers forecasts
    forecast_range = None
    historical_start = None
    dataset_range = None
    forecast_model = None
    strategy_forecasts: Dict[str, pd.DataFrame] = field(default_factory=dict)
    sellers_features: list = None
    sellers_features_used: list = None

    def validate_attributes(self):
        if self.user_id is None:
            raise ValueError("BuyerClass user_id not defined.")
        if self.resource_id is None:
            raise ValueError("BuyerClass resource_id not defined.")
        if self.challenge_id is None:
            raise ValueError("BuyerClass challenge_id not defined.")
        if self.challenge_start_dt is None:
            raise ValueError("BuyerClass challenge_start_dt not defined.")
        if self.challenge_end_dt is None:
            raise ValueError("BuyerClass challenge_end_dt not defined.")
        self.validate_attr_types()
        return self

    @property
    def details(self):
        return {
            "user_id": self.user_id,
            "resource_id": self.resource_id,
            "challenge_id": self.challenge_id,
            "challenge_usecase": self.challenge_usecase,
            "ensemble_weights": self.ensemble_weights,
            "forecasters_skill_scores": self.forecasters_skill_scores,
            "forecast_model": self.forecast_model,
        }

    def set_measurements(self, data):
        # round y index to closest time freq interval
        freq = settings.MARKET_DATA_TIME_RESOLUTION
        self.historical_start = data.index[0].round(freq)
        # prepare expected historical dataset range time intervals:
        self.dataset_range = pd.date_range(
            start=self.historical_start,
            end=self.challenge_end_dt,
            freq=freq,
            tz="utc",
            inclusive="both",
        )
        # reindex raw data to ensure to expected frequency:
        # todo: check if there's a need to fill missing values
        self.y = data.reindex(self.dataset_range, fill_value=np.nan)
        # initialize sellers forecasts dataframe (empty)
        # note: this DF will be used to store / join sellers forecasts
        self.sellers_forecasts = pd.DataFrame(index=self.dataset_range)
        return self

    def add_seller(self, user_id, forecast_variable, forecasts):
        if user_id not in self.sellers_metadata:
            self.sellers_metadata[user_id] = []
        self.sellers_metadata[user_id].append(forecast_variable)
        self.sellers_forecasts = self.sellers_forecasts.join(forecasts, how="outer")
        return self

    def set_strategy_forecasts(self, engine_results: dict) -> "BuyerClass":
        """Store all strategy forecast results.

        :param engine_results: Dict mapping strategy_name -> ForecastResult
        :return: Self for method chaining
        """
        for strategy_name, result in engine_results.items():
            if result is not None and result.predictions is not None:
                self.strategy_forecasts[strategy_name] = result.predictions
        return self

    def get_strategy_forecast(self, strategy_name: str) -> pd.DataFrame | None:
        """Get forecast for a specific strategy.

        :param strategy_name: Name of the strategy
        :return: DataFrame with predictions or None
        """
        return self.strategy_forecasts.get(strategy_name)

    @property
    def all_forecasts_dict(self) -> dict:
        """Return all strategy forecasts formatted for reporting.

        :return: Dict with resource_id, and forecasts per strategy
        """
        result = {
            "resource": self.resource_id,
            "strategies": {},
        }
        for strategy_name, forecasts_df in self.strategy_forecasts.items():
            if forecasts_df is not None and not forecasts_df.empty:
                f_ = forecasts_df.copy()
                f_["value"] = f_["value"].round(6)
                f_["datetime"] = f_["datetime"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                result["strategies"][strategy_name] = f_.to_dict(orient="records")
        return result

    def set_sellers_features_used(self, sellers_features, sellers_features_used):
        self.sellers_features = sellers_features
        self.sellers_features_used = sellers_features_used
        return self

    def set_forecast_range(self):
        freq = settings.MARKET_DATA_TIME_RESOLUTION
        self.forecast_range = pd.date_range(
            start=self.challenge_start_dt,
            end=self.challenge_end_dt,
            freq=freq,
            tz="utc",
            inclusive="both",
        )
        return self

    def set_forecasters_skill_scores(self, scores):
        self.forecasters_skill_scores = scores
        return self

    def remove_seller(self, user_id):
        # Select columns to remove and drop them from sellers_forecasts DF
        cols_to_remove = self.sellers_metadata.pop(user_id, None)
        # remove user forecasts from sellers_forecasts DF:
        self.sellers_forecasts.drop(columns=cols_to_remove, inplace=True)
        return self
