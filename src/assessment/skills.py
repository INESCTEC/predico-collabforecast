import re
from collections import defaultdict

import numpy as np
import pandas as pd

from loguru import logger


def extract_quantile_reference(quantile_str):
    match = re.match(r"q(\d+)", quantile_str)
    if match:
        return float(match.group(1)) / 100
    else:
        raise ValueError("Invalid quantile string format")


def pinball_loss_per_observation(df, q):
    obs_ = df["observed"].values.astype(np.float32)
    pred_ = df["forecast"].values.astype(np.float32)
    q_ = extract_quantile_reference(q)
    loss = np.where(obs_ > pred_, q_ * (obs_ - pred_), (1 - q_) * (pred_ - obs_))
    return loss


def pinball_loss_df(df, q):
    """
    Calculate the pinball loss for quantile forecasts.

    Parameters:
    - df: pandas.DataFrame with columns 'value' (actual values) and 'forecast' (forecasted values)
    - q: float, the quantile to evaluate (between 0 and 1)

    Returns:
    - float, the mean pinball loss over the dataframe (NaN if empty)
    """
    if df.empty:
        return float("nan")
    obs_ = df["observed"].values.astype(np.float32)
    pred_ = df["forecast"].values.astype(np.float32)
    if len(obs_) == 0 or len(pred_) == 0:
        return float("nan")
    q_ = extract_quantile_reference(q)
    loss = np.where(obs_ > pred_, q_ * (obs_ - pred_), (1 - q_) * (pred_ - obs_))
    return round(float(loss.mean()), 3)


def mse_per_observation(df):
    return (df["observed"] - df["forecast"]) ** 2


def winkler_per_observation(df):
    """
    Calculate the Winkler score for each row in a DataFrame that has
    the columns: 'observed', 'q10', and 'q90'.

    Parameters
    ----------
    - df: pandas.DataFrame with columns 'observed', 'q10', and 'q90'.

    Returns:
    - float: The mean Winkler score over the dataframe
    """
    alpha = 0.2  # 80% interval (10th and 90th quantiles)
    # 1. Base component: width of the interval
    w = df["q90"] - df["q10"]
    # 2. Penalty if observed < q10
    penalty_lower = (df["q10"] - df["observed"]).clip(lower=0)
    # 3. Penalty if observed > q90
    penalty_upper = (df["observed"] - df["q90"]).clip(lower=0)
    # 4. Add the penalization terms
    w = w + (2 / alpha) * penalty_lower + (2 / alpha) * penalty_upper
    return w


def winkler_df(df):
    if df.empty:
        return float("nan")
    w = winkler_per_observation(df)
    if len(w) == 0:
        return float("nan")
    return round(float(w.mean()), 3)


def rmse_df(df):
    """
    Calculate the Root Mean Square Error (RMSE) between actual values and forecasts.

    Parameters:
    - df: pandas.DataFrame with columns 'value' (actual values) and 'forecast' (forecasted values)

    Returns:
    - float, the RMSE over the dataframe (NaN if empty)
    """
    if df.empty:
        return float("nan")
    # Calculate the residuals (errors)
    errors = df["observed"] - df["forecast"]
    if len(errors) == 0:
        return float("nan")
    # Compute Mean Squared Error (MSE)
    mse = np.mean(errors**2)
    # Return the square root of MSE (RMSE)
    return round(np.sqrt(mse), 3)


def mse_boxplot_df(df):
    """
    Calculate the min, q1, median, q3, max and outliers of the RMSE values in the dataframe.

    Example:
        {
        "min": -35.2,
        "q1": -12.5,
        "median": 3.1,
        "q3": 18.4,
        "max": 48.7,
        "outliers": [-52.1, 61.3]
      }

    :param df: pandas.DataFrame with columns 'observed' and 'forecast'

    Returns:
        dict with the boxplot statistics
    """

    # Calculate the residuals (errors)
    mse_values = mse_per_observation(df).round(3)

    # Calculate boxplot statistics
    min_val = float(np.min(mse_values))
    q1 = float(np.percentile(mse_values, 25))
    median = float(np.median(mse_values))
    q3 = float(np.percentile(mse_values, 75))
    max_val = float(np.max(mse_values))
    # count number of samples
    n_samples = len(mse_values)

    # Important: we're not identifying outliers for the boxplots
    # as it would be a large overhead for large datasets

    return {
        "min": round(min_val, 3),
        "q1": round(q1, 3),
        "median": round(median, 3),
        "q3": round(q3, 3),
        "max": round(max_val, 3),
        "n_samples": n_samples,
    }


