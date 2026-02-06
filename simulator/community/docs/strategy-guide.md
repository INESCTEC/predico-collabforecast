# Creating Ensemble Strategies

Ensemble strategies combine predictions from multiple forecasters into a single, more accurate forecast. This guide shows how to create custom strategies using the `SimpleStrategy` base class.

> [!TIP]
> For most use cases, `SimpleStrategy` is the recommended approach. It handles quantile iteration, column extraction, and output formatting automatically. Only use `BaseStrategy` when you need custom training logic.

## 30-Second Version

The fastest way to create a working strategy. Copy this template and modify the `combine()` method:

```python
# src/strategies/my_strategy.py
from src.strategies import SimpleStrategy, StrategyRegistry

@StrategyRegistry.register("my_strategy")
class MyStrategy(SimpleStrategy):
    @property
    def name(self) -> str:
        return "my_strategy"

    def combine(self, forecasts, **kwargs):
        return forecasts.mean(axis=1)
```

> [!TIP]
> The `quantile` parameter is optional. Include it explicitly only if your algorithm needs it (see examples below).

Register it in `src/strategies/__init__.py`:

```python
from .my_strategy import MyStrategy
```

> [!IMPORTANT]
> The registration step is required. Without the import in `__init__.py`, the registry won't discover your strategy.

> [!NOTE]
> Strategy files use **absolute imports** (`from src.strategies import ...`) because they run from the project root. Inside `__init__.py`, use **relative imports** (`from .my_strategy import ...`).

Test it:

```bash
cd simulator/community
```

```bash
python simulate.py run --strategies="my_strategy" --n_sessions=5
```

**That's it.** `SimpleStrategy` handles quantile iteration, column extraction, and output formatting automatically.

---

## SimpleStrategy Explained

SimpleStrategy is designed for strategies that only need to combine forecasts - no training or state required. You implement one method: `combine()`.

### The `combine()` Method

This method is called once per quantile (q10, q50, q90). Return a Series with your ensemble prediction:

```python
def combine(self, forecasts: pd.DataFrame, **kwargs) -> pd.Series:
    """
    Combine forecaster predictions into an ensemble.

    Args:
        forecasts: DataFrame with one column per forecaster
        **kwargs: Contains 'quantile' and other context from fit()

    Returns:
        Series with ensemble predictions (same index as input)
    """
```

The `quantile` parameter is passed as a keyword argument, so you can include it explicitly if needed:

```python
# Without quantile (simplest form)
def combine(self, forecasts, **kwargs):
    return forecasts.mean(axis=1)

# With explicit quantile (for per-quantile logic)
def combine(self, forecasts, quantile, **kwargs):
    self._set_weights(quantile, {"s1": 0.5, "s2": 0.5})
    return forecasts.mean(axis=1)
```

### Input: The `forecasts` DataFrame

Each column contains one forecaster's predictions. Column names follow the `{forecaster_id}_{quantile}` pattern (in CSV files, this may appear as `{seller_id}_{quantile}` — "seller" and "forecaster" refer to the same entity):

> [!NOTE]
> The terms **seller** and **forecaster** are used interchangeably. In the Predico platform, forecasters "sell" their predictions on the marketplace, hence the naming in data files.

```
                           s1_q50    s2_q50    s3_q50
datetime
2023-02-16 00:00:00+00:00  428.19   452.98   249.39
2023-02-16 00:15:00+00:00  422.75   445.21   249.55
2023-02-16 00:30:00+00:00  418.32   439.44   250.71
```

- **Index**: DatetimeIndex with 15-minute intervals (96 per day = 24 hours x 4 intervals/hour)
- **Columns**: One per forecaster for the current quantile
- **Values**: Power predictions (typically in MW)

### Output: Return a Series

Your `combine()` method must return a pandas Series with:
- Same index as input (datetime)
- One value per timestamp (your ensemble prediction)

```python
def combine(self, forecasts, **kwargs):
    return forecasts.mean(axis=1)  # Returns Series with same index
```

---

## Examples

### Median Strategy

Use median instead of mean for robustness against outliers. A single bad forecaster won't skew results:

```python
@StrategyRegistry.register("median")
class MedianStrategy(SimpleStrategy):
    """Median is robust to outliers - one bad forecaster won't skew results."""

    @property
    def name(self) -> str:
        return "median"

    def combine(self, forecasts, **kwargs):
        return forecasts.median(axis=1)
```

### Trimmed Mean

Remove the highest and lowest predictions before averaging. Useful when you expect some forecasters to be consistently biased:

```python
@StrategyRegistry.register("trimmed_mean")
class TrimmedMeanStrategy(SimpleStrategy):
    """Remove extreme values before averaging. Requires 3+ forecasters."""

    @property
    def name(self) -> str:
        return "trimmed_mean"

    def combine(self, forecasts, **kwargs):
        # Sort each row, drop first and last, average the rest
        return forecasts.apply(
            lambda row: row.sort_values()[1:-1].mean(),
            axis=1
        )
```

### Custom Weights

Assign different weights to forecasters based on domain knowledge or external criteria:

```python
@StrategyRegistry.register("custom_weighted")
class CustomWeightedStrategy(SimpleStrategy):
    """Apply fixed weights based on known forecaster quality."""

    @property
    def name(self) -> str:
        return "custom_weighted"

    def combine(self, forecasts, quantile, **kwargs):
        # Define weights (must match forecaster IDs in your data)
        weights = {"s1": 0.5, "s2": 0.3, "s3": 0.2}

        # Store weights for reporting (optional)
        self._set_weights(quantile, weights)

        # Compute weighted sum
        result = pd.Series(0.0, index=forecasts.index)
        for col in forecasts.columns:
            user = self._extract_forecaster_id(col)  # "s1_q50" -> "s1"
            result += forecasts[col] * weights.get(user, 0)
        return result
```

---

## Running Your Strategy

### Basic Commands

Test and compare your strategy using the simulator.

Navigate to the community examples directory:

```bash
cd simulator/community
```

Run your strategy alone:

```bash
python simulate.py run --strategies="my_strategy" --n_sessions=10
```

Compare against standard benchmarks (arithmetic_mean, best_forecaster):

```bash
python simulate.py run --strategies="my_strategy" --run_benchmarks=True
```

Run multiple strategies for comparison:

```bash
python simulate.py run --strategies="my_strategy,median,weighted_avg"
```

Show plots after simulation:

```bash
python simulate.py run --strategies="my_strategy" --plot=True
```

### Output Location

Find your results in `output/<dataset>/<timestamp>/`:

| File | What it contains |
|------|------------------|
| `forecasts.csv` | Your ensemble predictions (datetime, variable, value, strategy) |
| `evaluation.csv` | Skill scores comparing predictions to actual measurements |

---

## Checklist

Follow these steps when creating a new strategy:

1. Create file: `src/strategies/my_strategy.py`
2. Add decorator: `@StrategyRegistry.register("my_strategy")`
3. Implement: `name` property and `combine()` method
4. Register: Add import to `src/strategies/__init__.py`
5. Test: `python simulate.py run --strategies="my_strategy"`
6. Compare: Add `--run_benchmarks=True` to see how it compares

---

## Learn More

For advanced topics like training ML models or using historical performance scores:

- [Advanced Strategies](advanced-strategies.md) - BaseStrategy, ML models, historical scores
- [Writing Tests](advanced-strategies.md#writing-tests) - pytest examples for your strategy
- [Evaluation Metrics](evaluation-metrics.md) - Understanding RMSE, Pinball, Winkler scores
- [Reference Implementation](../../../src/strategies/median.py) - `SimpleStrategy` example
