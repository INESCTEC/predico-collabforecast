"""
Protocol definitions for the forecast engine plugin architecture.

This module defines the core interfaces that enable extensibility:

- ForecastStrategy: Interface for ensemble forecasting strategies
- FeatureTransformer: Interface for feature engineering transformers
- Scorer: Interface for forecast evaluation metrics

Contributors can implement these protocols to add custom functionality
without modifying core code.

Example usage::

    from src.core.interfaces import ForecastStrategy
    from src.strategies.registry import StrategyRegistry

    @StrategyRegistry.register("my_strategy")
    class MyStrategy:
        '''Custom ensemble strategy.'''

        @property
        def name(self) -> str:
            return "my_strategy"

        def fit(self, X_train, y_train, quantiles, **kwargs):
            # Training logic here
            return self

        def predict(self, X_test, quantiles):
            # Prediction logic here
            return predictions_df

        def get_weights(self):
            return {"q50": {"user_1": 0.5, "user_2": 0.5}}
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    import pandas as pd


# =============================================================================
# Forecast Result Data Class
# =============================================================================


@dataclass
class ForecastResult:
    """
    Container for forecast strategy output.

    :param strategy_name: Name of the strategy that produced this result
    :param predictions: DataFrame with columns [datetime, variable, value]
    :param weights: Nested dict mapping quantile -> user_id -> weight
    :param metadata: Optional dict with additional strategy-specific data
    """

    strategy_name: str
    predictions: "pd.DataFrame"
    weights: dict[str, dict[str, float]]
    metadata: dict[str, Any] | None = None


# =============================================================================
# Forecast Strategy Protocol
# =============================================================================


@runtime_checkable
class ForecastStrategy(Protocol):
    """
    Interface for ensemble forecasting strategies.

    A ForecastStrategy combines predictions from multiple forecasters into
    a single ensemble forecast. Implementations can use simple averaging,
    weighted combinations, or machine learning approaches.

    Contributors implement this protocol to add new ensemble methods.
    The strategy is responsible for:

    1. Learning from historical data (fit)
    2. Generating ensemble predictions (predict)
    3. Reporting forecaster contribution weights (get_weights)

    Example implementation::

        class WeightedAverageStrategy:
            def __init__(self, beta: float = 0.001):
                self._beta = beta
                self._weights = {}

            @property
            def name(self) -> str:
                return "weighted_avg"

            def fit(self, X_train, y_train, quantiles, **kwargs):
                scores = kwargs.get("recent_scores", {})
                # Calculate weights from scores
                return self

            def predict(self, X_test, quantiles):
                # Apply weighted average
                return predictions_df

            def get_weights(self):
                return self._weights
    """

    @property
    def name(self) -> str:
        """
        Unique identifier for this strategy.

        Used for registration and selection. Should be a lowercase
        string with underscores (e.g., "weighted_avg", "stacked_lr").

        :return: Strategy name string
        """
        ...

    def fit(
        self,
        X_train: "pd.DataFrame",
        y_train: "pd.DataFrame",
        quantiles: list[str],
        **kwargs: Any,
    ) -> "ForecastStrategy":
        """
        Train the ensemble model on historical data.

        This method learns how to combine forecaster predictions based on
        historical performance. The fitted state should be stored internally.

        :param X_train: DataFrame with forecaster predictions as columns.
            Index should be DatetimeIndex, columns are forecaster IDs.
        :param y_train: DataFrame with actual measured values.
            Index should match X_train, single column with target values.
        :param quantiles: List of quantile names to fit (e.g., ["q10", "q50", "q90"]).
        :param kwargs: Strategy-specific parameters. Common kwargs:
            - recent_scores: dict mapping user_id to recent skill scores
            - config: ForecastConfig instance

        :return: self for method chaining

        :raises ModelFitException: If fitting fails
        """
        ...

    def predict(
        self,
        X_test: "pd.DataFrame",
        quantiles: list[str],
    ) -> "pd.DataFrame":
        """
        Generate ensemble forecasts for the given input.

        Combines forecaster predictions using the learned combination weights
        or model to produce ensemble forecasts.

        :param X_test: DataFrame with forecaster predictions for forecast period.
            Index should be DatetimeIndex, columns are forecaster IDs.
        :param quantiles: List of quantile names to predict.

        :return: DataFrame with columns [datetime, variable, value] where:
            - datetime: Forecast timestamp
            - variable: Quantile name (e.g., "q10", "q50", "q90")
            - value: Forecast value

        :raises ModelNotFittedError: If predict is called before fit
        :raises ModelForecastException: If prediction fails
        """
        ...

    def get_weights(self) -> dict[str, dict[str, float]]:
        """
        Return forecaster contribution weights per quantile.

        Weights indicate how much each forecaster contributed to the
        ensemble forecast. Useful for:
        - Understanding ensemble composition
        - Payment distribution
        - Forecaster performance analysis

        :return: Nested dict mapping {quantile: {user_id: weight}}.
            Weights should sum to 1.0 for each quantile.
            Example: {"q50": {"user_123": 0.6, "user_456": 0.4}}
        """
        ...


# =============================================================================
# Online Forecast Strategy Protocol
# =============================================================================


@runtime_checkable
class OnlineForecastStrategy(ForecastStrategy, Protocol):
    """
    Extended interface for online learning strategies.

    Online strategies support incremental updates after each session,
    allowing weights to adapt over time without full retraining.

    In addition to the base ForecastStrategy methods, online strategies
    provide:

    - partial_fit(): Incremental weight updates based on new observations
    - get_weight_history(): Track how weights evolved over time

    Example implementation::

        class OnlineWeightedStrategy:
            def partial_fit(self, X_new, y_true, quantiles, **kwargs):
                # Update weights based on forecast errors
                for q in quantiles:
                    errors = self._compute_errors(X_new, y_true, q)
                    self._update_weights(q, errors)
                return self

            def get_weight_history(self):
                return self._weight_snapshots
    """

    def partial_fit(
        self,
        X_new: "pd.DataFrame",
        y_true: "pd.DataFrame",
        quantiles: list[str],
        **kwargs: Any,
    ) -> "OnlineForecastStrategy":
        """
        Incrementally update model with new observation(s).

        Unlike fit(), which trains on the full historical dataset,
        partial_fit updates the model with a single session's data.
        This enables efficient adaptation without full retraining.

        :param X_new: DataFrame with forecaster predictions for new session.
            Index should be DatetimeIndex for the session period.
        :param y_true: DataFrame with actual measured values for the session.
            Index should match X_new.
        :param quantiles: List of quantile names to update.
        :param kwargs: Strategy-specific parameters. Common kwargs:
            - session_date: datetime of the session
            - session_id: identifier for the session

        :return: self for method chaining
        """
        ...

    def get_weight_history(self) -> list[dict[str, dict[str, float]]]:
        """
        Return history of weight snapshots over time.

        Each entry contains the weights after a partial_fit call,
        enabling analysis of weight evolution and stability.

        :return: List of weight dicts, one per partial_fit call.
            Each dict has format {quantile: {user_id: weight}}.
        """
        ...


# =============================================================================
# Feature Transformer Protocol
# =============================================================================


@runtime_checkable
class FeatureTransformer(Protocol):
    """
    Interface for feature engineering transformers.

    A FeatureTransformer creates derived features from raw forecaster
    predictions. Transformers can be composed into pipelines for
    complex feature engineering workflows.

    Common transformers include:
    - Lag features (previous timestep values)
    - Rolling statistics (mean, std over windows)
    - Diversity features (std, var across forecasters)
    - Polynomial features (squared, cubic terms)

    Example implementation::

        class LagTransformer:
            def __init__(self, max_lags: int = 2):
                self._max_lags = max_lags
                self._feature_names = []

            @property
            def name(self) -> str:
                return "lag_transformer"

            def fit(self, X):
                self._feature_names = [
                    f"{col}_lag{i}"
                    for col in X.columns
                    for i in range(1, self._max_lags + 1)
                ]
                return self

            def transform(self, X):
                result = X.copy()
                for col in X.columns:
                    for i in range(1, self._max_lags + 1):
                        result[f"{col}_lag{i}"] = X[col].shift(i)
                return result

            def fit_transform(self, X):
                return self.fit(X).transform(X)

            def get_feature_names(self):
                return self._feature_names
    """

    @property
    def name(self) -> str:
        """
        Unique identifier for this transformer.

        :return: Transformer name string
        """
        ...

    def fit(self, X: "pd.DataFrame") -> "FeatureTransformer":
        """
        Fit the transformer to the input data.

        Learn any parameters needed for transformation (e.g., scaling
        parameters, column names for derived features).

        :param X: Input DataFrame with raw features

        :return: self for method chaining
        """
        ...

    def transform(self, X: "pd.DataFrame") -> "pd.DataFrame":
        """
        Apply the transformation to input data.

        :param X: Input DataFrame with raw features

        :return: Transformed DataFrame with derived features

        :raises FeatureTransformError: If transformation fails
        """
        ...

    def fit_transform(self, X: "pd.DataFrame") -> "pd.DataFrame":
        """
        Fit and transform in a single step.

        Convenience method equivalent to fit(X).transform(X).

        :param X: Input DataFrame with raw features

        :return: Transformed DataFrame with derived features
        """
        ...

    def get_feature_names(self) -> list[str]:
        """
        Return names of features produced by this transformer.

        :return: List of feature name strings
        """
        ...


# =============================================================================
# Scorer Protocol
# =============================================================================


@runtime_checkable
class Scorer(Protocol):
    """
    Interface for forecast evaluation metrics.

    A Scorer computes a metric comparing forecasted values to actual
    observations. Scorers support both deterministic metrics (RMSE, MAE)
    and probabilistic metrics (Pinball loss, Winkler score).

    Example implementation::

        class RMSEScorer:
            @property
            def name(self) -> str:
                return "rmse"

            @property
            def higher_is_better(self) -> bool:
                return False  # Lower RMSE is better

            def score(self, y_true, y_pred, **kwargs):
                return np.sqrt(np.mean((y_true - y_pred) ** 2))
    """

    @property
    def name(self) -> str:
        """
        Unique identifier for this scorer.

        :return: Scorer name string (e.g., "rmse", "pinball", "winkler")
        """
        ...

    @property
    def higher_is_better(self) -> bool:
        """
        Whether higher scores indicate better forecasts.

        :return: True if higher is better (e.g., R2), False if lower is better (e.g., RMSE)
        """
        ...

    def score(
        self,
        y_true: "pd.DataFrame | pd.Series",
        y_pred: "pd.DataFrame | pd.Series",
        **kwargs: Any,
    ) -> float:
        """
        Calculate the score for predictions against actual values.

        :param y_true: Actual observed values
        :param y_pred: Predicted values
        :param kwargs: Scorer-specific parameters. Common kwargs:
            - quantile: float, for quantile-based metrics (e.g., pinball loss)
            - alpha: float, confidence level for interval metrics

        :return: Score value as a float

        :raises ScoringCalculationError: If score calculation fails
        """
        ...
