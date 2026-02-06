"""
ML Engine - Assessment and evaluation functions.

This module provides functions for evaluating forecaster performance
and creating assessment reports used by ensemble strategies.

The main functions are:
- validate_forecasters: Validates which forecasters submitted all required quantiles
- create_assessment_report: Evaluates forecaster skill scores
- calculate_ranking_per_date: Calculates daily ranking scores
"""

import pandas as pd
from loguru import logger

from .skills import (
    rmse_df,
    pinball_loss_df,
    mse_per_observation,
    pinball_loss_per_observation,
)


def validate_forecasters(
    forecast_range: pd.DatetimeIndex,
    df_market: pd.DataFrame,
    min_samples: int = 96 * 31,  # 1 month of 15-min data
) -> tuple[list[str], list[str]]:
    """
    Validate which forecasters submitted all required quantiles.

    This function performs validation only (no score computation):
    1. Identifies forecasters who submitted all quantiles (Q10, Q50, Q90)
    2. Filters to forecasters with sufficient historical data

    :param forecast_range: DatetimeIndex of forecast period
    :param df_market: DataFrame with market (forecaster) predictions
    :param min_samples: Minimum number of non-null samples required (default: 1 month)

    :return: Tuple of (valid_forecasters_list, forecasters_with_history)
        - valid_forecasters_list: List of forecasters who submitted all quantiles
        - forecasters_with_history: List of valid forecasters with sufficient
         history for the application of ensemble requiring training data
    """
    # Part 1: Ignore forecasters that did not submit Q10 / Q50 / Q90 forecasts
    forecast_data = df_market[forecast_range[0] : forecast_range[-1]].copy()
    complete_data = forecast_data.dropna(how="any", axis=1)

    def get_forecaster_ids(suffix: str) -> set[str]:
        return {
            col.split("_")[0] for col in complete_data.columns if col.endswith(suffix)
        }

    valid_forecasters = list(
        get_forecaster_ids("q50")
        & get_forecaster_ids("q10")
        & get_forecaster_ids("q90")
    )

    ignore_forecasters_list = [
        x for x in forecast_data.columns if x.split("_")[0] not in valid_forecasters
    ]
    if len(ignore_forecasters_list) > 0:
        logger.warning(
            f"Ignoring forecasters that did not submit all quantiles:\n"
            f"{ignore_forecasters_list}"
        )

    # Part 2: Get list of forecasters with sufficient historical data
    # Filter to columns belonging to valid forecasters that have enough samples
    sample_counts = df_market.notnull().sum()
    cols_with_history = sample_counts[sample_counts >= min_samples].index.tolist()
    forecasters_with_history = [
        col for col in cols_with_history if col.split("_")[0] in valid_forecasters
    ]

    return valid_forecasters, forecasters_with_history


def extract_quantile_columns(df: pd.DataFrame, quantile: str) -> pd.DataFrame:
    """Extract columns containing the specified quantile.

    :param df: DataFrame with forecaster prediction columns
    :param quantile: Quantile suffix to filter (e.g., 'q50', 'q10', 'q90')
    :return: DataFrame with only columns matching the quantile
    """
    columns = [name for name in df.columns if quantile in name]
    if columns:
        return df[columns]
    else:
        logger.warning(f"No columns found for {quantile}")
        return pd.DataFrame()


def calculate_ranking_per_date(df, quantile, seller_id):
    """
    Calculate daily ranking scores for a forecaster.

    :param df: DataFrame with 'observed' and 'forecast' columns
    :param quantile: Quantile name (e.g., 'q50', 'q10', 'q90')
    :param seller_id: Forecaster identifier

    :return: Series with daily mean scores indexed by date
    """
    df = df.copy()
    if quantile == "q50":
        obs_scores = mse_per_observation(df)
    else:
        obs_scores = pinball_loss_per_observation(df, quantile)

    df["scores"] = obs_scores
    df = df.tz_convert("Europe/Brussels")
    # Calculate daily mean scores:
    mean = df["scores"].groupby(df.index.date).mean()
    mean.name = seller_id
    return mean


