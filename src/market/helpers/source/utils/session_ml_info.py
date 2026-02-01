import os
import pickle
import pandas as pd

from pathlib import Path


def load_or_initialize_results(params, challenge_id):
    """Load or initialize results for the ensemble learning.
    Args:
        params (dict): dictionary with the parameters for the ensemble learning.
        challenge_id (int): challenge id.
    Returns:
        file_info (str): file name.
        iteration (int): iteration number.
        best_results (dict): best results for the wind power.
    """

    # check if file with model info exists
    file_name = 'wp_' + params['model_type'] + '_wpr_' + params['var_model_type'] + '.pickle'
    file_info = os.path.join(params['save_info'], str(challenge_id))
    os.makedirs(file_info, exist_ok=True)
    file_info = os.path.join(file_info, file_name)

    file_path = Path(file_info)  # file path
    # Load or initialize results
    if file_path.is_file():  # file exists
        with open(file_info, 'rb') as handle:
            results_challenge_dict = pickle.load(handle)
        iteration = results_challenge_dict['iteration'] + 1
        best_results = results_challenge_dict['wind_power']['best_results']
        best_results_var = results_challenge_dict['wind_power_ramp']['best_results']
    else:
        iteration = 0
        best_results = {}
        best_results_var = {}
    return file_info, iteration, best_results, best_results_var

def get_buyer_resource_name(df):
    """
    Returns buyer resource name.
    """
    assert df.shape[1] == 1
    return df.columns[0]

def set_timestamps(launch_time, forecast_range, utc):
    """
    Sets the timestamps for the end of observation and the start and end of predictions.
    Args:   
        launch_time (datetime): launch time.
        forecast_range (list): forecast range.
        utc (pytz): Coordinated Universal Time.
    Returns:
        dict: dictionary with the timestamps.
    """
    # Set timestamps
    end_observation_timestamp = pd.to_datetime(min(launch_time.replace(tzinfo=utc), forecast_range[0].replace(tzinfo=utc)), utc=True)
    start_prediction_timestamp = forecast_range[0]
    end_prediction_timestamp = forecast_range[-1]
    return {
        'end_observation_timestamp': end_observation_timestamp,
        'start_prediction_timestamp': start_prediction_timestamp,
        'end_prediction_timestamp': end_prediction_timestamp
    }


def set_prediction_timestamps(forecast_range):
    """
    Sets the timestamps for the end of observation and the start and end of predictions.
    """
    # Set timestamps
    start_prediction_timestamp = forecast_range[0]
    end_prediction_timestamp = forecast_range[-1]
    prev_day_start_prediction_timestamp = forecast_range[0] - pd.Timedelta('1day')
    return {
        'prev_day_start_prediction_timestamp': prev_day_start_prediction_timestamp,
        'start_prediction_timestamp': start_prediction_timestamp,
        'end_prediction_timestamp': end_prediction_timestamp
    }


