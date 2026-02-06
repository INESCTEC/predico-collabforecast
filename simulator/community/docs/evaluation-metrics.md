# Evaluation Metrics

This document explains the skill metrics used to evaluate forecast quality. Understanding these metrics helps you interpret results and design better ensemble strategies.

## Overview

The simulator evaluates forecasts on two tracks:

| Track | Quantile | Metrics | What it measures |
|-------|----------|---------|------------------|
| **Deterministic** | Q50 | RMSE, MAE | Point forecast accuracy |
| **Probabilistic** | Q10, Q90 | Pinball Loss, Winkler | Uncertainty quantification |

> [!NOTE]
> **Lower values are better** for all metrics. This applies to RMSE, MAE, Pinball Loss, and Winkler scores.

---

## Deterministic Metrics (Q50)

These metrics evaluate the point forecast (median prediction). Use them to assess how close predictions are to actual values.

### RMSE (Root Mean Square Error)

Measures average error magnitude, with higher penalty for large errors. Use RMSE when large errors are particularly costly.

**Formula:**

```
RMSE = sqrt(mean((observed - forecast)²))
```

**Example:**

```
Observed:  [100, 200, 300]
Forecast:  [110, 190, 320]
Errors:    [-10,  10, -20]
Squared:   [100, 100, 400]
MSE:       200
RMSE:      14.14 MW
```

**Interpretation:**
- Same units as the forecast variable (e.g., MW)
- Sensitive to outliers (one big error significantly increases RMSE)
- A good benchmark: RMSE should be lower than simply predicting the mean

### MAE (Mean Absolute Error)

Measures average error magnitude without squaring. More robust to outliers than RMSE.

**Formula:**

```
MAE = mean(|observed - forecast|)
```

**Example:**

```
Observed:  [100, 200, 300]
Forecast:  [110, 190, 320]
Errors:    [-10,  10, -20]
Absolute:  [ 10,  10,  20]
MAE:       13.33 MW
```

**Interpretation:**
- Same units as the forecast variable
- Easier to interpret: "on average, we're off by X MW"
- Less sensitive to occasional large errors than RMSE

### When to Use Each

> [!TIP]
> Use RMSE as your primary metric for comparing strategies, as it's the standard in the energy forecasting industry. Use MAE as a complementary metric when you suspect outliers are affecting RMSE.

| Situation | Prefer |
|-----------|--------|
| Large errors are very costly | RMSE |
| Want intuitive interpretation | MAE |
| Data has outliers | MAE |
| Comparing to other studies | RMSE (more common) |

---

## Probabilistic Metrics (Q10, Q90)

These metrics evaluate uncertainty quantification - how well the forecast captures the range of possible outcomes.

### Pinball Loss (Quantile Loss)

Measures how well a quantile forecast captures the intended probability level. Different quantiles have different penalty structures.

**Formula:**

```
If observed > forecast:  q × (observed - forecast)    [under-prediction]
If observed ≤ forecast:  (1-q) × (forecast - observed) [over-prediction]
```

Where `q` is the quantile level (0.10 for Q10, 0.90 for Q90).

**Why asymmetric?**

For Q10 (10th percentile), we expect the observation to be above the forecast 90% of the time. So:
- Under-prediction (obs > forecast) is expected → small penalty (10%)
- Over-prediction (obs < forecast) is unexpected → large penalty (90%)

**Example for Q10 (q = 0.10):**

```
Observed: 100, Forecast: 120 (over-prediction)
Loss: (1 - 0.10) × (120 - 100) = 0.90 × 20 = 18

Observed: 100, Forecast: 80 (under-prediction)
Loss: 0.10 × (100 - 80) = 0.10 × 20 = 2
```

**Example for Q90 (q = 0.90):**

```
Observed: 100, Forecast: 120 (over-prediction)
Loss: (1 - 0.90) × (120 - 100) = 0.10 × 20 = 2

Observed: 100, Forecast: 80 (under-prediction)
Loss: 0.90 × (100 - 80) = 0.90 × 20 = 18
```

**Interpretation:**
- Lower is better
- A well-calibrated Q10 should have observations above it ~90% of the time
- A well-calibrated Q90 should have observations below it ~90% of the time

### Winkler Score (Interval Score)

Evaluates prediction intervals (Q10 to Q90) by considering both:
1. **Width**: Narrower intervals are better (more informative)
2. **Coverage**: Intervals that miss the observation are penalized

**Formula:**

