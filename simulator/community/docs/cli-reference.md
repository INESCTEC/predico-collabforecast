# CLI Reference

Complete reference for all `simulate.py` commands. The CLI is built with Python Fire, so you can use `--help` on any command for quick reference.

> [!NOTE]
> All commands assume you are running from the `simulator/community/` directory.

> [!TIP]
> Add `--help` to any command to see available options: `python simulate.py run --help`

## Commands Overview

| Command | Purpose |
|---------|---------|
| `quickstart` | Generate demo dataset and run simulation with plots |
| `run` | Execute a simulation with one or more strategies |
| `list_datasets` | Show available datasets |
| `create_dataset` | Create a new dataset from a template |
| `generate_dataset` | Generate a synthetic dataset for testing |
| `list_archetypes` | List available forecaster archetypes |
| `validate_dataset` | Check dataset structure before running |
| `evaluate` | Compute skill scores for existing results |
| `plot` | Generate visualization plots from results |
| `info` | Display simulator version and configuration |

---

## `simulate.py quickstart`

The fastest way to see the simulator in action. Generates a synthetic dataset and runs a complete simulation with evaluation plots.

```bash
python simulate.py quickstart
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--log_level` | str | `info` | Verbosity: debug, info, warning, error, quiet |

### What It Does

1. **Generates** a dataset called `quickstart_demo` with:
   - 15 forecasters: 5 biased, 5 biased_low, 5 skilled
   - 60 days of wind power data
   - Fixed seed (42) for reproducibility
   - Base capacity: 2000 MW
   - Diversity: 0.5 (moderate parameter variation within archetypes)

2. **Runs** a 30-session simulation with strategies: weighted_avg, arithmetic_mean, median, best_forecaster

3. **Displays** evaluation plots and individual forecaster comparison

If `quickstart_demo` already exists, it will be regenerated (overwritten).

### Example

```bash
python simulate.py quickstart
```

Output:
```
============================================================
QUICKSTART
============================================================

[1/2] Generating dataset...
      Name: quickstart_demo
      Forecasters: 15 (biased:5,biased_low:5,skilled:5)
      Data: 60 days of wind_power
      Seed: 42
      Dataset saved to: input/quickstart_demo/

[2/2] Running simulation (30 sessions)...
Running sessions: |████████| 30/30 [00:45<00:00]

SIMULATION COMPLETE
Results saved to: output/quickstart_demo/20260129_143022/

[Plot windows open]
```

---

## `simulate.py run`

The main command for running simulations. Processes market sessions sequentially, generating ensemble forecasts for each.

```bash
python simulate.py run [OPTIONS]
```

### Options

