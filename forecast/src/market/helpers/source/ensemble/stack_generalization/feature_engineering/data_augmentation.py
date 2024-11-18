import pandas as pd
import numpy as np

def create_augmented_dataframe(df, max_lags, forecasters_diversity=False, add_lags=False, augment_with_poly=False, augment_with_roll_stats =False, differenciate=False, end_train=None, start_pred=None, end_pred=None):
    """ Create feature engineering dataframe with forecasters diversity, lagged, augmented and differenciate features 
    args:
        df: pd.DataFrame, dataframe
        max_lags: int, maximum lag value
        forecasters_diversity: bool, create forecasters diversity features
        lagged: bool, create lagged features
        augmented: bool, create augmented features
        differenciate: bool, create differenciate features
    returns:
        df: pd.DataFrame, dataframe with the new features
    """
    assert isinstance(df, pd.DataFrame), "df should be a DataFrame"
    assert isinstance(max_lags, int), "max_lags should be an integer"
    if add_lags:
        assert max_lags > 0, "max_lags should be greater than 0"
    else:
        assert max_lags == 0, "max_lags should be 0 when lagged is False"
    shifted_df_ensemble = pd.DataFrame()
    if forecasters_diversity:
        " Create forecasters diversity features"
        forecast_cols = [name for name in df.columns if any(q in name for q in ['q50', 'q10', 'q90'])] # forecasters columns
        shifted_df_ensemble["forecasters_std"] = df[forecast_cols].std(axis=1)  # standard deviation among forecasters
        shifted_df_ensemble["forecasters_var"] = df[forecast_cols].var(axis=1)  # variance among forecasters
        shifted_df_ensemble["forecasters_mean"] = df[forecast_cols].mean(axis=1)  # mean among forecasters
        shifted_df_ensemble["forecasters_prod"] = df[forecast_cols].prod(axis=1)  # product among forecasters
    if add_lags:
        " Create lagged features"
        for lag in range(1, max_lags + 1):
            for col in df.columns:
                if max_lags > 1:
                    for lag in range(1, max_lags + 1):
                            shifted_df_ensemble[col+'_t-'+str(lag)] = df[col].shift(lag)  # lagged
                else:
                    shifted_df_ensemble[col+'_t-1'] = df[col].shift(1)
    if augment_with_poly:
        " Create augmented features"
        for col in df.columns:
            shifted_df_ensemble[col + "_sqr"] = df[col]**2  # squared
            shifted_df_ensemble[col + "_cub"] = df[col]**3  # cubic
    if augment_with_roll_stats:
        " Create rolling statistics features"
        if add_lags:
            shifted_df_ensemble[col + "_avg"] = df[col].rolling(max_lags).mean()  # rolling average
            if max_lags > 1:
                shifted_df_ensemble[col + "_std"] = df[col].rolling(max_lags).std()  # rolling standard deviation
                shifted_df_ensemble[col + "_var"] = df[col].rolling(max_lags).var()  # rolling variance
            if max_lags > 2:
                shifted_df_ensemble[col + "_lag-1_avg"] = df[col].shift(1).rolling(max_lags-1).mean()  # rolling average on lag-1
                shifted_df_ensemble[col + "_lag-1_std"] = df[col].shift(1).rolling(max_lags-1).std()  # rolling standard deviation on lag-1
                shifted_df_ensemble[col + "_lag-1_var"] = df[col].shift(1).rolling(max_lags-1).var()  # rolling variance on lag-1
    if differenciate:
        " Create differenciate features"
        if add_lags:
            for col in df.columns:
                shifted_df_ensemble[col + "_diff"] = df[col].diff()  # difference
                shifted_df_ensemble[col + "_lag-1_diff"] = df[col].shift(1).diff()  # difference on lag-1
    " Concatenate the original dataframe with the shifted dataframe"
    df = pd.concat([df, shifted_df_ensemble], axis=1)
    if add_lags:
        df = df.iloc[max_lags:,:]  # remove the first rows with NaN values
        df_train = df[df.index < end_train].copy()
        df_test = df[(df.index >= start_pred) & (df.index <= end_pred)].copy()
        for lag in range(1, max_lags + 1):
            lag_colunms = df_train.columns.str.contains('_t-'+str(lag))
            # set the first lag rows to nans
            df_train.loc[:df_train.index[lag - 1],df_train.columns[lag_colunms]] = np.nan
            df_test.loc[:df_test.index[lag - 1], df_test.columns[lag_colunms]] = np.nan
            # backfill the nans
            df_train.bfill(inplace=True)
            df_test.bfill(inplace=True)
            # concatenate the training and testing data
            df = pd.concat([df_train, df_test], axis=0)

    return df.dropna(axis=1, how="all")

