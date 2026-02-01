import numpy as np
import pandas as pd

from loguru import logger


def scale(df, col_name, max_cap):
    " Scale a column by dividing by maximum capacity"
    assert max_cap > 0, "Maximum capacity must be greater than 0"
    df_ = df.copy()
    values = df_[col_name].values
    return values/max_cap

def get_maximum_values(df, end_train, buyer_resource_name=None):
    " Get the maximum values for the buyer resource and forecasters"
    assert isinstance(df, pd.DataFrame), 'df must be a DataFrame'
    assert buyer_resource_name is None or isinstance(buyer_resource_name, str), 'buyer_resource_name must be a string or None'
    # Check if the DataFrame indices are datetime types
    if not pd.api.types.is_datetime64_any_dtype(df.index):
        raise TypeError("The df index must be a datetime type.")
    if buyer_resource_name is not None:
        # get the maximum capacity for the buyer resource
        maximum_capacity_buyer = df[df.index < end_train][buyer_resource_name].max()
        return maximum_capacity_buyer
    else:
        # Get the maximum values for forecasters
        list_maximum_values_forecasters = df[df.index < end_train].max(axis=0).values
        return list_maximum_values_forecasters
    
def normalize_dataframe(df, axis=1, max_cap=None, max_cap_forecasters_list=None):
    " Normalize dataframe by dividing by maximum capacity"
    df_normalized = df.copy()
    if axis==1:
        assert max_cap is not None, "Maximum capacity must be provided"
        for col in df_normalized.columns:
            normalize_col = scale(df_normalized, col, max_cap)
            df_normalized[f'norm_{col}'] = normalize_col
        return df_normalized.filter(like='norm')
    elif axis==0:
        assert max_cap_forecasters_list is not None, "List of maximum capacities must be provided"
        for i, col in enumerate(df_normalized.columns):
            max_cap_forecaster = max_cap_forecasters_list[i]
            normalize_col = scale(df_normalized, col, max_cap_forecaster)
            df_normalized[f'norm_{col}'] = normalize_col
        return df_normalized.filter(like='norm')
    else:
        raise ValueError("Axis must be either 0 or 1")
    
def rescale_normalized_predictions(predictions, quantile, maximum_capacity):
    " Rescale normalized predictions"
    assert maximum_capacity > 0, "Maximum capacity must be greater than 0"
    assert quantile in predictions.keys(), "Quantile must be in the predictions keys"
    assert isinstance(predictions[quantile], np.ndarray), "Predictions must be a numpy array"
    return predictions[quantile] * maximum_capacity

def rescale_normalized_targets(df, target_name, maximum_capacity):
    "Rescale normalized targets"
    assert target_name in df.columns, f'{target_name} must be in the columns of the dataframe'
    return df[target_name] * maximum_capacity


def standard_scale(df, col_name, mean, std):
    " Scale a column by dividing by maximum capacity"
    df_ = df.copy()
    values = df_[col_name].values
    return (values - mean)/std

def get_mean_std_values(df, end_train, buyer_resource_name=None):
    "Get the mean, std values for the buyer resource and forecasters"
    assert isinstance(df, pd.DataFrame), 'df must be a DataFrame'
    assert buyer_resource_name is None or isinstance(buyer_resource_name, str), 'buyer_resource_name must be a string or None'
    # Check if the DataFrame indices are datetime types
    if not pd.api.types.is_datetime64_any_dtype(df.index):
        raise TypeError("The df index must be a datetime type.")
    if buyer_resource_name is not None:
        # get the mean, std for the buyer resource
        mean_buyer = df[df.index < end_train][buyer_resource_name].mean()
        std_buyer = df[df.index < end_train][buyer_resource_name].std()
        return mean_buyer, std_buyer
    else:
        # Get the mean values for forecasters
        list_mean_values_forecasters = df[df.index < end_train].mean(axis=0).values
        list_std_values_forecasters = df[df.index < end_train].std(axis=0).values
        return list_mean_values_forecasters, list_std_values_forecasters

