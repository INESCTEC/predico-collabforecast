# ruff: noqa: E501
from django.urls import re_path

from .views.raw_data import RawDataView
from .views.market_forecasts import MarketForecastsView
from .views.individual_forecasts import (
    IndividualForecastsView,
    IndividualForecastsHistoricalCreateRetrieveView
)

app_name = "data"

urlpatterns = [
    re_path('raw-measurements/?$', RawDataView.as_view(), name="raw-measurements"),
    # re_path('market-forecasts/?$', MarketForecastsView.as_view(), name="market-forecasts"),
    # re_path('individual-forecasts?$', IndividualForecastsView.as_view(), name="individual-forecasts"),
    re_path('individual-forecasts/historical?$', IndividualForecastsHistoricalCreateRetrieveView.as_view(), name="individual-forecasts"),
]
