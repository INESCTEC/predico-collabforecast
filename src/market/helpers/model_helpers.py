import numpy as np
import pandas as pd

from conf import settings
from src.market.models.linear import linear_regression_pipe as forecast_model


def create_forecast_mock(train_features,
                         train_targets,
                         test_features_df,
                         **kwargs):
    freq = settings.MARKET_DATA_TIME_RESOLUTION
    _st = test_features_df.index[0]
    _et = test_features_df.index[-1]
    _ts = pd.date_range(_st, _et, freq=freq, tz="utc", inclusive="both")

    # Create 4 variable forecasts ("q10", "q50", "q90"):
    forecasts = pd.DataFrame()
    for v in ["q10", "q50", "q90"]:
        _rand = np.random.uniform(low=0, high=1, size=len(_ts))
        _forecasts = pd.DataFrame({
            "datetime": _ts,
            "value": _rand,
            "variable": [v] * len(_ts),
        })
        forecasts = pd.concat([forecasts, _forecasts], axis=0)

    return forecasts


def create_forecast(train_features, train_targets, test_features_df):
    forecasts_df = pd.DataFrame(index=test_features_df.index)
    X_forecast = test_features_df.values

    # Generate forecasts:
    pipe = forecast_model()
    pipe.fit(train_features, train_targets)
    forecasts = pipe.predict(X_forecast)

    # Compute forecasts:
    forecasts_df["value"] = forecasts.ravel()
    forecasts_df.index.name = "datetime"
    return forecasts_df
