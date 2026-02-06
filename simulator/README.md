# Forecast Simulator

Part of the [Predico Forecast Engine](../README.md). This directory contains standalone simulators for developing, testing, and benchmarking ensemble forecasting strategies without requiring API or database access.

## Prerequisites

- **Python 3.12+**
- **Poetry** for dependency management
- Install dependencies from the project root: `poetry install`

## Simulators

### Community Simulator (`community/`)

The **public, open-source simulator** for strategy development and benchmarking.

**Features:**
- Run forecasts on synthetic or custom datasets
- Compare multiple ensemble strategies
- Generate evaluation metrics (RMSE, MAE, Pinball Loss, Winkler)
- Visualize results with built-in plotting

**Quick Start:**
```bash
cd community
python simulate.py quickstart
# Or for more control:
python simulate.py run --dataset=example_elia --n_sessions=10
```

See [`community/README.md`](community/README.md) for detailed documentation.

### Internal Simulator (`internal/`)

Validation tools for running ensemble strategies against production backup data. Requires access to session backup files (not included in the open-source release).

See [`internal/README.md`](internal/README.md) for details.

## Directory Structure

```
simulator/
├── community/          # Public simulator (included in open-source release)
│   ├── core/           # Core simulation components
│   ├── input/          # Sample datasets
│   ├── docs/           # User documentation
│   ├── output/         # Simulation results
│   └── simulate.py     # CLI entry point
└── internal/           # Internal validation against production backups (requires backup data)
    ├── core/           # Backup loader, metrics, plotting
    ├── files/          # Session backup files (not committed)
    ├── output/         # Validation results (auto-created)
    ├── README.md       # Internal simulator documentation
    └── validate.py     # CLI entry point
```
