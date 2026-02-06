# Dataset Format Specification

This document describes the file format for simulator datasets. A dataset contains historical measurements and forecaster predictions that the simulator uses to test ensemble strategies.

## Directory Structure

Each dataset is a folder containing exactly 3 files:

```
input/my_dataset/
├── config.json         # Timezone and forecast type settings
├── measurements.csv    # Historical observed values (ground truth)
└── forecasts.csv       # Forecaster predictions to combine
```

> [!TIP]
> Datasets created with `generate_dataset` or `quickstart` also include a `generation_log.json` file with full generation metadata (archetypes, seed, parameters) for reproducibility.

---

## config.json

Configuration settings that tell the simulator how to interpret your data.

```json
{
  "timezone": "Europe/Brussels",
  "use_case": "wind_power"
}
```

| Field | Required | Purpose |
|-------|----------|---------|
| `timezone` | Yes | Timezone for calculating forecast challenge periods (market sessions are defined in local time) |
| `use_case` | Yes | Type of forecast, affects which strategies are applicable |

### Supported Timezones

Use any valid IANA timezone identifier:

- `Europe/Brussels` - Central European Time
- `Europe/London` - UK time
- `America/New_York` - US Eastern
- `UTC` - Coordinated Universal Time

### Use Cases

| Value | Description |
|-------|-------------|
| `wind_power` | Wind power generation (MW) |
| `wind_power_ramp` | Wind power ramp events |
| `solar_power` | Solar power generation (MW) |
| `load` | Electricity demand/load (MW) |

---

## measurements.csv

Historical observed values - the ground truth that forecasts are compared against. This is what forecasters are trying to predict.

### Required Columns

> [!IMPORTANT]
> Both columns are required. The `target` column must be named exactly as shown (case-sensitive).

| Column | Type | Purpose |
|--------|------|---------|
| `datetime` | string | Timestamp for each observation |
| `target` | float | Observed value (e.g., power generation in MW) |

### Example

```csv
datetime,target
2023-01-24 00:00,423.57
2023-01-24 00:15,427.90
2023-01-24 00:30,443.67
2023-01-24 00:45,451.22
2023-01-24 01:00,458.89
```

### Requirements

- **Time resolution**: 15-minute intervals (96 values per day)
- **Minimum duration**: At least 9 days (8 for training history, 1 for forecast target)
- **No gaps**: Every 15-minute slot should have a value
- **Timezone**: Store datetimes in UTC without timezone suffix (no trailing `Z`, `+00:00`, or similar). The simulator localizes them as UTC internally. The `timezone` field in `config.json` is used only for market session boundary calculations (e.g., defining what "tomorrow" means in local time).

---

## forecasts.csv

Predictions from multiple forecasters. The simulator combines these using ensemble strategies.

### Column Naming Convention

> [!WARNING]
> Column names **must** follow the pattern: `{seller_id}_{quantile}`. The simulator uses this naming to automatically detect forecasters. Incorrect naming will result in "No sellers found" errors.

- **seller_id**: Unique forecaster identifier (e.g., `s1`, `alice`, `model_v2`). The terms "seller" and "forecaster" refer to the same entity — in the Predico platform, forecasters "sell" their predictions on the marketplace.
- **quantile**: One of `q10`, `q50`, `q90`

This naming lets the simulator automatically detect forecasters and their predictions.

### Required Columns

| Column | Type | Purpose |
|--------|------|---------|
| `datetime` | string | Timestamp matching measurements |
| `{seller_id}_q10` | float | 10th percentile forecast (lower bound) |
| `{seller_id}_q50` | float | 50th percentile forecast (point forecast) |
| `{seller_id}_q90` | float | 90th percentile forecast (upper bound) |

### Example

Two forecasters (`s1` and `s2`) with probabilistic predictions:

```csv
datetime,s1_q10,s1_q50,s1_q90,s2_q10,s2_q50,s2_q90
2023-01-24 00:00,180.65,428.19,675.73,186.85,452.98,703.58
2023-01-24 00:15,185.20,431.22,677.24,180.58,448.11,621.57
2023-01-24 00:30,190.15,435.67,680.19,175.32,443.25,618.72
```