```
Winkler = width + penalty_lower + penalty_upper

where:
  width = Q90 - Q10
  penalty_lower = (2/α) × max(0, Q10 - observed)  [if obs below Q10]
  penalty_upper = (2/α) × max(0, observed - Q90)  [if obs above Q90]
  α = 0.20 (for 80% prediction interval)
```

The penalty factor `2/α = 10` makes missing the interval costly.

**Example 1: Observation within interval (good)**

```
Q10 = 80, Q90 = 120, Observed = 100
Width:         120 - 80 = 40
Lower penalty: 10 × max(0, 80 - 100) = 0
Upper penalty: 10 × max(0, 100 - 120) = 0
Winkler:       40 + 0 + 0 = 40
```

**Example 2: Observation below Q10 (miss)**

```
Q10 = 80, Q90 = 120, Observed = 60
Width:         120 - 80 = 40
Lower penalty: 10 × max(0, 80 - 60) = 10 × 20 = 200
Upper penalty: 10 × max(0, 60 - 120) = 0
Winkler:       40 + 200 + 0 = 240
```

**Example 3: Observation above Q90 (miss)**

```
Q10 = 80, Q90 = 120, Observed = 150
Width:         120 - 80 = 40
Lower penalty: 10 × max(0, 80 - 150) = 0
Upper penalty: 10 × max(0, 150 - 120) = 10 × 30 = 300
Winkler:       40 + 0 + 300 = 340
```

**Interpretation:**
- Lower is better
- Rewards sharp (narrow) intervals that capture the observation
- Heavily penalizes intervals that miss the observation
- A score of ~40-60 is typical for well-calibrated 80% intervals (scale-dependent; values vary with the magnitude of the forecast variable)

---

## Evaluation Output

### evaluation.csv Format

The simulator outputs one row per strategy-quantile combination:

| Column | Description |
|--------|-------------|
| `strategy` | Strategy name (e.g., "weighted_avg") |
| `variable` | Quantile ("q10", "q50", "q90") or "interval" |
| `n_observations` | Number of forecast-observation pairs evaluated |
| `rmse` | Root Mean Square Error (Q50 only) |
| `mae` | Mean Absolute Error (Q50 only) |
| `pinball` | Pinball loss (all quantiles) |
| `winkler` | Winkler interval score (interval row only) |

### Example Output

```csv
strategy,variable,n_observations,rmse,mae,pinball,winkler
weighted_avg,q10,960,,,12.45,
weighted_avg,q50,960,45.23,32.18,22.61,
weighted_avg,q90,960,,,18.72,
weighted_avg,interval,960,,,,156.89
arithmetic_mean,q10,960,,,14.32,
arithmetic_mean,q50,960,52.67,38.45,26.33,
arithmetic_mean,q90,960,,,21.18,
arithmetic_mean,interval,960,,,,178.45
```

---

## Comparing Strategies

### What to Look For

When comparing strategies, check multiple metrics:

| Goal | Primary Metric |
|------|----------------|
| Best point forecast | RMSE or MAE (Q50) |
| Best uncertainty quantification | Winkler score |
| Balanced performance | Both RMSE and Winkler |

### Example Comparison

```
Strategy        | RMSE  | Winkler | Assessment
----------------|-------|---------|------------
weighted_avg    | 45.23 | 156.89  | Best overall
arithmetic_mean | 52.67 | 178.45  | Baseline
best_forecaster | 48.12 | 165.32  | Better than mean
my_strategy     | 44.10 | 152.33  | New best!
```

### Signs of a Good Ensemble Strategy

A well-designed ensemble should:

1. **Beat the best individual forecaster** - Combining should add value
2. **Beat simple averaging** - Weighting/filtering should help
3. **Have consistent performance** - Similar scores across different periods
4. **Show calibrated intervals** - ~20% of observations outside Q10-Q90

---

## Using the Evaluate Command

### Basic Usage

Scores are computed automatically after each simulation. To re-evaluate:

Re-evaluate existing results:

```bash
python simulate.py evaluate output/example_elia/20240115_103000/
```

Print to console (no file saved):

```bash
python simulate.py evaluate output/example_elia/20240115_103000/ --output_format=print
```

Save as JSON instead of CSV:

```bash
python simulate.py evaluate output/example_elia/20240115_103000/ --output_format=json
```

### When to Re-evaluate

You might want to re-evaluate when:
- You've updated measurement data (corrected errors)
- You want to compute scores for a subset of the data
- You're comparing against a different baseline

---

## See Also

- [CLI Reference](cli-reference.md) - All simulator commands and options
- [Dataset Format](dataset-format.md) - Input data specifications