def augment_with_quantiles(X_train, X_test, df_train_ensemble, 
                            X_train_quantile10, X_test_quantile10, df_train_ensemble_quantile10,
                            X_train_quantile90, X_test_quantile90, df_train_ensemble_quantile90,  
                            quantile, augment_q50=False):
    """ Augment the training and testing data with the quantiles predictions from forecasters
    args:
        X_train: np.array, training data
        X_test: np.array, testing data
        df_train_ensemble: pd.DataFrame, training data
        X_train_quantile10: np.array, training data for quantile 10
        X_test_quantile10: np.array, testing data for quantile 10
        df_train_ensemble_quantile10: pd.DataFrame, training data for quantile 10
        X_train_quantile90: np.array, training data for quantile 90
        X_test_quantile90: np.array, testing data for quantile 90
        df_train_ensemble_quantile90: pd.DataFrame, training data for quantile 90
        quantile: float, quantile value
        augment_q50: bool, augment with quantiles predictions
    returns:
        X_train: np.array, augmented training data
        X_test: np.array, augmented testing data
        df_train_ensemble: pd.DataFrame, augmented training data"""
    
    assert isinstance(X_train, np.ndarray), "X_train should be a numpy array"
    assert isinstance(X_test, np.ndarray), "X_test should be a numpy array"
    assert isinstance(df_train_ensemble, pd.DataFrame), "df_train_ensemble should be a DataFrame"
    assert isinstance(X_train_quantile10, np.ndarray), "X_train_quantile10 should be a numpy array"
    assert isinstance(X_test_quantile10, np.ndarray), "X_test_quantile10 should be a numpy array"
    assert isinstance(df_train_ensemble_quantile10, pd.DataFrame), "df_train_ensemble_quantile10 should be a DataFrame"
    assert isinstance(X_train_quantile90, np.ndarray), "X_train_quantile90 should be a numpy array"
    assert isinstance(X_test_quantile90, np.ndarray), "X_test_quantile90 should be a numpy array"
    assert isinstance(df_train_ensemble_quantile90, pd.DataFrame), "df_train_ensemble_quantile90 should be a DataFrame"
    assert quantile in [0.1, 0.5, 0.9], "Invalid quantile value. Must be 0.1, 0.5, or 0.9."
    # If quantile is 0.5 and no need to augment, return the original training and testing data
    if quantile == 0.5 and not augment_q50:
        " Do not augment with augmented quantiles"
        return X_train, X_test, df_train_ensemble
    # Create a dictionary with the quantile data
    if not df_train_ensemble_quantile10.empty and not df_train_ensemble_quantile90.empty: 
        quantile_data = {
            0.1: (X_train_quantile10, X_test_quantile10, df_train_ensemble_quantile10),
            0.5: (np.concatenate([X_train_quantile10, X_train_quantile90], axis=1),
                    np.concatenate([X_test_quantile10, X_test_quantile90], axis=1),
                    pd.concat([df_train_ensemble_quantile10, df_train_ensemble_quantile90], axis=1)),
            0.9: (X_train_quantile90, X_test_quantile90, df_train_ensemble_quantile90)
        }
    elif not df_train_ensemble_quantile10.empty:
        quantile_data = {
            0.1: (X_train_quantile10, X_test_quantile10, df_train_ensemble_quantile10),
            0.5: (X_train_quantile10, X_test_quantile10, df_train_ensemble_quantile10),
            0.9: (np.array([]), np.array([]), pd.DataFrame([]))
        }
    elif not df_train_ensemble_quantile90.empty:
        quantile_data = {
            0.1: (np.array([]), np.array([]), pd.DataFrame([])),
            0.5: (X_train_quantile90, X_test_quantile90, df_train_ensemble_quantile90),
            0.9: (X_train_quantile90, X_test_quantile90, df_train_ensemble_quantile90)
        }
    else:
        return X_train, X_test, df_train_ensemble
    if quantile not in quantile_data:
        raise ValueError('Invalid quantile value. Must be 0.1, 0.5, or 0.9.')
    " Get the quantile data and augment the training and testing data with it"
    X_train_part, X_test_part, df_train_ensemble_part = quantile_data[quantile]
    X_train = np.concatenate([X_train, X_train_part], axis=1) if X_train_part.size > 0 else X_train
    X_test = np.concatenate([X_test, X_test_part], axis=1) if X_test_part.size > 0 else X_test
    df_train_ensemble = pd.concat([df_train_ensemble, df_train_ensemble_part], axis=1)
    return X_train, X_test, df_train_ensemble