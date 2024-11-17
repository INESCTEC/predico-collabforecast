import pandas as pd
import numpy as np

def split_train_test_data(df, end_train, start_prediction, end_prediction):
    "Split the data into training and test sets"
    assert isinstance(df, pd.DataFrame), "df should be a DataFrame"
    assert isinstance(end_train, pd.Timestamp), "end_training should be a Timestamp"
    assert isinstance(start_prediction, pd.Timestamp), "start_predictions should be a Timestamp"
    df_train = df[df.index < end_train]
    df_test = df[(df.index >= start_prediction) & (df.index <= end_prediction)]
    return df_train, df_test

def extract_quantile_columns(df, quantile):
    """Extract columns containing the specified quantile."""
    columns = [name for name in df.columns if quantile in name]
    if columns:
        return df[columns]
    else:
        print(f"No columns found for {quantile}")
        return pd.DataFrame()
    
def split_quantile_train_test_data(df, end_training_timestamp, start_prediction_timestamp, end_prediction_timestamp):
    """Split the quantile data into training and test sets."""
    if df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    df_train = df[df.index < end_training_timestamp]
    df_test = df[(df.index >= start_prediction_timestamp) & (df.index <= end_prediction_timestamp)]
    return df_train, df_test

def concatenate_feat_targ_dataframes(buyer_resource_name, df_train_ensemble, df_test_ensemble, df_train, df_test,  max_lag):
    "Prepare train and test data for ensemble model"
    assert isinstance(df_train_ensemble, pd.DataFrame), "df_train_ensemble should be a DataFrame"
    assert isinstance(df_test_ensemble, pd.DataFrame), "df_test_ensemble should be a DataFrame"
    assert isinstance(df_train, pd.DataFrame), "df_train should be a DataFrame"
    assert isinstance(df_test, pd.DataFrame), "df_test should be a DataFrame"
    assert 'norm_' + buyer_resource_name in df_train.columns, "norm_measured should be in df_train columns"
    assert 'norm_' + buyer_resource_name in df_test.columns, "norm_measured should be in df_test columns"
    assert isinstance(max_lag, int), "max_lag should be an integer"
    df_train_ensemble = df_train_ensemble.copy()
    df_test_ensemble = df_test_ensemble.copy()
    col_name_buyer = 'norm_' + buyer_resource_name
    df_train_ensemble.loc[:, 'norm_targ'] = df_train[col_name_buyer].values[max_lag:]
    df_test_ensemble.loc[:, 'norm_targ'] = df_test[col_name_buyer].values
    return df_train_ensemble, df_test_ensemble

def get_numpy_Xy_train_test(df_train_ensemble, df_test_ensemble):
    "Get numpy arrays for X_train, y_train, X_test, y_test"
    assert isinstance(df_train_ensemble, pd.DataFrame), "df_train_ensemble should be a DataFrame"
    assert isinstance(df_test_ensemble, pd.DataFrame), "df_test_ensemble should be a DataFrame"
    X_train, y_train = df_train_ensemble.iloc[:, :-1].values, df_train_ensemble.iloc[:, -1].values
    X_test, y_test = df_test_ensemble.iloc[:, :-1].values, df_test_ensemble.iloc[:, -1].values
    return X_train, y_train, X_test, y_test

def get_numpy_Xy_train_test_quantile(ens_params, df_train_ensemble_quantile10, df_test_ensemble_quantile10, df_train_ensemble_quantile90, df_test_ensemble_quantile90):
    "Make X-y train and test sets for quantile"
    if ens_params['add_quantile_predictions']:
        X_train_quantile10 = df_train_ensemble_quantile10.values if not df_train_ensemble_quantile10.empty else np.array([])
        X_test_quantile10 = df_test_ensemble_quantile10.values if not df_test_ensemble_quantile10.empty else np.array([])
        X_train_quantile90 = df_train_ensemble_quantile90.values if not df_train_ensemble_quantile90.empty else np.array([])
        X_test_quantile90 = df_test_ensemble_quantile90.values if not df_test_ensemble_quantile90.empty else np.array([])
    else:
        X_train_quantile10, X_test_quantile10 = np.array([]), np.array([])
        X_train_quantile90, X_test_quantile90 = np.array([]), np.array([])
    return X_train_quantile10, X_test_quantile10, X_train_quantile90, X_test_quantile90

