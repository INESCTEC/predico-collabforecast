"""
Core subpackage for the community forecast simulator.

This package contains the core components for running standalone forecast simulations:
- SimulatorManager: Manages simulation lifecycle, reports, and logging
- AgentsLoader: Loads datasets (measurements, forecasts, resources)
- SessionGenerator: Creates mock market sessions and challenges
- ForecastPlotter: Visualization for forecast comparison and metrics
- SyntheticGenerator: Generate synthetic datasets for testing
- metrics: Evaluation metrics (RMSE, MAE, Pinball, Winkler)
"""

from .manager import SimulatorManager, SimulatorConfig
from .agents import AgentsLoader
from .session import SessionGenerator
from .plots import ForecastPlotter
from .generator import SyntheticGenerator
from . import metrics

__all__ = [
    "SimulatorManager",
    "SimulatorConfig",
    "AgentsLoader",
    "SessionGenerator",
    "ForecastPlotter",
    "SyntheticGenerator",
    "metrics",
]