def create_assessment_report(forecast_range, df_buyer, df_market, n_evaluation_days):
    """
    Create an assessment report evaluating forecaster performance.

    This function evaluates forecasters based on their recent submission
    history and calculates skill scores (RMSE for q50, Pinball loss for q10/q90).

    :param forecast_range: DatetimeIndex of forecast period
    :param df_buyer: DataFrame with buyer (target) data, must have 'target' column
    :param df_market: DataFrame with market (forecaster) predictions
    :param n_evaluation_days: Number of days to use for recent evaluation

    :return: Tuple of (assessment_report, valid_forecasters_list, forecasters_with_min_samples)
        - assessment_report: Dict with scores per quantile
        - valid_forecasters_list: List of forecasters who submitted all quantiles
        - forecasters_with_min_samples: List of forecasters with sufficient history
    """
    # Part 1: Ignore forecasters that did not submit Q10 / Q50 / Q90 forecasts for this session
    forecast_dataset = df_market[forecast_range[0] : forecast_range[-1]].copy()
    # Remove columns with missing values and get final list of forecasters:
    forecast_dataset_ = forecast_dataset.dropna(how="any", axis=1)
    forecasters_list_q50 = [
        x.split("_")[0] for x in forecast_dataset_.columns if x.endswith("q50")
    ]
    forecasters_list_q10 = [
        x.split("_")[0] for x in forecast_dataset_.columns if x.endswith("q10")
    ]
    forecasters_list_q90 = [
        x.split("_")[0] for x in forecast_dataset_.columns if x.endswith("q90")
    ]
    # Get list of valid forecasters (submitted all quantiles)
    valid_forecasters_list = list(
        set(forecasters_list_q50)
        .intersection(set(forecasters_list_q10))
        .intersection(set(forecasters_list_q90))
    )
    ignore_forecasters_list = [
        x
        for x in forecast_dataset.columns
        if x.split("_")[0] not in valid_forecasters_list
    ]
    if len(ignore_forecasters_list) > 0:
        logger.warning(
            f"Ignoring forecasters that did not submit all quantiles:\n{ignore_forecasters_list}"
        )

    # Part 2: Get list of variables with at least 1 month of not null samples:
    # Select forecasters with at least 1 month of not-null samples
    forecasters_with_min_samples = df_market.columns[
        df_market.notnull().sum() >= 96 * 31
    ].tolist()

    # Part 3: Evaluate forecasters that submitted all quantiles
    evaluation_period_start = forecast_range[0] - pd.DateOffset(days=n_evaluation_days)
    evaluation_period = pd.date_range(
        start=evaluation_period_start, periods=8 * 24 * 4, freq="15Min"
    )
    assessment_report = {}
    for quantile in ["q10", "q50", "q90"]:
        assessment_report[quantile] = {}
        df_market_qX = extract_quantile_columns(df_market, quantile)
        # Do not consider submissions from ignored Forecasters
        # due to missing quantile forecasts
        submissions_list = [
            x
            for x in df_market_qX.columns
            if not x.startswith(tuple(ignore_forecasters_list))
        ]
        # Prepare dataset for evaluation (specific for each quantile):
        # -- Note that we impute with zeros to penalize forecasters that
        # did not submit forecasts for this quantile on historical (no trust)
        dataset = df_buyer.join(df_market_qX).copy().dropna(subset=["target"]).fillna(0)
        # Remove from dataset forecasters that did not submit all quantiles
        dataset = dataset[
            ["target"]
            + [x for x in dataset.columns if x.split("_")[0] in valid_forecasters_list]
        ]

        # Prepare dictionary to store scores:
        scores_list = []
        recent_daily_scores = pd.DataFrame()
        for submission in submissions_list:
            # Get dataset just for the target and the submission:
            dataset_ = dataset[["target", submission]].copy()
            dataset_.rename(
                columns={"target": "observed", submission: "forecast"}, inplace=True
            )
            # Filter dataset to evaluation period (recent and past):
            recent_dataset_ = dataset_[
                evaluation_period[0] : evaluation_period[-1]
            ].copy()
            past_dataset_ = dataset_[: evaluation_period[0]].copy()
            # Rename columns - remove suffix:
            recent_dataset_.columns = [x.split("_")[0] for x in recent_dataset_.columns]
            past_dataset_.columns = [x.split("_")[0] for x in past_dataset_.columns]
            # Calculate scores (RMSE or Pinball Loss):
            recent_daily_scores_ = calculate_ranking_per_date(
                recent_dataset_, quantile, seller_id=submission
            )
            recent_daily_scores = pd.concat(
                [recent_daily_scores, recent_daily_scores_], axis=1
            )
            if quantile == "q50":
                recent_score = rmse_df(recent_dataset_)
                past_score = rmse_df(past_dataset_)
            else:
                recent_score = pinball_loss_df(recent_dataset_, quantile)
                past_score = pinball_loss_df(past_dataset_, quantile)

            # Store scores:
            scores_list.append(
                {
                    "submission": submission,
                    "recent_score": recent_score,
                    "past_score": past_score,
                    "n_recent_samples": len(recent_dataset_),
                    "n_past_samples": len(past_dataset_),
                }
            )

        # Create a dataframe of scores:
        scores_df = pd.DataFrame(scores_list)
        assessment_report[quantile]["scores"] = scores_df

    forecasters_with_min_samples = [
        x for x in forecasters_with_min_samples if x in valid_forecasters_list
    ]
    return assessment_report, valid_forecasters_list, forecasters_with_min_samples
