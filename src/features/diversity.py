"""Forecaster diversity metrics utilities."""

import pandas as pd
import numpy as np


def create_diversity_features(
    df: pd.DataFrame,
    quantile: str | None = None,
) -> pd.DataFrame:
    """
    Create forecaster diversity metrics (std, var, mean across forecasters).

    Calculates statistics across forecaster columns for each row, measuring
    the agreement/disagreement between forecasters.

    :param df: DataFrame with forecaster columns (e.g., 'user1_q50', 'user2_q50')
    :param quantile: Quantile pattern to filter columns (e.g., 'q50').
                    If None, uses all numeric columns.
    :return: DataFrame with diversity features:
             - forecasters_std: Standard deviation across forecasters
             - forecasters_var: Variance across forecasters
             - forecasters_mean: Mean across forecasters

    Example::

        >>> df = pd.DataFrame({
        ...     'user1_q50': [10, 20, 30],
        ...     'user2_q50': [12, 22, 28],
        ...     'user1_q10': [5, 10, 15],
        ... })
        >>> diversity = create_diversity_features(df, quantile='q50')
        >>> # Returns DataFrame with std, var, mean across q50 forecasters
    """
    if df.empty:
        return pd.DataFrame(index=df.index)

    # Filter columns by quantile pattern if provided
    if quantile is not None:
        cols = [c for c in df.columns if quantile in c]
    else:
        cols = df.select_dtypes(include="number").columns.tolist()

    if not cols:
        return pd.DataFrame(index=df.index)

    subset = df[cols]

    # Calculate diversity metrics across forecasters (axis=1)
    diversity_features = pd.DataFrame(
        {
            "forecasters_std": subset.std(axis=1),
            "forecasters_var": subset.var(axis=1),
            "forecasters_mean": subset.mean(axis=1),
        },
        index=df.index,
    )

    # Replace any inf values with NaN
    diversity_features = diversity_features.replace([np.inf, -np.inf], np.nan)

    return diversity_features
