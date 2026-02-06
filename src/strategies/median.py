"""
Median ensemble strategy.

This is an example strategy using SimpleStrategy that demonstrates
how easy it is to create a new ensemble method.

Example usage::

    from src.strategies import StrategyRegistry

    strategy = StrategyRegistry.get("median")
    strategy.fit(X_train, y_train, ["q10", "q50", "q90"])
    predictions = strategy.predict(X_test, ["q10", "q50", "q90"])

To test with the community simulator::

    cd simulator/community
    python simulate.py run --dataset=example_elia --n_sessions=5
"""

from __future__ import annotations

import pandas as pd

from .core import SimpleStrategy, StrategyRegistry


@StrategyRegistry.register("median")
class MedianStrategy(SimpleStrategy):
    """
    Median ensemble strategy.

    Combines forecaster predictions using the median instead of mean.
    The median is more robust to outliers than the arithmetic mean,
    making this useful when some forecasters may have extreme predictions.

    All forecasters receive equal weight (1/n_forecasters).
    """

    @property
    def name(self) -> str:
        """Return strategy name."""
        return "median"

    def combine(
        self,
        forecasts: pd.DataFrame,
        **kwargs,
    ) -> pd.Series:
        """
        Combine forecasts using median.

        :param forecasts: DataFrame with one column per forecaster
        :param kwargs: Additional context (not used)
        :return: Series with median predictions
        """
        return forecasts.median(axis=1)