Control what data to use, which strategies to run, and how to process:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--dataset` | str | `example_elia` | Dataset name in `input/` directory |
| `--name` | str | auto | Custom name for output directory (default: timestamp) |
| `--n_sessions` | int | auto | Number of sessions to simulate |
| `--start_date` | str | auto | First session launch time (ISO UTC format, e.g., `2024-01-15T10:00:00Z`) |
| `--end_date` | str | auto | Last session launch time (ISO UTC format, e.g., `2024-01-25T10:00:00Z`) |
| `--session_freq` | int | `24` | Hours between sessions |
| `--output_dir` | str | auto | Custom output directory path |
| `--n_jobs` | int | `1` | Parallel workers for faster processing |
| `--run_benchmarks` | bool | `True` | Include benchmark strategies for comparison |
| `--strategies` | str | `weighted_avg` | Comma-separated list of strategies |
| `--datetime_format` | str | `%Y-%m-%d %H:%M` | Format for parsing CSV datetime columns |
| `--csv_delimiter` | str | `,` | CSV field delimiter |
| `--plot` | bool | `False` | Display plots when simulation completes |
| `--plot_individuals` | bool | `False` | Plot individual forecaster submissions vs observed |
| `--log_level` | str | `info` | Verbosity: debug, info, warning, error, quiet |

> [!NOTE]
> When `--n_sessions` is not specified, the simulator automatically determines the maximum number of sessions based on available data.

### Examples

Common usage patterns.

Basic run with defaults:

```bash
python simulate.py run
```

Name your run for easy identification:

```bash
python simulate.py run --name=baseline_v1
```

Test a specific strategy:

```bash
python simulate.py run --strategies="my_strategy" --n_sessions=5
```

Compare multiple strategies:

```bash
python simulate.py run --strategies="weighted_avg,median,my_strategy"
```

Add benchmarks for comparison:

```bash
python simulate.py run --strategies="my_strategy" --run_benchmarks=True
```

Faster processing with parallel workers:

```bash
python simulate.py run --n_sessions=30 --n_jobs=4
```

Specific date range:

```bash
python simulate.py run --start_date="2024-01-15T10:00:00Z" --end_date="2024-01-25T10:00:00Z"
```

Minimal output (errors only):

```bash
python simulate.py run --log_level=quiet
```

Debug output for troubleshooting:

```bash
python simulate.py run --log_level=debug
```

Show plots at end:

```bash
python simulate.py run --n_sessions=10 --plot=True
```

Show plots with individual forecaster comparison:

```bash
python simulate.py run --n_sessions=10 --plot_individuals
```

Custom datetime format for your CSVs:

```bash
python simulate.py run --datetime_format="%Y/%m/%d %H:%M:%S"
```

### Strategy Selection

The `--strategies` and `--run_benchmarks` options control which strategies execute:

| Command | What runs |
|---------|-----------|
| (defaults) | weighted_avg + arithmetic_mean + best_forecaster |
| `--strategies="median"` | median only |
| `--strategies="median,my_strategy"` | median + my_strategy |
| `--strategies="median" --run_benchmarks=True` | median + arithmetic_mean + best_forecaster |
| `--run_benchmarks=False` | weighted_avg only (no benchmarks) |

---

## `simulate.py list_datasets`

Show all datasets in the `input/` directory. Useful for checking what's available before running.

```bash
python simulate.py list_datasets
```

Output shows each dataset name and whether it has all required files (complete/incomplete).

---

## `simulate.py create_dataset`

Create a new dataset by copying an existing template. This gives you the correct file structure to fill in with your own data.

```bash
python simulate.py create_dataset --name=<name> [--template=example_elia]
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--name` | str | required | Name for your new dataset |
| `--template` | str | `example_elia` | Existing dataset to copy structure from |

**Example:**

Create new dataset:

```bash
python simulate.py create_dataset --name=my_wind_farm
```

Edit files in `input/my_wind_farm/`, then validate before running:

```bash
python simulate.py validate_dataset --name=my_wind_farm
```

---

## `simulate.py validate_dataset`

Check that a dataset has correct structure and content before running simulations. Catches common issues like missing files, wrong column names, or insufficient data. See [Dataset Format](dataset-format.md) for the full specification.

```bash
python simulate.py validate_dataset --name=<name> [OPTIONS]
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--name` | str | required | Dataset name to validate |
| `--datetime_format` | str | `%Y-%m-%d %H:%M` | Format for datetime parsing |

### What Gets Checked

The validator runs these checks in order:

1. **File existence**: config.json, measurements.csv, forecasts.csv all present
2. **Config validity**: Required fields (timezone, use_case) exist and have valid values
3. **Measurements structure**: Has `datetime` and `target` columns
4. **Forecasts structure**: Columns follow `{seller}_{quantile}` naming convention
5. **Date coverage**: At least 9 days of data (8 historical + 1 forecast target)
6. **Data quality**: No excessive missing values

**Example:**

```bash
python simulate.py validate_dataset --name=example_elia
```

Output: `Validation PASSED - all checks OK`

```bash
python simulate.py validate_dataset --name=broken_dataset
```

Output: `Validation FAILED - Missing 'target' column in measurements.csv`

---

## `simulate.py evaluate`

Compute skill scores by comparing ensemble forecasts against actual measurements. This runs automatically at the end of each simulation, but you can re-run it manually (e.g., if you update measurement data).

```bash
python simulate.py evaluate <results_dir> [OPTIONS]
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--dataset` | str | auto | Dataset name for loading observations |
| `--output_format` | str | `csv` | Output format: csv, json, or print |
| `--save_to` | str | auto | Custom output file path |
| `--datetime_format` | str | `%Y-%m-%d %H:%M` | Format for datetime parsing |

**Example:**

Re-evaluate existing results:

```bash
python simulate.py evaluate output/example_elia/20240115_103000/
```

Print to console without saving:

```bash
python simulate.py evaluate output/example_elia/20240115_103000/ --output_format=print
```

Save as JSON:

```bash
python simulate.py evaluate output/example_elia/20240115_103000/ --output_format=json
```

---

## `simulate.py plot`

Generate visualization plots from existing simulation results. Plots are displayed interactively or saved to file.

```bash
python simulate.py plot <results_dir> [OPTIONS]
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--dataset` | str | auto | Dataset name for loading observations |
| `--session_id` | int/str | `all` | Session ID to plot, or "all" |
| `--strategy` | str | `weighted_avg` | Strategy for prediction interval plot |
| `--plot_individuals` | bool | `False` | Plot individual forecaster submissions |
| `--datetime_format` | str | `%Y-%m-%d %H:%M` | Format for datetime parsing |
| `--save_to` | str | None | Path to save plots (e.g., "plots.png") |
| `--log_level` | str | `info` | Logging verbosity |

**Examples:**

Plot results interactively:

```bash
python simulate.py plot output/example_elia/20240115_103000/
```

Include individual forecasters (grey lines) vs ensembles (color):

```bash
python simulate.py plot output/example_elia/20240115_103000/ --plot_individuals
```

Save plots to file:

```bash
python simulate.py plot output/example_elia/20240115_103000/ --save_to=comparison.png
```

Plot a specific strategy's prediction intervals:

```bash
python simulate.py plot output/run1/ --strategy=arithmetic_mean
```

---

## `simulate.py generate_dataset`

Launch an interactive wizard to generate a synthetic dataset for testing ensemble strategies. Creates controlled test scenarios with known properties.

```bash
python simulate.py generate_dataset [OPTIONS]
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--log_level` | str | `info` | Logging verbosity |
| `--plot` | bool | `False` | Plot individual forecasts after generation |

The wizard guides you through:
1. **Dataset name** - Unique identifier for your dataset
2. **Use case** - Power generation type (wind_power, solar_power)
3. **Dataset size** - Number of days and base capacity
4. **Forecaster archetypes** - Mix of forecaster types
5. **Diversity** - Parameter variation within archetypes
6. **Scenarios** - Optional test conditions (regime_change, dropout, distribution_shift)
7. **Advanced options** - Random seed, start date

**Example:**

```bash
python simulate.py generate_dataset
```

Output files in `input/<name>/`:
- `config.json` - Dataset configuration
- `measurements.csv` - Synthetic power measurements
- `forecasts.csv` - Synthetic forecaster predictions
- `generation_log.json` - Full generation metadata for reproducibility

After generation, run a simulation:

```bash
python simulate.py run --dataset=<name> --n_sessions=10
```

---

## `simulate.py list_archetypes`

Display available forecaster archetypes for synthetic data generation. Shows archetype names with descriptions.

```bash
python simulate.py list_archetypes
```

**Output:**

| Archetype | Description |
|-----------|-------------|
| `skilled` | High accuracy, well-calibrated forecaster |
| `noisy` | Random errors around truth |
| `biased` | Systematic over-prediction |
| `biased_low` | Systematic under-prediction |
| `lagged` | Good but uses stale information |
| `overconfident` | Narrow intervals, poor coverage |
| `underconfident` | Wide intervals, good coverage |
| `adversarial` | Deliberately incorrect predictions |
| `intermittent` | Sometimes missing submissions |
| `variable` | Time-varying skill (daily + monthly drift) |
| `outlier` | Occasionally produces outlier predictions |
| `regime_high` | Accurate when output is high, biased when low |
| `regime_low` | Accurate when output is low, biased when high |

**Archetype specification format:**

```
archetype:count,archetype:count,...
```

**Examples:**

- `skilled:3,noisy:2` - 3 skilled + 2 noisy forecasters
- `skilled:2,biased:1,intermittent:1` - Mixed pool of 4 forecasters

---

## `simulate.py info`

Display simulator version and configuration. Useful for debugging or reporting issues.

```bash
python simulate.py info
```
