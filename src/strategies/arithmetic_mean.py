"""
Arithmetic mean ensemble strategy.

This strategy calculates a simple (unweighted) arithmetic mean of all
forecaster predictions. All forecasters contribute equally regardless
of their historical performance.

Optionally, DTW-based outlier detection can be applied to remove
anomalous forecast profiles before averaging.

Example usage::

    from src.strategies import ArithmeticMeanStrategy

    strategy = ArithmeticMeanStrategy(outlier_detection=True)
    strategy.fit(X_train, y_train, ["q10", "q50", "q90"])
    predictions = strategy.predict(X_test, ["q10", "q50", "q90"])
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from loguru import logger

from .core import BaseStrategy, StrategyRegistry
from .utils import detect_outliers_dtw


@StrategyRegistry.register("arithmetic_mean")
class ArithmeticMeanStrategy(BaseStrategy):
    """
    Simple arithmetic mean ensemble strategy.

    This strategy calculates the unweighted average of all forecaster
    predictions for each quantile. All forecasters receive equal weight
    regardless of their historical performance.

    Optionally applies DTW-based outlier detection to remove anomalous
    forecast profiles before averaging.

    Use this as a baseline benchmark to compare against more sophisticated
    ensemble methods like weighted averaging.

    :param outlier_detection: Enable DTW outlier detection (default: True).
    :param outlier_alpha: MAD multiplier for outlier threshold (default: 20.0).
    :param min_forecasters_for_outlier_detection: Minimum forecasters
        required to run outlier detection (default: 4).

    Example::

        strategy = ArithmeticMeanStrategy(outlier_detection=True)
        strategy.fit(pd.DataFrame(), pd.DataFrame(), ["q10", "q50", "q90"])
        predictions = strategy.predict(X_test, ["q10", "q50", "q90"])
    """

    def __init__(
        self,
        outlier_detection: bool = True,
        outlier_alpha: float = 20.0,
        min_forecasters_for_outlier_detection: int = 4,
        **kwargs: Any,
    ):
        """
        Initialize the arithmetic mean strategy.

        :param outlier_detection: Enable outlier detection (default: True)
        :param outlier_alpha: MAD multiplier for outliers (default: 20.0)
        :param min_forecasters_for_outlier_detection: Min forecasters for
            outlier detection (default: 4)
        :param kwargs: Additional parameters passed to base class
        """
        super().__init__(
            outlier_detection=outlier_detection,
            outlier_alpha=outlier_alpha,
            min_forecasters_for_outlier_detection=min_forecasters_for_outlier_detection,
            **kwargs,
        )
        self._outlier_detection = outlier_detection
        self._outlier_alpha = outlier_alpha
        self._min_forecasters = min_forecasters_for_outlier_detection

    @property
    def name(self) -> str:
        """Return strategy name."""
        return "arithmetic_mean"

    def _do_fit(
        self,
        X_train: pd.DataFrame,
        y_train: pd.DataFrame,
        quantiles: list[str],
        **kwargs: Any,
    ) -> None:
        """
        Fit the arithmetic mean strategy.

        This strategy requires no training - all forecasters receive
        equal weight. This method only stores metadata.

        :param X_train: Historical forecaster predictions (unused)
        :param y_train: Historical actual values (unused)
        :param quantiles: List of quantile names
        :param kwargs: Additional parameters (unused)
        """
        self._add_metadata("outlier_detection", self._outlier_detection)
        self._add_metadata("outlier_alpha", self._outlier_alpha)

    def _do_predict(
        self,
        X_test: pd.DataFrame,
        quantiles: list[str],
    ) -> pd.DataFrame:
        """
        Generate arithmetic mean ensemble predictions.

        :param X_test: DataFrame with forecaster predictions for forecast period.
            Columns should be in format "{forecaster_id}_{quantile}".
        :param quantiles: List of quantile names to predict

        :return: DataFrame with columns [datetime, variable, value]
        """
        results = []

        for quantile in quantiles:
            # Extract columns for this quantile
            quantile_cols = self._get_quantile_columns(X_test, quantile)

            if not quantile_cols:
                # Try without suffix (for pre-filtered data)
                quantile_cols = list(X_test.columns)

            if not quantile_cols:
                logger.warning(f"No forecaster columns found for {quantile}")
                continue

            forecast_df = X_test[quantile_cols].copy()

            # Outlier detection
            if (
                self._outlier_detection
                and forecast_df.shape[1] >= self._min_forecasters
            ):
                outliers = detect_outliers_dtw(forecast_df, self._outlier_alpha)
                if outliers:
                    logger.info(
                        f"Outlier detection for {quantile}: "
                        f"removing {len(outliers)} forecasters"
                    )
                    forecast_df = forecast_df.drop(columns=outliers)
                    self._add_metadata(f"outliers_{quantile}", outliers)

            # Set equal weights for all remaining forecasters
            n_forecasters = forecast_df.shape[1]
            weight = 1.0 / n_forecasters if n_forecasters > 0 else 0.0
            weight_dict = {
                self._extract_forecaster_id(col): weight for col in forecast_df.columns
            }
            self._set_weights(quantile, weight_dict)

            # Calculate arithmetic mean
            mean_forecast = forecast_df.mean(axis=1)

            # Format output using base class helper (includes clipping)
            results.append(self._format_predictions(mean_forecast, quantile))

        if not results:
            return pd.DataFrame(columns=["datetime", "variable", "value"])

        return pd.concat(results, ignore_index=True)
