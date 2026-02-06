"""
Score calculator for computing forecaster skill scores.

This module provides a helper function for strategies to compute their own
skill scores from training data, decoupling score computation from the
orchestration layer.
"""

import pandas as pd

from .skills import rmse_df, pinball_loss_df

SAMPLES_PER_DAY = 96  # 15-min resolution


def compute_scores(
    X_train: pd.DataFrame,
    y_train: pd.DataFrame,
    quantiles: list[str],
    n_days: int = 6,
) -> dict[str, dict[str, float]]:
    """
    Compute skill scores from training data.

    This function computes RMSE (for q50) or Pinball loss (for q10/q90)
    for each forecaster column based on the most recent n_days of data.

    :param X_train: Forecaster predictions DataFrame.
        Columns should be in format "{forecaster_id}_{quantile}".
    :param y_train: Actual values DataFrame with 'target' column.
    :param quantiles: List of quantile names (e.g., ["q10", "q50", "q90"])
    :param n_days: Number of lookback days for scoring (default: 6)

    :return: Dict mapping quantile -> {column_name: score}
        Example: {"q50": {"user1_q50": 0.05, "user2_q50": 0.08}, ...}
    """
    n_samples = n_days * SAMPLES_PER_DAY
    X = X_train.tail(n_samples)
    y = y_train.tail(n_samples)

    scores: dict[str, dict[str, float]] = {}

    for quantile in quantiles:
        scores[quantile] = {}
        cols = [c for c in X.columns if c.endswith(quantile)]

        for col in cols:
            df = pd.DataFrame(
                {"observed": y["target"].values, "forecast": X[col].values},
                index=X.index,
            ).dropna()

            if df.empty:
                continue

            if quantile == "q50":
                score = rmse_df(df)
            else:
                score = pinball_loss_df(df, quantile)

            scores[quantile][col] = score

    return scores
