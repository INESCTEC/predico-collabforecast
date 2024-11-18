import numpy as np
import pandas as pd

from typing import Union
from dataclasses import dataclass
from .helpers.class_helpers import ValidatorClass


@dataclass
class SellerClass(ValidatorClass):
    user_id: Union[int, str] = None                 # Resource User ID
    user_forecasts: dict = None   # Resource forecasts (key: target / value: forecast df)

    def validate_attributes(self):
        if self.user_id is None:
            raise ValueError("SellerClass user_id not defined.")
        self.validate_attr_types()
        return self

    @property
    def details(self):
        return {
            "user_id": self.user_id,
            "user_forecasts": self.user_forecasts
        }
