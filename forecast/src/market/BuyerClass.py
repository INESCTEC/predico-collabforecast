import uuid
import numpy as np
import pandas as pd

from typing import Union, Dict
from dataclasses import dataclass, field

from ...conf import settings
from .helpers.class_helpers import ValidatorClass


@dataclass()
class BuyerClass(ValidatorClass):
    challenge_id: Union[int, str, uuid.UUID] = None           # Challenge identifier
    challenge_usecase: str = None  # Challenge use case
    resource_id: Union[int, str] = None             # Challenge resource identifier
    user_id: Union[int, str] = None                 # Challenge user identifier
    challenge_start_dt: str = None                            # Challenge forecast start datetime
    challenge_end_dt: str = None                            # Challenge forecast end datetime
    y: pd.DataFrame = None              # Challenge resource measurements time-series
    ensemble_forecasts: pd.DataFrame = None      # Resource id market forecasts
    ensemble_weights: dict = None      # Resource id forecast weights
    forecasters_skill_scores: list = None      # Resource id forecast weights
    sellers_metadata: Dict = field(default_factory=dict)  # Sellers data
    sellers_forecasts: pd.DataFrame = None  # Sellers forecasts
    forecast_range = None
    historical_start = None
    dataset_range = None
    forecast_model = None

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
            "forecast_model": self.forecast_model
        }

    @property
    def forecasts_dict(self):
        f_ = self.ensemble_forecasts.copy()
        f_["value"] = f_["value"].round(6)
        f_["datetime"] = f_["datetime"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        f_ = f_.to_dict(orient="records")
        return {
            "resource": self.resource_id,
            "model": self.forecast_model,
            "forecasts": f_
        }

    def set_measurements(self, data):
        # round y index to closest time freq interval
        freq = settings.MARKET_DATA_TIME_RESOLUTION
        self.historical_start = data.index[0].round(freq)
        # prepare expected historical dataset range time intervals:
        self.dataset_range = pd.date_range(start=self.historical_start,
                                           end=self.challenge_end_dt,
                                           freq=freq,
                                           tz="utc",
                                           inclusive="both")
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

    def set_ensemble_forecasts(self, model, forecasts):
        self.ensemble_forecasts = forecasts
        self.forecast_model = model
        return self

    def set_forecast_range(self):
        freq = settings.MARKET_DATA_TIME_RESOLUTION
        self.forecast_range = pd.date_range(start=self.challenge_start_dt,
                                            end=self.challenge_end_dt,
                                            freq=freq,
                                            tz="utc",
                                            inclusive="both")
        return self

    def set_ensemble_weights(self, weights):
        self.ensemble_weights = weights
        return self

    def set_forecasters_skill_scores(self, scores):
        self.forecasters_skill_scores = scores
        return self
