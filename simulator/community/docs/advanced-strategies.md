# Advanced Strategy Development

This guide covers advanced topics for building sophisticated ensemble strategies. Use these techniques when SimpleStrategy isn't enough - for example, when you need to train ML models or weight forecasters by their historical performance.

For basic strategy creation, see [Strategy Guide](strategy-guide.md).

---

## Table of Contents

1. [BaseStrategy Overview](#basestrategy-overview) - Full control over fit/predict cycle
2. [Using Historical Scores](#using-historical-scores) - Weight forecasters by past performance
3. [ML-Based Strategies](#ml-based-strategies) - Train models to learn optimal combinations
4. [Helper Methods Reference](#helper-methods-reference) - Utility functions available in BaseStrategy
5. [Writing Tests](#writing-tests) - Ensure your strategy works correctly
6. [Debugging Strategies](#debugging-strategies) - Troubleshoot common issues

---

## BaseStrategy Overview

Use `BaseStrategy` when you need control over the training phase. Unlike SimpleStrategy, BaseStrategy splits the process into two phases:

1. **fit()**: Train on historical data (compute weights, fit ML models)
2. **predict()**: Generate forecasts using what you learned

### When to Use BaseStrategy

Choose BaseStrategy over SimpleStrategy when:

- You need to compute skill scores from historical performance
- You want to train ML models (regression, neural networks)
- You need to store state between fit() and predict()
- Your combination logic requires access to training targets

### Required Methods

Implement `_do_fit()` and `_do_predict()`:

```python
from src.strategies import BaseStrategy, StrategyRegistry
import pandas as pd

@StrategyRegistry.register("my_advanced")
class MyAdvancedStrategy(BaseStrategy):

    @property
    def name(self) -> str:
        return "my_advanced"

    def _do_fit(self, X_train, y_train, quantiles, **kwargs):
        """
        Train on historical data. Store results as instance attributes.

        Args:
            X_train: Historical forecaster predictions (DataFrame)
            y_train: Historical observations (DataFrame). By convention,
                     uses the 'target' column, but falls back to the first
                     column if 'target' is not present.
            quantiles: List of quantiles ["q10", "q50", "q90"]
            kwargs: Additional parameters
        """
        # Example: compute and store something from training data
        self._learned_params = self._compute_something(X_train, y_train)

    def _do_predict(self, X_test, quantiles):
        """
        Generate ensemble predictions using learned parameters.

        Args:
            X_test: Forecaster predictions for the forecast period
            quantiles: List of quantiles to predict

        Returns:
            DataFrame with columns [datetime, variable, value]
        """
        results = []

        for quantile in quantiles:
            cols = self._get_quantile_columns(X_test, quantile)
            if not cols:
                continue

            forecasts = X_test[cols]

            # Apply your combination logic
            ensemble_values = self._combine_with_params(forecasts, self._learned_params)

            # Set weights and format output
            self._set_equal_weights(quantile, cols)
            results.append(self._format_predictions(ensemble_values, quantile))

        return pd.concat(results, ignore_index=True)
```

### Constructor Parameters

BaseStrategy accepts these constructor parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `clip_lower` | `float \| None` | `0.0` | Minimum value to clip predictions. Set to `None` to disable clipping (for series that can have negative values). Default is `0.0` for energy forecasts. |
| `**kwargs` | `Any` | — | Strategy-specific configuration, stored in `self._config` |

```python
# Example: disable clipping for temperature forecasts
class TempEnsemble(BaseStrategy):
    def __init__(self):
        super().__init__(clip_lower=None)  # Allow negative values
```

> [!NOTE]
> Constructor parameters cannot be passed from the CLI. To customize defaults, create a subclass with the desired values hardcoded in its `__init__` method.

### Output Format

> [!IMPORTANT]
> The `_do_predict()` method must return a DataFrame with exactly these columns. Incorrect formats will cause runtime errors.

| Column | Type | Description |
|--------|------|-------------|
| `datetime` | datetime | Forecast timestamp |
| `variable` | str | Quantile name (q10, q50, q90) |
| `value` | float | Predicted value (non-negative when `clip_lower=0.0`, the default) |

Use `_format_predictions()` to ensure correct format:

```python
ensemble_values = pd.Series([100, 110, 105], index=dates)
result_df = self._format_predictions(ensemble_values, "q50")
# Returns DataFrame with [datetime, variable, value] columns
```

---

## Using Historical Scores

Weight forecasters by their recent performance. Better forecasters (lower error scores) get higher weights. This is how the production `weighted_average` strategy works.

### Computing Skill Scores

Use `compute_scores()` to calculate forecaster performance from training data:

```python
from src.strategies import BaseStrategy, StrategyRegistry
from src.assessment.score_calculator import compute_scores
import numpy as np

@StrategyRegistry.register("weighted_by_score")
class WeightedByScoreStrategy(BaseStrategy):
    """Weight forecasters by their recent skill scores."""

    def __init__(self, n_score_days: int = 6, beta: float = 0.001):
        super().__init__(n_score_days=n_score_days)
        self._n_score_days = n_score_days  # How many days of history to use
        self._beta = beta  # Controls weight sensitivity (higher = more extreme weights)

    @property
    def name(self) -> str:
        return "weighted_by_score"

    def _do_fit(self, X_train, y_train, quantiles, **kwargs):
        # Compute skill scores from training data
        # Returns: {quantile: {column_name: score_value}}
        # Note: keys are full column names (e.g., "user1_q50"), not forecaster IDs
        scores = compute_scores(
            X_train, y_train, quantiles,
            n_days=self._n_score_days
        )

        # Lower scores = better performance (RMSE for q50, pinball for q10/q90)
        # Convert to weights using exponential transformation
        for quantile in quantiles:
            quantile_scores = scores.get(quantile, {})
            if not quantile_scores:
                continue

            # Better forecasters (lower scores) get higher weights
            weights = {}
            for col, score in quantile_scores.items():
                # Extract forecaster ID from column name (e.g., "user1_q50" -> "user1")
                user = self._extract_forecaster_id(col)
                weights[user] = np.exp(-self._beta * score)

            # Normalize so weights sum to 1
            total = sum(weights.values())
            weights = {k: v / total for k, v in weights.items()}
            self._set_weights(quantile, weights)

    def _do_predict(self, X_test, quantiles):
        results = []

        for quantile in quantiles:
            cols = self._get_quantile_columns(X_test, quantile)
            if not cols:
                continue

            forecasts = X_test[cols]
            weights = self._weights.get(quantile, {})

            # Apply weighted combination
            ensemble = pd.Series(0.0, index=forecasts.index)
            for col in cols:
                forecaster_id = self._extract_forecaster_id(col)
                weight = weights.get(forecaster_id, 0)
                ensemble += forecasts[col] * weight

            results.append(self._format_predictions(ensemble, quantile))

        return pd.concat(results, ignore_index=True)
```

### Understanding the Beta Parameter

> [!TIP]
> Start with the default `beta=0.001` and adjust based on results. Lower values give more equal weights; higher values favor the best forecasters more aggressively.

The `beta` parameter controls how aggressively to favor better forecasters:

| Beta | Effect |
|------|--------|
| 0.0001 | Nearly equal weights (small differences) |
| 0.001 | Moderate differentiation (default) |
| 0.01 | Strong differentiation (best forecasters dominate) |

See `WeightedAverageStrategy` in `src/strategies/weighted_average.py` for a complete production example with outlier detection. For details on how scores are computed, see [Evaluation Metrics](evaluation-metrics.md).

---

## ML-Based Strategies

Train machine learning models to learn optimal forecaster weights from data.

### Ridge Regression Example

Use Ridge regression to learn weights that minimize prediction error:

```python
from src.strategies import BaseStrategy, StrategyRegistry
from sklearn.linear_model import Ridge
import pandas as pd
import numpy as np

@StrategyRegistry.register("ridge_ensemble")
class RidgeEnsembleStrategy(BaseStrategy):
    """Learn optimal weights using Ridge regression."""

    def __init__(self, alpha: float = 1.0):
        super().__init__(alpha=alpha)
        self._alpha = alpha  # Regularization strength
        self._models = {}    # One model per quantile

    @property
    def name(self) -> str:
        return "ridge_ensemble"

    def _do_fit(self, X_train, y_train, quantiles, **kwargs):
        for quantile in quantiles:
            cols = self._get_quantile_columns(X_train, quantile)
            if not cols:
                continue

            # Prepare training data
            X = X_train[cols].values
            y = y_train["target"].values

            # Fit Ridge regression
            model = Ridge(alpha=self._alpha)
            model.fit(X, y)
            self._models[quantile] = model

            # Extract learned weights (regression coefficients)
            weights = {}
            for col, coef in zip(cols, model.coef_):
                forecaster_id = self._extract_forecaster_id(col)
                weights[forecaster_id] = max(0, coef)  # Keep non-negative

            # Normalize
            total = sum(weights.values()) or 1
            weights = {k: v / total for k, v in weights.items()}
            self._set_weights(quantile, weights)

    def _do_predict(self, X_test, quantiles):
        results = []

        for quantile in quantiles:
            cols = self._get_quantile_columns(X_test, quantile)
            if not cols or quantile not in self._models:
                continue

            # Use trained model to predict
            X = X_test[cols].values
            predictions = self._models[quantile].predict(X)

            # Ensure non-negative (power can't be negative)
            # WARNING: Always clip to zero - negative power predictions are invalid
            predictions = np.maximum(predictions, 0)
            ensemble = pd.Series(predictions, index=X_test.index)

            results.append(self._format_predictions(ensemble, quantile))

        return pd.concat(results, ignore_index=True)
```

### Other ML Approaches

You can use any scikit-learn model or custom implementation:

- **Gradient Boosting**: Better for non-linear relationships
- **Neural Networks**: For complex patterns (requires more data)
- **Quantile Regression**: Native support for probabilistic forecasts

> [!WARNING]
> Always ensure predictions are non-negative. Power generation cannot be negative, so use `np.maximum(predictions, 0)` before returning results. Alternatively, use the `clip_lower` constructor parameter (default: `0.0`) which handles this automatically.

---

## Helper Methods Reference

All base classes (`BaseStrategy` and `SimpleStrategy`) provide these utility methods:

| Method | Purpose |
|--------|---------|
| `_get_quantile_columns(X, quantile)` | Get column names ending with `_{quantile}` |
| `_extract_forecaster_id(col)` | Parse forecaster ID from column (e.g., `s1_q50` → `s1`) |
| `_format_predictions(values, quantile)` | Convert Series to output DataFrame format (with clipping) |
| `_set_equal_weights(quantile, cols)` | Assign equal weights to all forecasters |
| `_set_weights(quantile, dict)` | Set custom weight dictionary |
| `_add_metadata(key, value)` | Store metadata about the strategy run |
| `get_weights()` | Return the current weight dictionary |
| `get_result()` | Return a `ForecastResult` dataclass with predictions, weights, and metadata |

For testing, the `StrategyRegistry` also provides:

| Method | Purpose |
|--------|---------|
| `StrategyRegistry.is_registered(name)` | Check if a strategy name is registered |
| `StrategyRegistry.unregister(name)` | Remove a strategy from the registry (useful in tests) |
| `StrategyRegistry.clear()` | Remove all registered strategies (useful in tests) |

### Usage Example

```python
def _do_predict(self, X_test, quantiles):
    for quantile in quantiles:
        # Get columns for this quantile
        cols = self._get_quantile_columns(X_test, quantile)
        # Returns: ['s1_q50', 's2_q50', 's3_q50']

        # Extract forecaster IDs
        for col in cols:
            user = self._extract_forecaster_id(col)
            # Returns: 's1', 's2', 's3'

        # Format output correctly
        result = self._format_predictions(ensemble_series, quantile)
        # Returns DataFrame with [datetime, variable, value]

        # Store metadata for debugging
        self._add_metadata("n_forecasters", len(cols))
```

---

## Writing Tests

Test your strategy to ensure it handles edge cases and produces valid output.

### Test File Structure

Create `tests/strategies/test_my_strategy.py`:

```python
import pytest
import pandas as pd
import numpy as np
from src.strategies import MyStrategy, StrategyRegistry


class TestMyStrategy:
    """Tests for MyStrategy ensemble."""

    @pytest.fixture
    def strategy(self):
        """Create a fresh strategy instance for each test."""
        return MyStrategy()

    @pytest.fixture
    def sample_data(self):
        """Create sample forecaster predictions."""
        dates = pd.date_range("2024-01-01", periods=4, freq="15min", tz="UTC")
        return pd.DataFrame({
            "user1_q50": [10.0, 20.0, 30.0, 40.0],
            "user2_q50": [20.0, 30.0, 40.0, 50.0],
            "user3_q50": [30.0, 40.0, 50.0, 60.0],
        }, index=dates)

    @pytest.fixture
    def sample_target(self, sample_data):
        """Create sample observations (ground truth)."""
        return pd.DataFrame({
            "target": [15.0, 25.0, 35.0, 45.0]
        }, index=sample_data.index)

    def test_is_registered(self):
        """Strategy should be discoverable via registry."""
        assert StrategyRegistry.is_registered("my_strategy")

    def test_name_property(self, strategy):
        """Strategy should return correct name."""
        assert strategy.name == "my_strategy"

    def test_fit_marks_as_fitted(self, strategy, sample_data, sample_target):
        """After fit(), strategy should be marked as fitted."""
        strategy.fit(sample_data, sample_target, ["q50"])
        assert strategy.is_fitted

    def test_predict_output_format(self, strategy, sample_data, sample_target):
        """Predictions should have correct DataFrame structure."""
        strategy.fit(sample_data, sample_target, ["q50"])
        predictions = strategy.predict(sample_data, ["q50"])

        assert list(predictions.columns) == ["datetime", "variable", "value"]
        assert len(predictions) == 4  # One per timestamp

    def test_predictions_non_negative(self, strategy, sample_data, sample_target):
        """Power predictions should never be negative."""
        strategy.fit(sample_data, sample_target, ["q50"])
        predictions = strategy.predict(sample_data, ["q50"])

        assert (predictions["value"] >= 0).all()

    def test_weights_are_set(self, strategy, sample_data, sample_target):
        """Strategy should set forecaster weights."""
        strategy.fit(sample_data, sample_target, ["q50"])
        strategy.predict(sample_data, ["q50"])

        weights = strategy.get_weights()
        assert "q50" in weights
        assert len(weights["q50"]) > 0

    def test_weights_sum_to_one(self, strategy, sample_data, sample_target):
        """Normalized weights should sum to approximately 1."""
        strategy.fit(sample_data, sample_target, ["q50"])
        strategy.predict(sample_data, ["q50"])

        weights = strategy.get_weights()["q50"]
        assert abs(sum(weights.values()) - 1.0) < 0.001

    def test_handles_all_quantiles(self, strategy):
        """Strategy should work with q10, q50, and q90."""
        dates = pd.date_range("2024-01-01", periods=4, freq="15min", tz="UTC")
        X = pd.DataFrame({
            "u1_q10": [10, 20, 30, 40],
            "u1_q50": [15, 25, 35, 45],
            "u1_q90": [20, 30, 40, 50],
            "u2_q10": [12, 22, 32, 42],
            "u2_q50": [17, 27, 37, 47],
            "u2_q90": [22, 32, 42, 52],
        }, index=dates)
        y = pd.DataFrame({"target": [14, 24, 34, 44]}, index=dates)

        strategy.fit(X, y, ["q10", "q50", "q90"])
        predictions = strategy.predict(X, ["q10", "q50", "q90"])

        assert set(predictions["variable"].unique()) == {"q10", "q50", "q90"}
```

### Running Tests

From the project root, run tests for your strategy:

```bash
poetry run pytest tests/strategies/test_my_strategy.py -v
```

Run all strategy tests:

```bash
poetry run pytest tests/strategies/ -v
```

Run with coverage report:

```bash
poetry run pytest tests/strategies/ --cov=src/strategies
```

---

## Debugging Strategies

### Enable Debug Logging

See detailed execution information:

```bash
python simulate.py run --strategies="my_strategy" --log_level=debug
```

### Add Logging to Your Strategy

Use loguru for structured debug output:

```python
from loguru import logger

class MyStrategy(BaseStrategy):
    def _do_fit(self, X_train, y_train, quantiles, **kwargs):
        logger.debug(f"Training with {len(X_train)} samples")
        logger.debug(f"Columns: {list(X_train.columns)}")
        logger.debug(f"Quantiles: {quantiles}")

        # ... your logic ...

        logger.debug(f"Computed weights: {self._weights}")
```

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "Strategy not found" | Missing registration | Add `@StrategyRegistry.register("name")` decorator |
| "No columns for quantile" | Wrong column naming | Use `{forecaster_id}_{quantile}` format in data (e.g., `s1_q50`) |
| Empty predictions | `_do_predict` returns nothing | Check quantile column extraction with debug logging |
| Weights don't sum to 1 | Missing normalization | Divide by sum after computing weights |
| Negative predictions | No clipping | Use `np.maximum(values, 0)` |
| "Not fitted" error | Predict before fit | Ensure fit() is called first |