def standardize_dataframe(df, axis=1, mean_buyer=None, std_buyer=None, mean_forecasters_list=None, std_forecasters_list=None):
    " Standardize dataframe by subtracting the mean and dividing by the standard deviation"
    df_standardized = df.copy()
    if axis==1:
        assert mean_buyer is not None, "Mean values must be provided"
        assert std_buyer is not None, "Std values must be provided"
        for col in df_standardized.columns:
            standardize_col = standard_scale(df_standardized, col, mean_buyer, std_buyer)
            df_standardized[f'norm_{col}'] = standardize_col
        return df_standardized.filter(like='norm')
    elif axis==0:
        assert mean_forecasters_list is not None, "List of mean values must be provided"
        assert std_forecasters_list is not None, "List of std values must be provided"
        for i, col in enumerate(df_standardized.columns):
            mean_forecaster = mean_forecasters_list[i]
            std_forecaster = std_forecasters_list[i]
            standardize_col = standard_scale(df_standardized, col, mean_forecaster, std_forecaster)
            df_standardized[f'norm_{col}'] = standardize_col
        return df_standardized.filter(like='norm')
    else:
        raise ValueError("Axis must be either 0 or 1")

def rescale_standardized_predictions(predictions, quantile, mean, std, stage = '1st'):
    " Rescale standardized predictions"
    assert mean is not None, "Mean values must be provided"
    assert std is not None, "Std values must be provided"
    assert quantile in predictions.keys(), "Quantile must be in the predictions keys"
    assert isinstance(predictions[quantile], np.ndarray), "Predictions must be a numpy array"
    if stage == '1st':
        return (predictions[quantile] * std) + mean
    elif stage == '2nd':
        return predictions[quantile] * std
    else:
        raise ValueError("Stage must be either '1st' or '2nd'")
    
def rescale_standardized_targets(df, target_name, mean, std, stage = '1st'):
    " Rescale standardized targets"
    assert mean is not None, "Mean values must be provided"
    assert std is not None, "Std values must be provided"
    assert target_name in df.columns, "Target name must be in the DataFrame columns"
    if stage == '1st':
        return (df[target_name] * std) + mean
    elif stage == '2nd':
        return df[target_name] * std
    else:
        raise ValueError("Stage must be either '1st' or '2nd'")
    

def buyer_scaler_statistics(ens_params, df_buyer, end_training_timestamp, buyer_resource_name):
    " Compute statistics for buyer resource scaler"
    assert ens_params['scale_features'], 'scale_features must be True'
    assert ens_params['normalize'] or ens_params['standardize'], 'normalize or standardize must be True'
    assert end_training_timestamp is not None, 'end_training_timestamp must be provided'
    stats = {}
    # Get maximum capacity
    if ens_params['scale_features'] and ens_params['normalize']:
        maximum_capacity = get_maximum_values(df=df_buyer, end_train=end_training_timestamp, buyer_resource_name=buyer_resource_name)
        logger.opt(colors=True).info(f'<fg 250,128,114> Maximum Capacity: {maximum_capacity} </fg 250,128,114>')
        stats['maximum_capacity'] = maximum_capacity
    # Get mean and std values
    elif ens_params['scale_features'] and ens_params['standardize']:
        mean_buyer, std_buyer = get_mean_std_values(df=df_buyer, end_train=end_training_timestamp, buyer_resource_name=buyer_resource_name)
        logger.opt(colors=True).info(f'<fg 250,128,114> Mean Buyer: {mean_buyer} </fg 250,128,114>')
        logger.opt(colors=True).info(f'<fg 250,128,114> Std Buyer: {std_buyer} </fg 250,128,114>')
        stats['mean_buyer'] = mean_buyer
        stats['std_buyer'] = std_buyer
    logger.info('  ')
    return stats


