"""
Base class for forecast strategies.

This module provides the BaseStrategy abstract class that implements
common functionality for all forecast strategies. Concrete strategies
should inherit from this class and implement the abstract methods.

Example usage::

    from src.strategies import BaseStrategy, StrategyRegistry

    @StrategyRegistry.register("my_strategy")
    class MyStrategy(BaseStrategy):
        @property
        def name(self) -> str:
            return "my_strategy"

        def _do_fit(self, X_train, y_train, quantiles, **kwargs):
            # Custom fitting logic
            pass

        def _do_predict(self, X_test, quantiles):
            # Custom prediction logic
            return predictions_df
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from ...core.exceptions import ModelNotFittedError
from ...core.interfaces import ForecastResult


class BaseStrategy(ABC):
    """
    Abstract base class for forecast strategies.

    This class provides common functionality for all strategies including:
    - Fitted state tracking
    - Weight storage and retrieval
    - Common validation
    - Result formatting

    Subclasses must implement:
    - :attr:`name` property
    - :meth:`_do_fit` method
    - :meth:`_do_predict` method

    :param config: Optional configuration dict for strategy-specific settings
    """

    def __init__(self, clip_lower: float | None = 0.0, **kwargs: Any):
        """
        Initialize the base strategy.

        :param clip_lower: Minimum value to clip predictions. Use None to
            disable clipping (for series that can have negative values).
            Default is 0.0 for energy forecasts.
        :param kwargs: Strategy-specific configuration parameters
        """
        self._fitted = False
        self._weights: dict[str, dict[str, float]] = {}
        self._config = kwargs
        self._metadata: dict[str, Any] = {}
        self._clip_lower = clip_lower

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique identifier for this strategy.

        :return: Strategy name string
        """
        ...

    @property
    def is_fitted(self) -> bool:
        """
        Check if the strategy has been fitted.

        :return: True if fit() has been called successfully
        """
        return self._fitted

    def fit(
        self,
        X_train: pd.DataFrame,
        y_train: pd.DataFrame,
        quantiles: list[str],
        **kwargs: Any,
    ) -> "BaseStrategy":
        """
        Train the ensemble model on historical data.

        This method handles common validation and state management,
        then delegates to :meth:`_do_fit` for strategy-specific logic.

        :param X_train: DataFrame with forecaster predictions as columns.
            Index should be DatetimeIndex, columns are forecaster IDs.
        :param y_train: DataFrame with actual measured values.
            Index should match X_train, single column with target values.
        :param quantiles: List of quantile names to fit (e.g., ["q10", "q50", "q90"]).
        :param kwargs: Strategy-specific parameters.

        :return: self for method chaining
        """
        # Reset state
        self._weights = {}
        self._metadata = {}

        # Delegate to subclass implementation
        self._do_fit(X_train, y_train, quantiles, **kwargs)

        self._fitted = True
        return self

    @abstractmethod
    def _do_fit(
        self,
        X_train: pd.DataFrame,
        y_train: pd.DataFrame,
        quantiles: list[str],
        **kwargs: Any,
    ) -> None:
        """
        Strategy-specific fitting logic.

        Subclasses must implement this method with their specific
        training algorithm.

        :param X_train: DataFrame with forecaster predictions
        :param y_train: DataFrame with actual values
        :param quantiles: List of quantile names
        :param kwargs: Additional parameters
        """
        ...

    def predict(
        self,
        X_test: pd.DataFrame,
        quantiles: list[str],
    ) -> pd.DataFrame:
        """
        Generate ensemble forecasts for the given input.

        This method handles fitted state validation, then delegates
        to :meth:`_do_predict` for strategy-specific logic.

        :param X_test: DataFrame with forecaster predictions for forecast period.
        :param quantiles: List of quantile names to predict.

        :return: DataFrame with columns [datetime, variable, value]

        :raises ModelNotFittedError: If predict is called before fit
        """
        if not self._fitted:
            raise ModelNotFittedError(
                f"Strategy '{self.name}' must be fitted before calling predict().",
                {"strategy": self.name},
            )

        return self._do_predict(X_test, quantiles)

    @abstractmethod
    def _do_predict(
        self,
        X_test: pd.DataFrame,
        quantiles: list[str],
    ) -> pd.DataFrame:
        """
        Strategy-specific prediction logic.

        Subclasses must implement this method with their specific
        prediction algorithm.

        :param X_test: DataFrame with forecaster predictions
        :param quantiles: List of quantile names

        :return: DataFrame with columns [datetime, variable, value]
        """
        ...

    def get_weights(self) -> dict[str, dict[str, float]]:
        """
        Return forecaster contribution weights per quantile.

        :return: Nested dict mapping {quantile: {user_id: weight}}
        """
        return self._weights.copy()

    def get_result(self, predictions: pd.DataFrame) -> ForecastResult:
        """
        Create a ForecastResult from predictions.

        :param predictions: DataFrame with columns [datetime, variable, value]

        :return: ForecastResult instance
        """
        return ForecastResult(
            strategy_name=self.name,
            predictions=predictions,
            weights=self.get_weights(),
            metadata=self._metadata.copy(),
        )

    def _set_weights(self, quantile: str, weights: dict[str, float]) -> None:
        """
        Store weights for a specific quantile.

        :param quantile: Quantile name (e.g., "q50")
        :param weights: Dict mapping forecaster_id to weight
        """
        self._weights[quantile] = weights

    def _add_metadata(self, key: str, value: Any) -> None:
        """
        Add metadata about the fitting/prediction process.

        :param key: Metadata key
        :param value: Metadata value
        """
        self._metadata[key] = value

    # -------------------------------------------------------------------------
    # Helper methods for common operations
    # -------------------------------------------------------------------------

    def _get_quantile_columns(self, X: pd.DataFrame, quantile: str) -> list[str]:
        """
        Get column names that match a specific quantile.

        :param X: DataFrame with forecaster predictions
        :param quantile: Quantile name (e.g., "q50")
        :return: List of column names ending with _{quantile}
        """
        return [c for c in X.columns if c.endswith(f"_{quantile}")]

    def _extract_forecaster_id(self, column_name: str) -> str:
        """
        Extract forecaster ID from column name.

        Handles formats like:
        - "s1_q50" -> "s1"
        - "forecaster1_q50_resource1" -> "forecaster1_q50"

        :param column_name: Column name with forecaster and quantile
        :return: Forecaster identifier
        """
        parts = column_name.rsplit("_", 1)
        return parts[0] if len(parts) > 1 else column_name

    def _format_predictions(
        self,
        values: pd.Series,
        quantile: str,
    ) -> pd.DataFrame:
        """
        Format prediction values into standard output DataFrame.

        Uses the instance's `clip_lower` setting. If `clip_lower` is None,
        no clipping is applied (for series that can have negative values).

        :param values: Series with predictions (index should be datetime)
        :param quantile: Quantile name (e.g., "q50")
        :return: DataFrame with columns [datetime, variable, value]
        """
        output_values = values
        if self._clip_lower is not None:
            output_values = values.clip(lower=self._clip_lower)

        return pd.DataFrame(
            {
                "datetime": output_values.index,
                "variable": quantile,
                "value": output_values.values,
            }
        )

    def _set_equal_weights(self, quantile: str, columns: list[str]) -> None:
        """
        Set equal weights for all forecasters in the given columns.

        :param quantile: Quantile name (e.g., "q50")
        :param columns: List of column names to extract forecaster IDs from
        """
        n = len(columns)
        if n == 0:
            return
        weights = {self._extract_forecaster_id(c): 1.0 / n for c in columns}
        self._set_weights(quantile, weights)
