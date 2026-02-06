"""
Forecast strategies module.

This module provides pluggable ensemble strategies for combining
forecaster predictions. Each strategy implements the ForecastStrategy
protocol and can be registered with the StrategyRegistry.

Available Strategies
--------------------
WeightedAverageStrategy
    Production ensemble using exponentially-weighted averaging based on
    recent skill scores. Default strategy.

ArithmeticMeanStrategy
    Simple unweighted average of all forecaster predictions. Useful as a
    benchmark baseline.

BestForecasterStrategy
    Selects the single best-performing forecaster per quantile. Useful to
    compare ensemble methods against individual forecasters.

MedianStrategy
    Median of forecaster predictions. Example using SimpleStrategy.

Registry
--------
StrategyRegistry
    Global registry for registering and retrieving strategies.

Base Classes
------------
BaseStrategy
    Abstract base class for implementing new strategies.

SimpleStrategy
    Simplified base for combine-only strategies.

Example usage::

    from src.strategies import (
        StrategyRegistry,
        WeightedAverageStrategy,
    )

    # Get the default production strategy
    strategy = StrategyRegistry.get("weighted_avg", beta=0.001)

    # Fit with historical data and scores
    strategy.fit(X_train, y_train, ["q10", "q50", "q90"], scores=assessment_report)

    # Generate predictions
    predictions = strategy.predict(X_test, ["q10", "q50", "q90"])

    # Get forecaster weights
    weights = strategy.get_weights()

Creating Custom Strategies
--------------------------

**SimpleStrategy (Recommended for most cases)**

For simple ensemble algorithms, use SimpleStrategy - it handles all boilerplate:

1. Inherit from SimpleStrategy
2. Implement name property
3. Implement combine() method
4. Register with @StrategyRegistry.register("name")

Example::

    from src.strategies import SimpleStrategy, StrategyRegistry

    @StrategyRegistry.register("my_ensemble")
    class MyEnsembleStrategy(SimpleStrategy):
        @property
        def name(self) -> str:
            return "my_ensemble"

        def combine(self, forecasts, **kwargs):
            # Your algorithm - just return a Series
            return forecasts.mean(axis=1)

The ``quantile`` parameter is optional. Include it if your algorithm needs it::

    def combine(self, forecasts, quantile, **kwargs):
        # Per-quantile logic (e.g., custom weights)
        self._set_weights(quantile, {"s1": 0.5, "s2": 0.5})
        return forecasts.mean(axis=1)

**BaseStrategy (Advanced - for ML-based ensembles)**

Use BaseStrategy when you need full control over training/prediction:

1. Inherit from BaseStrategy
2. Implement name property
3. Implement _do_fit and _do_predict methods
4. Register with @StrategyRegistry.register("name")

Example::

    from src.strategies import BaseStrategy, StrategyRegistry

    @StrategyRegistry.register("my_ml_ensemble")
    class MyMLEnsembleStrategy(BaseStrategy):
        @property
        def name(self) -> str:
            return "my_ml_ensemble"

        def _do_fit(self, X_train, y_train, quantiles, **kwargs):
            # Train your ML model
            pass

        def _do_predict(self, X_test, quantiles):
            # Generate predictions using your model
            return predictions_df
"""

from .core import BaseStrategy, SimpleStrategy, StrategyRegistry

# Import strategies to trigger registration
from .weighted_average import WeightedAverageStrategy
from .arithmetic_mean import ArithmeticMeanStrategy
from .best_forecaster import BestForecasterStrategy
from .median import MedianStrategy  # Example using SimpleStrategy

__all__ = [
    # Base classes
    "BaseStrategy",
    "SimpleStrategy",
    "StrategyRegistry",
    # Batch strategies
    "WeightedAverageStrategy",
    "ArithmeticMeanStrategy",
    "BestForecasterStrategy",
    "MedianStrategy",
]