def scale_forecasters_dataframe(ens_params, stats, df_ensemble_quantile50, df_ensemble_quantile10, df_ensemble_quantile90, end_training_timestamp):
    """
    Normalize or standardize the dataframes based on the given ensemble parameters.
    """
    # Extract statistics
    maximum_capacity = stats.get('maximum_capacity', None)
    mean_buyer = stats.get('mean_buyer', None)
    std_buyer = stats.get('std_buyer', None)

    # Initialize dataframes
    df_ensemble_normalized = pd.DataFrame()
    df_ensemble_normalized_quantile10 = pd.DataFrame()
    df_ensemble_normalized_quantile90 = pd.DataFrame()

    # Normalize dataframes
    if ens_params['scale_features'] and ens_params['normalize']:
        logger.info('   ')
        logger.opt(colors=True).info(f'<fg 250,128,114> Normalize DataFrame </fg 250,128,114>')
        list_max_forecasters_q50 = get_maximum_values(df=df_ensemble_quantile50, end_train=end_training_timestamp)
        df_ensemble_normalized = normalize_dataframe(df_ensemble_quantile50, axis=ens_params['axis'], max_cap=maximum_capacity, max_cap_forecasters_list=list_max_forecasters_q50)
        if ens_params['add_quantile_predictions']:
            logger.opt(colors=True).info(f'<fg 250,128,114> -- Add quantile predictions </fg 250,128,114>')
            # Get maximum values for quantile predictions
            if not df_ensemble_quantile10.empty:
                list_max_forecasters_q10 = get_maximum_values(df=df_ensemble_quantile10, end_train=end_training_timestamp)
            else:
                list_max_forecasters_q10 = []
            if not df_ensemble_quantile90.empty:
                list_max_forecasters_q90 = get_maximum_values(df=df_ensemble_quantile90, end_train=end_training_timestamp)
            else:
                list_max_forecasters_q90 = []
            df_ensemble_normalized_quantile10 = normalize_dataframe(df_ensemble_quantile10, axis=ens_params['axis'], 
                                                                    max_cap=maximum_capacity, max_cap_forecasters_list=list_max_forecasters_q10) 
            df_ensemble_normalized_quantile90 = normalize_dataframe(df_ensemble_quantile90, axis=ens_params['axis'], 
                                                                    max_cap=maximum_capacity, max_cap_forecasters_list=list_max_forecasters_q90)
        else:
            df_ensemble_normalized_quantile10 = df_ensemble_normalized_quantile90 = None 
    # Standardize dataframes
    elif ens_params['scale_features'] and ens_params['standardize']:
        logger.info('   ')
        logger.opt(colors=True).info(f'<fg 250,128,114> Standardize DataFrame </fg 250,128,114>')
        mean_forecasters_q50, std_forecasters_q50 = get_mean_std_values(df=df_ensemble_quantile50, end_train=end_training_timestamp)
        df_ensemble_normalized = standardize_dataframe(df_ensemble_quantile50, axis=ens_params['axis'], mean_buyer=mean_buyer, std_buyer=std_buyer, mean_forecasters_list=mean_forecasters_q50, std_forecasters_list=std_forecasters_q50)
        if ens_params['add_quantile_predictions']:
            logger.opt(colors=True).info(f'<fg 250,128,114> -- Add quantile predictions </fg 250,128,114>')
            if not df_ensemble_quantile10.empty:
                mean_forecasters_q10, std_forecasters_q10 = get_mean_std_values(df=df_ensemble_quantile10, end_train=end_training_timestamp)
            else:
                mean_forecasters_q10, std_forecasters_q10 = [], []
            if not df_ensemble_quantile90.empty:
                mean_forecasters_q90, std_forecasters_q90 = get_mean_std_values(df=df_ensemble_quantile90, end_train=end_training_timestamp)
            else:
                mean_forecasters_q90, std_forecasters_q90 = [], []
            df_ensemble_normalized_quantile10 = standardize_dataframe(df_ensemble_quantile10, axis=ens_params['axis'], mean_buyer=mean_buyer, std_buyer=std_buyer, 
                                                                        mean_forecasters_list=mean_forecasters_q10, std_forecasters_list=std_forecasters_q10) 
            df_ensemble_normalized_quantile90 = standardize_dataframe(df_ensemble_quantile90, axis=ens_params['axis'], mean_buyer=mean_buyer, std_buyer=std_buyer, 
                                                                        mean_forecasters_list=mean_forecasters_q90, std_forecasters_list=std_forecasters_q90)
        else:
            df_ensemble_normalized_quantile10 = df_ensemble_normalized_quantile90 = None 
    # If no scaling is applied, simply copy and prefix dataframes
    else:
        df_ensemble_normalized = df_ensemble_quantile50.copy().add_prefix('norm_')
        if ens_params['add_quantile_predictions']:
            df_ensemble_normalized_quantile10 = df_ensemble_quantile10.copy().add_prefix('norm_') 
            df_ensemble_normalized_quantile90 = df_ensemble_quantile90.copy().add_prefix('norm_')
        else:
            df_ensemble_normalized_quantile10 = df_ensemble_normalized_quantile90 = None 
    return df_ensemble_normalized, df_ensemble_normalized_quantile10, df_ensemble_normalized_quantile90


