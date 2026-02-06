# Ensemble Strategies

Part of the [Predico Forecast Engine](../../README.md). Strategies are applied during market sessions to combine forecaster predictions into ensemble forecasts.

This document covers the available ensemble strategies and how to create new ones.

## Available Strategies

| Strategy | Registry Key | Type | Description |
|----------|--------------|------|-------------|
| WeightedAverage | `weighted_avg` | Batch | Exponential weighting with DTW (Dynamic Time Warping) outlier detection |
| ArithmeticMean | `arithmetic_mean` | Batch | Simple unweighted average |
| Median | `median` | Batch | Median of forecaster predictions |
| BestForecaster | `best_forecaster` | Batch | Selects single best forecaster |

## Which Strategy Should I Use?

```
└─ Process all data at once? → BATCH STRATEGIES
    ├─ Production (default)           → weighted_avg
    ├─ Simple benchmark               → arithmetic_mean
    └─ Median-based benchmark         → median
```

---

## Creating Custom Strategies

### Directory Structure

```
strategies/
├── core/                   # Infrastructure (don't modify unless extending framework)
│   ├── base.py             # BaseStrategy - abstract base with fit/predict
│   ├── simple.py           # SimpleStrategy - simplified base for combine-only strategies
│   └── registry.py         # StrategyRegistry - plugin discovery
│
├── utils/                  # Shared utilities
│   └── outlier_detection.py # DTW-based outlier detection
│
├── median.py               # Example SimpleStrategy implementation
├── weighted_average.py     # Production ensemble (BaseStrategy)
├── arithmetic_mean.py      # Benchmark
└── best_forecaster.py      # Benchmark
```

### Class Hierarchy (Template Method Pattern)

```
BaseStrategy (abstract)
│
├── fit() / predict()              → Public API - handles state management
├── _do_fit() / _do_predict()      → @abstractmethod - implement your logic here
│
├── SimpleStrategy (extends BaseStrategy)
│   ├── _do_fit()                  → Concrete: stores kwargs for later use
│   ├── _do_predict()              → Concrete: iterates quantiles, calls combine()
│   └── combine()                  → @abstractmethod: YOU implement this
│
└── YourStrategy (extends any of the above)
    └── Implement required abstract methods for your chosen base class
```

### Which Base Class to Use?

| Use Case | Base Class | You Implement |
|----------|------------|---------------|
| Simple combination (mean, median, trimmed) | `SimpleStrategy` | `combine()` only |
| Need training phase (ML models, score computation) | `BaseStrategy` | `_do_fit()` + `_do_predict()` |
| Need outlier detection or complex logic | `BaseStrategy` | `_do_fit()` + `_do_predict()` |

```
Does your algorithm need custom training logic?
│
├── NO → Does it just combine forecasts into one prediction?
│        │
│        ├── YES → Use SimpleStrategy, implement combine()
│        │
│        └── NO → Use BaseStrategy
│
└── YES → Use BaseStrategy, implement _do_fit() and _do_predict()
```

---

## Quick Examples

### SimpleStrategy (Recommended for most cases)

```python
from src.strategies import SimpleStrategy, StrategyRegistry

@StrategyRegistry.register("my_median")
class MedianStrategy(SimpleStrategy):
    @property
    def name(self) -> str:
        return "my_median"

    def combine(self, forecasts, **kwargs):
        # forecasts: DataFrame with one column per forecaster
        # Return: Series with ensemble predictions
        return forecasts.median(axis=1)
```

The `quantile` parameter is optional - include it only if your algorithm needs it:

```python
def combine(self, forecasts, quantile, **kwargs):
    # Use quantile if needed for per-quantile logic
    self._set_weights(quantile, {"user1": 0.5, "user2": 0.5})
    return forecasts.mean(axis=1)
```

### BaseStrategy (For advanced strategies)

```python
from src.strategies import BaseStrategy, StrategyRegistry

@StrategyRegistry.register("my_ml_ensemble")
class MLEnsembleStrategy(BaseStrategy):
    @property
    def name(self) -> str:
        return "my_ml_ensemble"

    def _do_fit(self, X_train, y_train, quantiles, **kwargs):
        # Compute scores, train ML model, etc.
        self._model = train_my_model(X_train, y_train)

    def _do_predict(self, X_test, quantiles):
        # Use trained model to generate predictions
        # Must return DataFrame with [datetime, variable, value]
        predictions = self._model.predict(X_test)
        return self._format_predictions(predictions, "q50")
```

---

## Helper Methods

All base classes (`BaseStrategy` and `SimpleStrategy`) provide helper methods for common operations. See [Advanced Strategies — Helper Methods Reference](../../simulator/community/docs/advanced-strategies.md#helper-methods-reference) for the complete list.

> [!TIP]
> The `clip_lower` constructor parameter (default: `0.0`) automatically clips predictions to a minimum value. Set it to `None` if your forecast variable can be negative (e.g., temperature).

---

## Registration

All strategies must be registered with the `StrategyRegistry`:

```python
@StrategyRegistry.register("strategy_name")
class MyStrategy(SimpleStrategy):
    ...
```

Then add the import to `src/strategies/__init__.py` and include it in `__all__`:

```python
from .my_strategy import MyStrategy

__all__ = [
    # ... other strategies ...
    "MyStrategy",
]
```

> [!NOTE]
> Inside `__init__.py`, use **relative imports** (`from .my_strategy import ...`). In your strategy file itself, use **absolute imports** (`from src.strategies import ...`) since it runs from the project root.

> [!NOTE]
> Registry keys use **lowercase with underscores** (e.g., `weighted_avg`, `my_strategy`).

### End-to-End Example

After creating and registering your strategy, test it with the community simulator:

```bash
cd simulator/community
python simulate.py run --strategies="my_strategy" --n_sessions=10 --run_benchmarks=True
```

This runs your strategy alongside the default benchmarks (`arithmetic_mean`, `best_forecaster`) and outputs comparative evaluation metrics.

---

## See Also

- [`median.py`](median.py) - Reference SimpleStrategy implementation
- [`weighted_average.py`](weighted_average.py) - Reference BaseStrategy implementation (production)
- [`simulator/community/`](../../simulator/community/) - Standalone simulator for testing strategies
- [Contributing Guidelines](https://github.com/INESCTEC/.github/blob/main/documents/contributing.md) - Organization-wide contribution guidelines
