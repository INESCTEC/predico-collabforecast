"""
Forecast engine for orchestrating ensemble strategies.

The ForecastEngine is the core component that:
1. Manages strategy selection per resource
2. Runs one or more strategies for each forecast
3. Collects and returns results from all strategies

This module provides a clean interface for the forecasting pipeline,
decoupling strategy implementation from the market session logic.

Example usage::

    from forecast.src.market.engine import ForecastEngine
    from forecast.src.core.config import ForecastConfig

    config = ForecastConfig(
        default_strategy="weighted_avg",
        resource_strategies={"wind": ["weighted_avg", "stacked_lr"]}
    )

    engine = ForecastEngine(config)

    results = engine.forecast(
        resource_id="wind",
        X_train=train_features,
        y_train=train_targets,
        X_test=test_features,
        forecast_range=forecast_dates,
    )

    # results is a dict: {"weighted_avg": ForecastResult, "stacked_lr": ForecastResult}
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd
from loguru import logger

from ..core.config import ForecastConfig
from ..core.exceptions import (
    ForecastError,
    StrategyExecutionError,
    StrategyNotFoundError,
)
from ..core.interfaces import ForecastResult
from ..strategies import StrategyRegistry

if TYPE_CHECKING:
    from ..core.interfaces import ForecastStrategy


class ForecastEngine:
    """
    Core forecasting engine that orchestrates ensemble strategies.

    The ForecastEngine provides a unified interface for running forecasts
    using one or more strategies. It supports:

    - Per-resource strategy configuration
    - Running multiple strategies for comparison
    - Collecting results from all strategies

    :param config: ForecastConfig instance with engine settings

    Example::

        config = ForecastConfig(
            default_strategy="weighted_avg",
            resource_strategies={
                "wind_offshore": ["weighted_avg", "stacked_lr"],
                "solar": ["weighted_avg"],
            }
        )

        engine = ForecastEngine(config)

        # Run forecast for wind resource (uses both strategies)
        results = engine.forecast(
            resource_id="wind_offshore",
            X_train=train_data,
            y_train=actual_data,
            X_test=test_data,
            forecast_range=dates,
        )

        # Access results
        weighted_avg_result = results["weighted_avg"]
        stacked_lr_result = results["stacked_lr"]
    """

    def __init__(self, config: ForecastConfig | None = None):
        """
        Initialize the forecast engine.

        :param config: ForecastConfig instance. If None, uses default config.
        """
        self._config = config or ForecastConfig()
        self._results: dict[str, dict[str, ForecastResult]] = {}
        self._strategy_instances: dict[str, "ForecastStrategy"] = {}

    @property
    def config(self) -> ForecastConfig:
        """Return the engine configuration."""
        return self._config

    def forecast(
        self,
        resource_id: str,
        X_train: pd.DataFrame,
        y_train: pd.DataFrame,
        X_test: pd.DataFrame,
        forecast_range: pd.DatetimeIndex,
        strategies: list[str] | None = None,
        quantiles: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, ForecastResult]:
        """
        Run forecasting for a resource with one or more strategies.

        :param resource_id: Identifier for the resource being forecast
        :param X_train: Historical forecaster predictions (DataFrame)
        :param y_train: Historical actual values (DataFrame)
        :param X_test: Forecaster predictions for forecast period (DataFrame)
        :param forecast_range: DatetimeIndex of forecast timestamps
        :param strategies: List of strategy names to run. If None, uses
            strategies configured for this resource.
        :param quantiles: List of quantile names. If None, uses config default.
        :param kwargs: Additional parameters passed to strategies

        :return: Dict mapping strategy name to ForecastResult

        :raises StrategyNotFoundError: If a requested strategy is not registered
        :raises StrategyExecutionError: If strategy execution fails
        """
        # Get strategies to run
        if strategies is None:
            strategies = self._config.get_strategies_for_resource(resource_id)

        # Get quantiles
        if quantiles is None:
            quantiles = list(self._config.quantiles)

        logger.info(
            f"ForecastEngine: Running {len(strategies)} strategy(ies) "
            f"for resource '{resource_id}': {strategies}"
        )

        results: dict[str, ForecastResult] = {}

        for strategy_name in strategies:
            try:
                result = self._run_strategy(
                    strategy_name=strategy_name,
                    X_train=X_train,
                    y_train=y_train,
                    X_test=X_test,
                    quantiles=quantiles,
                    **kwargs,
                )
                results[strategy_name] = result
                logger.success(f"Strategy '{strategy_name}' completed successfully")

            except StrategyNotFoundError:
                raise
            except Exception as e:
                logger.error(f"Strategy '{strategy_name}' failed: {e}")
                raise StrategyExecutionError(
                    f"Strategy '{strategy_name}' failed: {e}",
                    {"strategy": strategy_name, "resource_id": resource_id},
                ) from e

        # Store results
        self._results[resource_id] = results

        return results

    def _run_strategy(
        self,
        strategy_name: str,
        X_train: pd.DataFrame,
        y_train: pd.DataFrame,
        X_test: pd.DataFrame,
        quantiles: list[str],
        **kwargs: Any,
    ) -> ForecastResult:
        """
        Run a single strategy and return results.

        :param strategy_name: Name of the strategy to run
        :param X_train: Training features
        :param y_train: Training targets
        :param X_test: Test features
        :param quantiles: Quantiles to predict
        :param kwargs: Additional strategy parameters

        :return: ForecastResult from the strategy
        """
        # Get or create strategy instance
        strategy = self._get_strategy(strategy_name)

        logger.debug(f"Running strategy '{strategy_name}'")

        # Fit strategy - strategies compute their own scores from X_train/y_train
        strategy.fit(X_train, y_train, quantiles, **kwargs)

        # Generate predictions
        predictions = strategy.predict(X_test, quantiles)

        # Return result
        return ForecastResult(
            strategy_name=strategy.name,
            predictions=predictions,
            weights=strategy.get_weights(),
            metadata=getattr(strategy, "_metadata", None),
        )

    def _get_strategy(self, name: str) -> "ForecastStrategy":
        """
        Get a strategy instance, creating if necessary.

        :param name: Strategy name

        :return: Strategy instance
        """
        if name not in self._strategy_instances:
            # Get strategy config params
            strategy_params = self._get_strategy_params(name)
            self._strategy_instances[name] = StrategyRegistry.get(
                name, **strategy_params
            )

        return self._strategy_instances[name]

    def _get_strategy_params(self, strategy_name: str) -> dict[str, Any]:
        """
        Get configuration parameters for a strategy.

        :param strategy_name: Strategy name

        :return: Dict of strategy parameters
        """
        params: dict[str, Any] = {}

        if strategy_name == "weighted_avg":
            params["beta"] = self._config.weighting.beta

        return params

    def get_results(self, resource_id: str) -> dict[str, ForecastResult]:
        """
        Get stored results for a resource.

        :param resource_id: Resource identifier

        :return: Dict mapping strategy name to ForecastResult

        :raises ForecastError: If no results exist for the resource
        """
        if resource_id not in self._results:
            raise ForecastError(
                f"No results found for resource '{resource_id}'",
                {"resource_id": resource_id, "available": list(self._results.keys())},
            )
        return self._results[resource_id]

    def get_comparison(self, resource_id: str) -> pd.DataFrame:
        """
        Compare results from multiple strategies for a resource.

        Creates a DataFrame with strategy predictions side-by-side
        for easy comparison.

        :param resource_id: Resource identifier

        :return: DataFrame with columns for each strategy's predictions

        :raises ForecastError: If no results exist for the resource
        """
        results = self.get_results(resource_id)

        if len(results) < 2:
            logger.warning(
                f"Comparison requested but only {len(results)} strategy result(s) "
                f"available for '{resource_id}'"
            )

        comparison_data = []

        for strategy_name, result in results.items():
            df = result.predictions.copy()
            df = df.rename(columns={"value": f"value_{strategy_name}"})
            comparison_data.append(df)

        if not comparison_data:
            return pd.DataFrame()

        # Merge all results
        merged = comparison_data[0]
        for df in comparison_data[1:]:
            merged = merged.merge(df, on=["datetime", "variable"], how="outer")

        return merged

    def clear_results(self) -> None:
        """Clear all stored results."""
        self._results.clear()

    def clear_strategy_cache(self) -> None:
        """Clear cached strategy instances."""
        self._strategy_instances.clear()