def scale_buyer_dataframe(ens_params, stats, df_buyer):
    """
    Normalize or standardize the buyer dataframe based on the given ensemble parameters.
    """
    maximum_capacity = stats.get('maximum_capacity', None)
    mean_buyer = stats.get('mean_buyer', None)
    std_buyer = stats.get('std_buyer', None)

    if ens_params['scale_features'] and ens_params['normalize']:
        list_max_buyer = [maximum_capacity]
        df_buyer_norm = normalize_dataframe(df_buyer, axis=ens_params['axis'], max_cap=maximum_capacity, max_cap_forecasters_list=list_max_buyer)
    elif ens_params['scale_features'] and ens_params['standardize']:
        list_mean_buyer, list_std_buyer = [mean_buyer], [std_buyer]
        df_buyer_norm = standardize_dataframe(df_buyer, axis=ens_params['axis'], mean_buyer=mean_buyer, std_buyer=std_buyer, mean_forecasters_list=list_mean_buyer, std_forecasters_list=list_std_buyer)
    else:
        df_buyer_norm = df_buyer.copy()
        df_buyer_norm = df_buyer_norm.add_prefix('norm_')
    return df_buyer_norm


def rescale_predictions(predictions, ens_params, stats, quantile, stage):
    """
    Rescale predictions by normalizing or standardizing them based on the given ensemble parameters.
    """
    # Extract statistics
    maximum_capacity = stats.get('maximum_capacity', None)
    mean_buyer = stats.get('mean_buyer', None)
    std_buyer = stats.get('std_buyer', None)
    # Normalize predictions
    if ens_params['scale_features'] and ens_params['normalize']:
        predictions[quantile] = rescale_normalized_predictions(predictions, quantile, maximum_capacity)
    # Standardize predictions
    elif ens_params['scale_features'] and ens_params['standardize']:
        predictions[quantile] = rescale_standardized_predictions(predictions, quantile, mean_buyer, std_buyer, stage=stage)
    return predictions

def rescale_targets(ens_params, stats, df, target_name, stage):
    """
    Rescale targets by normalizing or standardizing them based on the given ensemble parameters.
    """
    maximum_capacity = stats.get('maximum_capacity', None)
    mean_buyer = stats.get('mean_buyer', None)
    std_buyer = stats.get('std_buyer', None)
    # Normalize targets
    if ens_params['scale_features'] and ens_params['normalize']:
        df.loc[:, 'targets'] = rescale_normalized_targets(df, target_name, maximum_capacity)
    # Standardize targets
    elif ens_params['scale_features'] and ens_params['standardize']:
        df.loc[:, 'targets'] = rescale_standardized_targets(df, target_name, mean_buyer, std_buyer, stage=stage)
    else:
        df.loc[:, 'targets'] = df[target_name]
    return df

def set_non_negative_predictions(predictions, quantile):
    """
    Ensures that all values in the specified quantile of predictions are non-negative.
    """
    if quantile in predictions:
        predictions[quantile] = np.maximum(predictions[quantile], 0)
    else:
        raise KeyError(f"Quantile '{quantile}' not found in predictions.")
    return predictions

def drop_nans_with_warning(df):
    """
    Drops NaNs from the DataFrame and logs a warning if NaNs are found.
    """
    if df.isna().sum().sum() > 0:
        logger.warning('Dropping NaNs in the DataFrame.')
        df.dropna(inplace=True)
    return df

def check_minimum_data_training(df, minimum_rows):
    """
    Checks if the DataFrame has enough data and logs an error if it does not.
    """
    if df.shape[0] < minimum_rows:
        logger.error(f'Not enough data to train the model. Please provide at least {minimum_rows} days of data.')
        raise Exception('Not enough data to train the model.')
    return df


def extract_quantile_data(df, quantile_markers):
    """
    Extracts columns from a DataFrame based on quantile markers and returns them as separate DataFrames.
    """
    dataframes = []
    for marker in quantile_markers:
        filtered_df = df[[col for col in df.columns if marker in col]]
        dataframes.append(filtered_df)
    return tuple(dataframes)

def impute_mean_for_nan(df):
    """
    Imputes the mean for NaN values in each column of a DataFrame.
    Args:
        df (pd.DataFrame): The DataFrame in which to impute mean for NaN values.
    Returns:
        df (pd.DataFrame): The DataFrame with NaN values replaced by the column mean.
    """
    for col in df.columns:
        # Log number of NaNs in the current column
        num_nans = df[col].isna().sum()
        if num_nans > 0:
            logger.warning(f'Number of NaNs in {col}: {num_nans}')
            logger.warning(f'Imputing mean for NaN values in {col}')
            # Impute mean for NaN values
            df[col].fillna(df[col].mean(), inplace=True)
    return df