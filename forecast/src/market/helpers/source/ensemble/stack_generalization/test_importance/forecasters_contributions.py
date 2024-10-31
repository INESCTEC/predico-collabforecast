import pandas as pd

from loguru import logger
from collections import defaultdict

from .first_stage_importance import wind_power_importance
from .second_stage_importance import wind_power_variability_importance
from ....utils.session_ml_info import set_prediction_timestamps


def calculate_contributions(results_challenge_dict, ens_params, df_y_test, forecast_range):
    """Calculate the contributions of the models in the ensemble.
    Args:
        results_challenge_dict: Dictionary with the results of the challenge
        ens_params: Dictionary with the ensemble parameters
        df_y_test: DataFrame with the true values
        forecast_range: Dictionary with the forecast range
    Returns:
        results_contributions: Dictionary with the contributions of the forecasters
    """
    assert isinstance(results_challenge_dict, dict), 'The results_challenge_dict must be a dictionary'
    assert isinstance(ens_params, dict), 'The ens_params must be a dictionary'
    assert isinstance(df_y_test, pd.DataFrame), 'The df_y_test must be a DataFrame'
    results_contributions = defaultdict(dict)
    # Set the launch time and forecast range
    timestamps = set_prediction_timestamps(forecast_range)
    start_prediction_timestamp = timestamps['start_prediction_timestamp']
    end_prediction_timestamp = timestamps['end_prediction_timestamp']
    try:
        # wind power importance
        y_test_1st_stage = df_y_test[(df_y_test.index >= start_prediction_timestamp) & (df_y_test.index <= end_prediction_timestamp)].values
        assert len(y_test_1st_stage) >= 92, 'The length of the test set must be at least 92'
        assert len(y_test_1st_stage) <= 100, 'The length of the test set must be at most 100'
        results_contributions = wind_power_importance(results_challenge_dict, ens_params, y_test_1st_stage, results_contributions)
        # wind power ramp importance
        y_test_2nd_stage = df_y_test[(df_y_test.index >= start_prediction_timestamp) & (df_y_test.index <= end_prediction_timestamp)].values
        assert len(y_test_2nd_stage) >= 92, 'The length of the test set must be at least 92'
        assert len(y_test_2nd_stage) <= 100, 'The length of the test set must be at most 100'
        results_contributions = wind_power_variability_importance(results_challenge_dict, ens_params, y_test_2nd_stage, forecast_range, results_contributions)
    except Exception as e:
        logger.error(f"Failed to calculate contributions: {e}")
    return results_contributions
