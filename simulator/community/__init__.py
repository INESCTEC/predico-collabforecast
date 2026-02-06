"""
Community Forecast Simulator Package.

This package provides a standalone simulation environment for testing
collaborative forecasting algorithms without requiring API or database access.

Usage:
    python simulate.py run --dataset=example_elia --n_sessions=10
    python simulate.py list_datasets
    python simulate.py evaluate output/20250101_120000/
"""

from .simulator import SimulatorManager, AgentsLoader, SessionGenerator

__all__ = ["SimulatorManager", "AgentsLoader", "SessionGenerator"]
__version__ = "1.0.0"
