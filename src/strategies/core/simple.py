"""
Simplified base class for ensemble strategies.

This module provides SimpleStrategy, a streamlined base class that handles
all boilerplate code, letting contributors focus on their ensemble algorithm.

Example usage::

    from src.strategies import SimpleStrategy, StrategyRegistry

    @StrategyRegistry.register("my_ensemble")
    class MyEnsembleStrategy(SimpleStrategy):
        @property
        def name(self) -> str:
            return "my_ensemble"

        def combine(self, forecasts, **kwargs):
            # Your algorithm here - just return a Series
            return forecasts.mean(axis=1)

The ``quantile`` parameter is optional. Include it explicitly if needed::

    def combine(self, forecasts, quantile, **kwargs):
        # Per-quantile logic (e.g., setting weights)
        self._set_weights(quantile, {"user1": 0.5, "user2": 0.5})
        return forecasts.mean(axis=1)
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

import pandas as pd
from loguru import logger

from .base import BaseStrategy


class SimpleStrategy(BaseStrategy):
    """
    Simplified base class for ensemble strategies.

    This class handles all the boilerplate:
    - Quantile iteration
    - Column extraction by quantile suffix
    - Output DataFrame formatting
    - Weight management (defaults to equal weights)

    Subclasses only need to implement:
    - ``name`` property - unique identifier
    - ``combine()`` method - the core ensemble algorithm

    Example::

        @StrategyRegistry.register("my_median")
        class MedianStrategy(SimpleStrategy):
            @property
            def name(self) -> str:
                return "my_median"

            def combine(self, forecasts, **kwargs):
                return forecasts.median(axis=1)

    For strategies that need the quantile or custom weights, include
    ``quantile`` as an explicit parameter::

        def combine(self, forecasts, quantile, **kwargs):
            # Custom weight calculation
            weights = calculate_my_weights(forecasts)
            self._set_weights(quantile, weights)
            return (forecasts * weights).sum(axis=1)
    """

    @abstractmethod
    def combine(
        self,
        forecasts: pd.DataFrame,
        **kwargs: Any,
    ) -> pd.Series:
        """
        Combine forecaster predictions into an ensemble forecast.

        This is the only method you need to implement. The input DataFrame
        contains one column per forecaster with their predictions. Return
        a Series with your ensemble predictions.

        :param forecasts: DataFrame with forecaster predictions.
            - Index: DatetimeIndex with forecast timestamps
            - Columns: Forecaster identifiers (e.g., "s1_q50", "s2_q50")
            - Values: Prediction values for each forecaster
        :param kwargs: Additional context passed from fit():
            - ``quantile``: Current quantile being processed (e.g., "q50").
              Include this as an explicit parameter if your algorithm needs it.
            - ``scores``: Dict with historical skill scores per forecaster
            - Any other kwargs passed to fit()
        :return: Series with ensemble predictions, same index as input

        Example implementations::

            # Simple mean (quantile not needed)
            def combine(self, forecasts, **kwargs):
                return forecasts.mean(axis=1)

            # With explicit quantile parameter (for per-quantile logic)
            def combine(self, forecasts, quantile, **kwargs):
                self._set_weights(quantile, {"user1": 0.5, "user2": 0.5})
                return forecasts.mean(axis=1)

            # Weighted by inverse score
            def combine(self, forecasts, quantile, **kwargs):
                scores = kwargs.get("scores", {}).get(quantile, {})
                if not scores:
                    return forecasts.mean(axis=1)
                weights = {k: 1/v for k, v in scores.items() if v > 0}
                # ... apply weights
        """
        ...

    def _do_fit(
        self,
        X_train: pd.DataFrame,
        y_train: pd.DataFrame,
        quantiles: list[str],
        **kwargs: Any,
    ) -> None:
        """
        Store fit kwargs for use in predict.

        Override this method if your strategy needs custom training logic.
        The default implementation stores kwargs for access in combine().

        :param X_train: Historical forecaster predictions (optional use)
        :param y_train: Historical actual values (optional use)
        :param quantiles: List of quantiles
        :param kwargs: Additional parameters (e.g., scores)
        """
        self._fit_kwargs = kwargs
        self._add_metadata("strategy_type", "simple")
        logger.debug(f"{self.name} fitted (SimpleStrategy)")

    def _do_predict(
        self,
        X_test: pd.DataFrame,
        quantiles: list[str],
    ) -> pd.DataFrame:
        """
        Generate ensemble predictions for all quantiles.

        This method handles the iteration over quantiles, column extraction,
        calling your combine() method, and formatting the output.

        :param X_test: DataFrame with forecaster predictions
        :param quantiles: List of quantiles to predict
        :return: DataFrame with columns [datetime, variable, value]
        """
        results = []

        for quantile in quantiles:
            # Extract columns for this quantile
            cols = self._get_quantile_columns(X_test, quantile)

            if not cols:
                logger.warning(f"No forecaster columns found for {quantile}")
                continue

            forecasts = X_test[cols]

            # Call user's combine method (quantile as keyword so it's optional)
            ensemble = self.combine(
                forecasts,
                quantile=quantile,
                **getattr(self, "_fit_kwargs", {}),
            )

            # Set equal weights by default if user didn't set custom weights
            if quantile not in self._weights:
                self._set_equal_weights(quantile, cols)

            # Format output
            results.append(self._format_predictions(ensemble, quantile))

        if not results:
            logger.warning("No predictions generated - no valid quantile columns found")
            return pd.DataFrame(columns=["datetime", "variable", "value"])

        return pd.concat(results, ignore_index=True)
