"""
Outlier detection utilities for forecast strategies.

This module provides reusable outlier detection functions that can be
shared across multiple ensemble strategies.

Example usage::

    from src.strategies.utils import detect_outliers_dtw

    # Detect outlier forecasters
    outliers = detect_outliers_dtw(forecasts_df, alpha=20.0)

    # Remove outliers before ensemble
    clean_forecasts = forecasts_df.drop(columns=outliers)
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def distance_based_outlier_detection(
    df: pd.DataFrame,
    base_profile: np.ndarray,
    distance: str = "dtw",
    alpha: float = 1.5,
) -> list[str]:
    """
    Detect outlier forecast profiles using distance-based detection.

    Computes the distance from each forecaster's profile to a reference
    profile (typically the median), then identifies outliers using
    MAD-based thresholding.

    :param df: DataFrame with forecaster predictions as columns
    :param base_profile: Reference profile (typically median)
    :param distance: Distance metric ("dtw" or "euclidean")
    :param alpha: MAD multiplier for threshold (higher = fewer outliers)

    :return: List of column names identified as outliers
    """
    if distance == "dtw":
        from dtaidistance import dtw

        distances = [dtw.distance(df[x].values, base_profile) for x in df.columns]
    elif distance == "euclidean":
        distances = [np.linalg.norm(df[x].values - base_profile) for x in df.columns]
    else:
        raise ValueError(f"Unknown distance metric: {distance}")

    # MAD-based threshold
    median_dist = np.median(distances)
    abs_dev = np.abs(distances - median_dist)
    mad = np.median(abs_dev)
    threshold = median_dist + alpha * mad

    return [col for col, d in zip(df.columns, distances) if d > threshold]


def detect_outliers_dtw(
    df: pd.DataFrame,
    alpha: float = 20.0,
    min_forecasters: int = 4,
) -> list[str]:
    """
    Detect outlier forecast profiles using Dynamic Time Warping distance.

    Normalizes all profiles to a common scale and identifies profiles
    that deviate significantly from the median profile using DTW distance
    and MAD-based thresholding.

    This function is extracted from WeightedAverageStrategy for reuse
    across online learning strategies.

    :param df: DataFrame with forecaster predictions as columns.
        Index should be DatetimeIndex, columns are forecaster IDs.
    :param alpha: MAD multiplier for threshold (default: 20.0).
        Higher values result in fewer outliers detected.
    :param min_forecasters: Minimum number of forecasters required
        to run outlier detection. If fewer forecasters are present,
        returns an empty list. Default is 4.

    :return: List of column names identified as outliers

    Example::

        forecasts = pd.DataFrame({
            "s1_q50": [100, 105, 110],
            "s2_q50": [102, 107, 112],
            "s3_q50": [500, 510, 520],  # Outlier
        })

        outliers = detect_outliers_dtw(forecasts, alpha=20.0)
        # Returns: ["s3_q50"]
    """
    if df.shape[1] < min_forecasters:
        return []

    df = df.copy()

    # Normalize all features according to global min/max
    min_val = df.min().min()
    max_val = df.max().max()

    if max_val - min_val == 0:
        # All values are the same, no outliers
        return []

    ref_df = (df - min_val) / (max_val - min_val)

    # Calculate median profile as reference
    base_arr = ref_df.median(axis=1).values

    # Find outliers using DTW distance
    outliers = distance_based_outlier_detection(
        ref_df, base_arr, distance="dtw", alpha=alpha
    )

    return outliers
