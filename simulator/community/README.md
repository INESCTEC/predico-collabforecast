# Predico Community Simulator

A standalone simulation environment for testing collaborative forecasting algorithms. Use this to develop and validate ensemble strategies without needing API access or database setup.

## Prerequisites

- **Python 3.12+**
- **Poetry** for dependency management (`pip install poetry`)

## Quick Start

### Installation

The simulator runs on the Predico Forecast Engine package. From the project root, install dependencies and activate the environment:

```bash
poetry install
```

```bash
poetry env activate
```

> [!NOTE]
> In [conda](https://www.anaconda.com/docs/getting-started/miniconda/main) environments, you may need to run `poetry env use python` to ensure the correct Python version is used.


Then move to the simulator directory:

```bash
cd simulator/community
```

And check the available commands on our simulator CLI:

```bash
python simulate.py --help
``` 


### Run Your First Simulation

#### Option A: Quickstart (Fastest)

We've created a quickstart command for you to quickly generate a synthetic dataset and see the simulator run immediately:

```bash
python simulate.py quickstart
```

This creates a `quickstart_demo` dataset with 15 forecasters, runs 30 market sessions, and displays evaluation plots. Check the generated output:

```bash
ls output/quickstart_demo/
```


#### Option B: Step-by-Step (More Control)

Generate a synthetic dataset using our interactive wizard:

```bash
python simulate.py generate_dataset
```

The wizard guides you through configuring forecasters, data size, and test scenarios.

Let's assume you named your dataset `my_dataset`. Check it by listing the available datasets:

```bash
python simulate.py list_datasets
```

Then run the simulation on your generated dataset:

```bash
python simulate.py run --n_sessions=10 --dataset=my_dataset
```

Check the generated output:

```bash
ls output/my_dataset/
```


## Creating Custom Datasets

The simulator supports both synthetic and real datasets. Use the `generate_dataset` command for synthetic data or create your own dataset folder with measurements and forecasts CSV files.


### Using Synthetic Data

The synthetic data generator creates controlled test datasets with configurable forecaster behaviors. Use `generate_dataset` for the interactive wizard or `quickstart` for instant defaults.


### Using Your Own Datasets

To test strategies on your own data, create a dataset with historical measurements and forecaster predictions.

> [!IMPORTANT]
> The simulator needs at least 9 days of 15-minute resolution data (8 days for training, 1 for forecasting).


#### First step: Create a new dataset from the template:

The easiest way is to first generate a synthetic dataset and then update it with your data. 
You might already have one if you ran `quickstart`, if not you can create one with:

```bash
python simulate.py generate_dataset
```

Then replace the generated CSV files with your real data while keeping the same format. Make sure to update `config.json` with the correct timezone and use case.

Edit the files in `input/<your-dataset-name>/`:
- `config.json` - Set timezone and use_case (wind_power, solar_power, etc.)
- `measurements.csv` - Historical observed values (must have 'target' column)
- `forecasts.csv` - Forecaster predictions using `{seller}_{quantile}` column names


#### Validate the Dataset

To ensure your dataset is correctly formatted and ready for simulation, run the validation command:

```bash
python simulate.py validate_dataset --name=your-dataset-name
# Expected: Validation PASSED - all checks OK
```

#### Simulate

After validation, run the simulation:

```bash
python simulate.py run --dataset=my_dataset
```

See [Dataset Format Specification](docs/dataset-format.md) for column formats and requirements.

## Creating Custom Strategies

Ensemble strategies combine multiple forecaster predictions into a single forecast. Create your own to test different combination approaches (weighted averages, ML models, outlier filtering, etc.).

A minimal strategy needs ~10 lines of code:

```python
# src/strategies/my_strategy.py (relative to the project root)
from src.strategies import SimpleStrategy, StrategyRegistry

@StrategyRegistry.register("my_strategy")
class MyStrategy(SimpleStrategy):
    @property
    def name(self) -> str:
        return "my_strategy"

    def combine(self, forecasts, **kwargs):
        # forecasts: DataFrame with one column per forecaster
        # Return: Series with your ensemble prediction
        return forecasts.mean(axis=1)
```

> [!TIP]
> The `quantile` parameter is optional. Include it explicitly only if your algorithm needs per-quantile logic (e.g., setting weights).

Register it by adding to `src/strategies/__init__.py`:

```python
from .my_strategy import MyStrategy
```

> [!NOTE]
> Strategy files use **absolute imports** (`from src.strategies import ...`) because they are executed from the project root. Inside `__init__.py`, **relative imports** (`from .my_strategy import ...`) are used because that file is part of the package.

Test your strategy:

```bash
python simulate.py run --strategies="my_strategy" --n_sessions=5
```

See [Strategy Development Guide](docs/strategy-guide.md) for input/output formats and more examples.

## Output Files

Each simulation run creates a timestamped folder with results. Use these files to evaluate strategy performance and debug issues.

Results are saved to `output/<dataset>/<timestamp>/`:

| File | Description |
|------|-------------|
| `sessions.csv` | Session metadata (launch times, forecaster counts, processing time) |
| `forecasts.csv` | Generated ensemble predictions for each strategy |
| `submissions.csv` | Individual forecaster submissions (for `--plot_individuals`) |
| `evaluation.csv` | Skill scores comparing predictions to actual measurements |
| `simulation.log` | Detailed execution log for debugging |

> [!NOTE]
> Skill scores (RMSE, Pinball Loss, Winkler) are computed and displayed automatically at the end of each run.

## Common Commands

Frequently used commands for running and comparing strategies.

### Running Simulations

Run specific strategies (comma-separated):

```bash
python simulate.py run --strategies="weighted_avg,median"
```

Compare your strategy against benchmarks (arithmetic_mean, best_forecaster are included by default; use `--run_benchmarks=False` to disable):

```bash
python simulate.py run --strategies="my_strategy" --run_benchmarks=True
```

Visualize results after simulation:

```bash
python simulate.py run --n_sessions=10 --plot=True
```

Re-evaluate existing results (e.g., after fixing measurement data):

```bash
python simulate.py evaluate output/<dataset>/<timestamp>/
```

See [CLI Reference](docs/cli-reference.md) for all available options.

## Visualizing Results

Generate plots from simulation results to compare strategies and analyze performance.

Plot results interactively:

```bash
python simulate.py plot output/<dataset>/<timestamp>/
```

Include individual forecaster submissions (grey lines) vs ensemble predictions:

```bash
python simulate.py plot output/<dataset>/<timestamp>/ --plot_individuals
```

Save plots to file instead of displaying:

```bash
python simulate.py plot output/<dataset>/<timestamp>/ --save_to=results.png
```

## Synthetic Dataset Options

The `generate_dataset` wizard and `quickstart` command create synthetic datasets for testing. This section covers advanced configuration options.

### Forecaster Archetypes

List available archetypes:

```bash
python simulate.py list_archetypes
```

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

Specify archetypes using the format `archetype:count,archetype:count,...`:
- `skilled:3,noisy:2` - 3 skilled + 2 noisy forecasters
- `skilled:2,biased:1,intermittent:1` - Mixed pool of 4 forecasters

### Test Scenarios

Scenarios add specific test conditions to stress-test ensemble strategies:

- **regime_change**: Forecaster performance degrades at a specific point
- **dropout**: Some forecasters stop submitting partway through
- **distribution_shift**: Underlying data distribution changes mid-dataset

### Diversity Parameter

Control how much forecaster parameters vary from archetype defaults:
- `0.0` = Identical parameters (only random sequences differ)
- `0.5` = Moderate variation in noise, bias, interval scale
- `1.0` = Maximum variation within archetype ranges

## Troubleshooting

Common errors and how to fix them:

| Error | Solution |
|-------|----------|
| "MarketClass not available" | Dependencies missing. Run `poetry install` from the project root |
| "Dataset not found" | Dataset doesn't exist. Check `python simulate.py list_datasets` |
| "Empty measurements dataset" | No data before simulation start date. Check your date ranges |
| "No sellers found" | Wrong column naming. Use `{seller}_{quantile}` format (e.g., `s1_q50`) |

## Learn More

- [Strategy Guide](docs/strategy-guide.md) - How to create ensemble strategies
- [Advanced Strategies](docs/advanced-strategies.md) - ML models, historical scores, testing
- [CLI Reference](docs/cli-reference.md) - All command-line options
- [Dataset Format](docs/dataset-format.md) - CSV column specifications
- [Evaluation Metrics](docs/evaluation-metrics.md) - How RMSE, Pinball, and Winkler scores work

## Architecture

Overview of the simulator components:

```
community/
├── simulate.py          # CLI entry point (Fire-based)
├── core/                # Core simulation logic
│   ├── manager.py       # SimulatorManager orchestrates runs
│   ├── agents.py        # Loads forecasters and measurements
│   ├── session.py       # Creates market sessions
│   ├── metrics.py       # Computes evaluation scores
│   ├── plots.py         # Visualization and plotting
│   └── generator.py     # Synthetic dataset generation
├── docs/                # User documentation (strategy guides, CLI reference, etc.)
├── input/               # Input datasets (measurements + forecasts)
└── output/              # Simulation results (gitignored)
```