def winkler_boxplot_df(df):
    """
    Calculate the min, q1, median, q3, max and outliers of the Winkler scores in the dataframe.

    Example:
        {
        "min": 5.2,
        "q1": 12.5,
        "median": 23.1,
        "q3": 38.4,
        "max": 58.7,
        "outliers": [62.1, 71.3]
      }

    :param df: pandas.DataFrame with columns 'observed', 'q10', and 'q90'

    Returns:
        dict with the boxplot statistics
    """

    # Calculate Winkler scores
    winkler_scores = winkler_per_observation(df)

    # Calculate boxplot statistics
    min_val = float(np.min(winkler_scores))
    q1 = float(np.percentile(winkler_scores, 25))
    median = float(np.median(winkler_scores))
    q3 = float(np.percentile(winkler_scores, 75))
    max_val = float(np.max(winkler_scores))

    # Identify outliers using 1.5 * IQR rule
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    outliers = winkler_scores[
        (winkler_scores < lower_bound) | (winkler_scores > upper_bound)
    ].tolist()
    outliers = [float(x) for x in outliers]

    return {
        "min": round(min_val, 3),
        "q1": round(q1, 3),
        "median": round(median, 3),
        "q3": round(q3, 3),
        "max": round(max_val, 3),
        "outliers": outliers,
    }


def mae_df(df):
    """
    Calculate the Mean Absolute Error (MAE) between actual values and forecasts.

    Parameters:
    - df: pandas.DataFrame with columns 'value' and 'forecast'

    Returns:
    - float, the MAE over the dataframe (NaN if empty)
    """
    if df.empty:
        return float("nan")
    abs_errors = np.abs(df["observed"] - df["forecast"])
    if len(abs_errors) == 0:
        return float("nan")
    return round(abs_errors.mean(), 3)


def compute_forecasters_skill_scores(df_y_test, forecasts, forecast_id_col):
    """
    Compute forecast skill score metrics, for all the submissions or
    ensemble forecasts for a given challenge

    """
    if forecast_id_col not in ["submission", "ensemble"]:
        raise ValueError(
            "Invalid forecast_id_col. Must be either 'submission' or 'ensemble'"
        )

    score_dict = dict([(forecast_id, {}) for forecast_id in forecasts.keys()])
    score_dict["general"] = {}

    y_ = df_y_test.rename(columns={"value": "observed"})

    forecast_scores = []
    forecast_intervals_dict = defaultdict(pd.DataFrame)
    user_variable_submission_map = {}
    for forecast_id, forecast in forecasts.items():
        f_ = forecast.rename(columns={"value": "forecast"})
        dataset = f_.join(y_, how="left")
        variable = dataset["variable"].unique()[0]
        user_id = dataset["user_id"].unique()[0]
        forecast_id = str(forecast_id)

        if variable == "q50":
            pinball_ = pinball_loss_df(df=dataset, q=variable)
            rmse_ = rmse_df(df=dataset)
            mae_ = mae_df(df=dataset)
            forecast_scores.append(
                {forecast_id_col: forecast_id, "metric": "pinball", "value": pinball_}
            )
            forecast_scores.append(
                {forecast_id_col: forecast_id, "metric": "rmse", "value": rmse_}
            )
            forecast_scores.append(
                {forecast_id_col: forecast_id, "metric": "mae", "value": mae_}
            )
        else:
            pinball_ = pinball_loss_df(df=dataset, q=variable)
            forecast_scores.append(
                {forecast_id_col: forecast_id, "metric": "pinball", "value": pinball_}
            )
            if forecast_intervals_dict[user_id].empty:
                forecast_intervals_dict[user_id] = y_.join(
                    forecast.rename(columns={"value": variable})[[variable]], how="left"
                )
                user_variable_submission_map[user_id] = {variable: forecast_id}
            else:
                forecast_intervals_dict[user_id] = forecast_intervals_dict[
                    user_id
                ].join(
                    forecast.rename(columns={"value": variable})[[variable]], how="left"
                )
                user_variable_submission_map[user_id][variable] = forecast_id

    # Calculate winkler scores:
    for user_id, forecast_intervals in forecast_intervals_dict.items():
        if ("q90" not in forecast_intervals.columns) or (
            "q10" not in forecast_intervals.columns
        ):
            logger.warning(f"Skipped user {user_id} due to missing quantile forecasts.")
            continue
        winkler_ = winkler_df(forecast_intervals)
        forecast_scores.append(
            {
                forecast_id_col: user_variable_submission_map[user_id]["q10"],
                "metric": "winkler",
                "value": winkler_,
            }
        )
        forecast_scores.append(
            {
                forecast_id_col: user_variable_submission_map[user_id]["q90"],
                "metric": "winkler",
                "value": winkler_,
            }
        )

    return forecast_scores
