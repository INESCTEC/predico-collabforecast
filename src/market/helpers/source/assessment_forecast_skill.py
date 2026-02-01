import re
import numpy as np


def extract_quantile_reference(quantile_str):
    match = re.match(r'q(\d+)', quantile_str)
    if match:
        return float(match.group(1)) / 100
    else:
        raise ValueError("Invalid quantile string format")


def pinball_loss_df(df, q):
    """
    Calculate the pinball loss for quantile forecasts.

    Parameters:
    - df: pandas.DataFrame with columns 'value' (actual values) and 'forecast' (forecasted values)
    - q: float, the quantile to evaluate (between 0 and 1)

    Returns:
    - float, the mean pinball loss over the dataframe
    """
    obs_ = df['observed'].values.astype(np.float32)
    pred_ = df['forecast'].values.astype(np.float32)
    q_ = extract_quantile_reference(q)
    loss = np.where(obs_ > pred_, q_ * (obs_ - pred_), (1 - q_) * (pred_ - obs_))
    return round(float(loss.mean()), 3)


def rmse_df(df):
    """
    Calculate the Root Mean Square Error (RMSE) between actual values and forecasts.

    Parameters:
    - df: pandas.DataFrame with columns 'value' (actual values) and 'forecast' (forecasted values)

    Returns:
    - float, the RMSE over the dataframe
    """
    # Calculate the residuals (errors)
    errors = df['observed'] - df['forecast']
    # Compute Mean Squared Error (MSE)
    mse = np.mean(errors ** 2)
    # Return the square root of MSE (RMSE)
    return round(np.sqrt(mse), 3)


def mae_df(df):
    """
    Calculate the Mean Absolute Error (MAE) between actual values and forecasts.

    Parameters:
    - df: pandas.DataFrame with columns 'value' and 'forecast'

    Returns:
    - float, the MAE over the dataframe
    """
    return round(np.abs(df['observed'] - df['forecast']).mean(), 3)


def compute_forecasters_skill_scores(df_y_test, sellers_forecasts):
    """
    Compute forecast skill score metrics, for all the submissions in this challenge

    """
    score_dict = dict([(submission_id, {}) for submission_id in sellers_forecasts.keys()])
    score_dict["general"] = {}

    y_ = df_y_test.rename(columns={"value": "observed"})

    submission_scores = []
    for submission_id, forecast in sellers_forecasts.items():
        f_ = forecast.rename(columns={"value": "forecast"})
        dataset = f_.join(y_, how="left")
        variable = dataset["variable"].unique()[0]
        submission_id = str(submission_id)
        if variable == "q50":
            pinball_ = pinball_loss_df(df=dataset, q=variable)
            rmse_ = rmse_df(df=dataset)
            mae_ = mae_df(df=dataset)
            submission_scores.append({"submission": submission_id, "metric": "pinball", "value": pinball_})
            submission_scores.append({"submission": submission_id, "metric": "rmse", "value": rmse_})
            submission_scores.append({"submission": submission_id, "metric": "mae", "value": mae_})

        else:
            pinball_ = pinball_loss_df(df=dataset, q=variable)
            submission_scores.append({"submission": submission_id, "metric": "pinball", "value": pinball_})

    return submission_scores