The simulator detects:
- **2 forecasters**: `s1` and `s2`
- **3 quantiles each**: `q10`, `q50`, `q90`

### Seller ID Rules

Keep IDs simple and consistent:

- Use alphanumeric characters and underscores: `s1`, `alice`, `model_v2`
- Avoid special characters: no spaces, hyphens, or dots
- IDs are case-sensitive: `Alice` and `alice` are different forecasters

### Requirements

- **All three quantiles required** for each forecaster
- **Same timestamps** as measurements.csv
- **Same resolution** (15-minute intervals)
- **Quantile ordering**: Values should satisfy `q10 ≤ q50 ≤ q90` (not enforced, but expected)

---

## Datetime Handling

### Default Format

The default format is `%Y-%m-%d %H:%M`:

```
2023-01-24 00:00
2023-01-24 00:15
```

### Custom Formats

If your data uses a different format, specify it when running:

```bash
# ISO format with seconds
python simulate.py run --datetime_format="%Y-%m-%dT%H:%M:%S"

# Slash-separated dates
python simulate.py run --datetime_format="%Y/%m/%d %H:%M"
```

### Timezone Interpretation

> [!NOTE]
> Store datetimes in **UTC** without timezone suffix (no trailing `Z`, `+00:00`, or similar). The simulator localizes all timestamps as UTC internally. The `timezone` setting in `config.json` controls **market session boundaries only** — it determines how the simulator calculates "tomorrow" and forecast challenge periods in local time.

- Ensure measurements and forecasts use the same timezone (both in UTC)

---

## Validation

Always validate your dataset before running simulations to catch formatting errors early:

```bash
python simulate.py validate_dataset --name=my_dataset
```

### Common Validation Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "Missing config.json" | File not found | Create config.json with timezone and use_case |
| "Missing target column" | Wrong column name | Rename your value column to `target` |
| "No sellers found" | Wrong column naming | Use `{seller}_{quantile}` format (e.g., `s1_q50`) |
| "Insufficient date range" | Less than 9 days | Add more historical data |
| "Missing quantile" | Incomplete forecaster | Ensure each seller has q10, q50, and q90 |

---

## Creating a Dataset

Step-by-step process for creating a new dataset.

**Step 1:** Create from template (copies example_elia structure):

```bash
python simulate.py create_dataset --name=my_solar_plant
```

**Step 2:** Edit `config.json` with your settings:

```bash
cat > input/my_solar_plant/config.json << 'EOF'
{
  "timezone": "Europe/Brussels",
  "use_case": "solar_power"
}
EOF
```

**Step 3:** Replace `measurements.csv` with your observed data (must have `datetime` and `target` columns).

**Step 4:** Replace `forecasts.csv` with your forecaster predictions (use `{seller}_{quantile}` column names).

**Step 5:** Validate the dataset:

```bash
python simulate.py validate_dataset --name=my_solar_plant
```

**Step 6:** Run simulation:

```bash
python simulate.py run --dataset=my_solar_plant --n_sessions=10
```

---

## Data Preparation Tips

### Converting Existing Data

If you have data in a different format:

1. **Reshape forecasts**: Pivot so each forecaster-quantile combination is a column
2. **Rename columns**: Follow `{seller}_{quantile}` convention
3. **Align timestamps**: Ensure measurements and forecasts have identical datetime values
4. **Fill gaps**: Interpolate or remove periods with missing data

### Minimum Data Requirements

| Requirement | Value | Why |
|-------------|-------|-----|
| Time resolution | 15 minutes | Matches Predico platform |
| Minimum duration | 9 days | 8 days training + 1 day forecast |
| Forecasters | 1+ | At least one forecaster to combine |
| Quantiles | 3 (q10, q50, q90) | Required for probabilistic evaluation |

---

## See Also

- [CLI Reference](cli-reference.md) - All simulator commands and options
- [Strategy Guide](strategy-guide.md) - How to create ensemble strategies
