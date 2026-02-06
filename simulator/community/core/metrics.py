"""
Evaluation metrics for forecast skill assessment.

This module provides functions for calculating forecast accuracy metrics:
- RMSE (Root Mean Square Error) - for deterministic forecasts
- MAE (Mean Absolute Error) - for deterministic forecasts
- Pinball Loss - for quantile/probabilistic forecasts
- Winkler Score - for prediction intervals

All metric functions expect DataFrames with specific column names:
- 'observed': Actual measured values
- 'forecast': Predicted values
- 'q10', 'q90': Quantile bounds (for Winkler score)

Example:
    >>> from core.metrics import rmse, pinball_loss, winkler_score
    >>> df = pd.DataFrame({
    ...     'observed': [100, 110, 105],
    ...     'forecast': [98, 112, 103],
    ... })
    >>> print(f"RMSE: {rmse(df):.3f}")
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd


def _extract_quantile_value(quantile_str: str) -> float:
    """Extract numeric quantile value from string format.

    :param quantile_str: Quantile string like "q10", "q50", "q90"
    :return: Quantile value between 0 and 1 (e.g., 0.1, 0.5, 0.9)

    :raises ValueError: If the string format is invalid
    """
    match = re.match(r"q(\d+)", quantile_str.lower())
    if match:
        return float(match.group(1)) / 100
    raise ValueError(
        f"Invalid quantile string format: '{quantile_str}'. "
        f"Expected format: 'q10', 'q50', 'q90', etc."
    )


def rmse(df: pd.DataFrame) -> float:
    """Calculate Root Mean Square Error (RMSE).

    RMSE measures the average magnitude of forecast errors, giving
    higher weight to large errors.

    :param df: DataFrame with 'observed' and 'forecast' columns
    :return: RMSE value (rounded to 3 decimal places)

    :raises KeyError: If required columns are missing

    Example:
        >>> df = pd.DataFrame({'observed': [100, 110], 'forecast': [98, 112]})
        >>> rmse(df)
        2.828
    """
    errors = df["observed"] - df["forecast"]
    mse = np.mean(errors**2)
    return round(float(np.sqrt(mse)), 3)


def mae(df: pd.DataFrame) -> float:
    """Calculate Mean Absolute Error (MAE).

    MAE measures the average magnitude of forecast errors without
    considering direction.

    :param df: DataFrame with 'observed' and 'forecast' columns
    :return: MAE value (rounded to 3 decimal places)

    :raises KeyError: If required columns are missing

    Example:
        >>> df = pd.DataFrame({'observed': [100, 110], 'forecast': [98, 112]})
        >>> mae(df)
        2.0
    """
    return round(float(np.abs(df["observed"] - df["forecast"]).mean()), 3)


def mse(df: pd.DataFrame) -> float:
    """Calculate Mean Squared Error (MSE).

    :param df: DataFrame with 'observed' and 'forecast' columns
    :return: MSE value (rounded to 3 decimal places)
    """
    errors = df["observed"] - df["forecast"]
    return round(float(np.mean(errors**2)), 3)


def pinball_loss(
    df: pd.DataFrame,
    quantile: str | float,
    per_observation: bool = False,
) -> float | pd.Series:
    """Calculate Pinball Loss for quantile forecasts.

    The pinball loss (also called quantile loss) is an asymmetric loss
    function that penalizes over-predictions and under-predictions
    differently based on the target quantile.

    Formula:
        If observed > forecast: q * (observed - forecast)
        If observed <= forecast: (1 - q) * (forecast - observed)

    :param df: DataFrame with 'observed' and 'forecast' columns
    :param quantile: Target quantile as string ("q10", "q50", "q90") or float (0.1, 0.5, 0.9)
    :param per_observation: If True, return Series of per-observation losses

    :return: Mean pinball loss (float) or per-observation Series

    :raises KeyError: If required columns are missing
    :raises ValueError: If quantile format is invalid

    Example:
        >>> df = pd.DataFrame({'observed': [100, 110], 'forecast': [98, 112]})
        >>> pinball_loss(df, "q50")
        1.0
    """
    # Parse quantile value
    if isinstance(quantile, str):
        q = _extract_quantile_value(quantile)
    else:
        q = float(quantile)

    obs = df["observed"].values.astype(np.float32)
    pred = df["forecast"].values.astype(np.float32)

    # Calculate pinball loss
    loss = np.where(obs > pred, q * (obs - pred), (1 - q) * (pred - obs))

    if per_observation:
        return pd.Series(index=df.index, data=loss, name="pinball_loss")

    return round(float(loss.mean()), 3)


def winkler_score(
    df: pd.DataFrame,
    alpha: float = 0.2,
    per_observation: bool = False,
) -> float | pd.Series:
    """Calculate Winkler Interval Score.

    The Winkler score evaluates prediction intervals by combining:
    1. The width of the interval (narrower is better)
    2. A penalty for observations falling outside the interval

    For the default alpha=0.2, this evaluates the 80% prediction interval
    (10th to 90th percentile).

    Formula:
        score = (q90 - q10) + (2/alpha) * penalty_lower + (2/alpha) * penalty_upper
        where:
            penalty_lower = max(0, q10 - observed) if observed < q10
            penalty_upper = max(0, observed - q90) if observed > q90

    :param df: DataFrame with 'observed', 'q10', and 'q90' columns
    :param alpha: Significance level (default: 0.2 for 80% interval)
    :param per_observation: If True, return Series of per-observation scores

    :return: Mean Winkler score (float) or per-observation Series

    :raises KeyError: If required columns are missing

    Example:
        >>> df = pd.DataFrame({
        ...     'observed': [100, 110, 150],
        ...     'q10': [90, 100, 110],
        ...     'q90': [110, 120, 130],
        ... })
        >>> winkler_score(df)
        30.0  # Includes penalty for 150 being outside [110, 130]
    """
    # Base component: interval width
    width = df["q90"] - df["q10"]

    # Penalty for observations below q10
    penalty_lower = (df["q10"] - df["observed"]).clip(lower=0)

    # Penalty for observations above q90
    penalty_upper = (df["observed"] - df["q90"]).clip(lower=0)

    # Combine components
    score = width + (2 / alpha) * penalty_lower + (2 / alpha) * penalty_upper

    if per_observation:
        return score.rename("winkler_score")

    return round(float(score.mean()), 3)


def mse_per_observation(df: pd.DataFrame) -> pd.Series:
    """Calculate per-observation Mean Squared Error.

    :param df: DataFrame with 'observed' and 'forecast' columns
    :return: Series of squared errors
    """
    return ((df["observed"] - df["forecast"]) ** 2).rename("mse")


def compute_skill_scores(
    observations: pd.DataFrame,
    forecasts: dict[str, pd.DataFrame],
    metrics: list[str] | None = None,
) -> list[dict]:
    """Compute forecast skill scores for multiple forecasters.

    :param observations: DataFrame with 'value' column and datetime index
    :param forecasts: Dictionary mapping forecaster_id to forecast DataFrame
        Each forecast DataFrame should have 'value' and 'variable' columns
    :param metrics: List of metrics to compute (default: all applicable)
        Options: "rmse", "mae", "pinball", "mse"

    :return: List of score dictionaries with keys:
        - forecaster_id: Forecaster identifier
        - metric: Metric name
        - value: Computed metric value
        - variable: Forecast variable (q10, q50, q90)

    Example:
        >>> scores = compute_skill_scores(
        ...     observations=obs_df,
        ...     forecasts={"forecaster_1": fc_df},
        ... )
        >>> for s in scores:
        ...     print(f"{s['forecaster_id']}: {s['metric']}={s['value']}")
    """
    if metrics is None:
        metrics = ["rmse", "mae", "pinball"]

    # Prepare observations
    y = observations.rename(columns={"value": "observed"})

    scores = []
    for forecaster_id, forecast in forecasts.items():
        # Prepare forecast data
        f = forecast.rename(columns={"value": "forecast"})
        dataset = f.join(y, how="left")

        # Get variable type
        variable = dataset["variable"].unique()[0] if "variable" in dataset else "q50"

        # Compute applicable metrics
        if variable == "q50":
            # Deterministic metrics
            if "rmse" in metrics:
                scores.append(
                    {
                        "forecaster_id": str(forecaster_id),
                        "metric": "rmse",
                        "value": rmse(dataset),
                        "variable": variable,
                    }
                )
            if "mae" in metrics:
                scores.append(
                    {
                        "forecaster_id": str(forecaster_id),
                        "metric": "mae",
                        "value": mae(dataset),
                        "variable": variable,
                    }
                )
            if "pinball" in metrics:
                scores.append(
                    {
                        "forecaster_id": str(forecaster_id),
                        "metric": "pinball",
                        "value": pinball_loss(dataset, variable),
                        "variable": variable,
                    }
                )
        else:
            # Quantile metrics
            if "pinball" in metrics:
                scores.append(
                    {
                        "forecaster_id": str(forecaster_id),
                        "metric": "pinball",
                        "value": pinball_loss(dataset, variable),
                        "variable": variable,
                    }
                )

    return scores


# Convenience aliases for backward compatibility
rmse_df = rmse
mae_df = mae
pinball_loss_df = pinball_loss
winkler_df = winkler_score
