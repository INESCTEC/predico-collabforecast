"""
Assessment module for forecaster evaluation and scoring.

This module provides functions for:
- Validating forecaster submissions
- Creating assessment reports for forecaster performance
- Computing skill scores (RMSE, Pinball Loss, Winkler, etc.)
"""

from .report import create_assessment_report, validate_forecasters
from .score_calculator import compute_scores
from .skills import (
    compute_forecasters_skill_scores,
    rmse_df,
    pinball_loss_df,
    winkler_df,
    mae_df,
    mse_boxplot_df,
)

__all__ = [
    "create_assessment_report",
    "validate_forecasters",
    "compute_scores",
    "compute_forecasters_skill_scores",
    "rmse_df",
    "pinball_loss_df",
    "winkler_df",
    "mae_df",
    "mse_boxplot_df",
]
