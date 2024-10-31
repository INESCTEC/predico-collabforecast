import pandas as pd
import numpy as np

def create_augmented_dataframe_2stage(df, order_diff, max_lags, differentiate = False, add_lags=False, augment_with_poly=False, end_train=None, start_pred=None, end_pred=None):
    """ Process 2-stage ensemble dataframe with lags.
    Args:
        df: pd.DataFrame, ensemble dataframe
        order_diff: int, order of differentiation
        max_lags: int, maximum number of lags
        differentiate: bool, differentiate the dataframe
        add_lags: bool, add lags to the dataframe
        augment_with_poly: bool, augment with polynomial features
    Returns:
        df_: pd.DataFrame, processed ensemble dataframe
    """
    assert order_diff > 0, "Order of differentiation must be greater than 0"
    if add_lags:
        assert max_lags > 0, "max_lags should be greater than 0"
    else:
        assert max_lags == 0, "max_lags should be 0 when lagged is False"
    # Differentiate the targets
    for col in df.columns:
        if 'targets' in col:
            df[col] = df[col].diff(order_diff)
    # Differentiate the dataframe
    if differentiate:
        for col in df.columns:
            if 'targets' not in col:
                df[f'{col}_diff'] = df[col].diff(order_diff)
    # Create lagged features
    if add_lags:
        for col in df.columns:
            for lag in range(1, max_lags + 1):
                if 'targets' not in col:
                    df[col+'_t-'+str(lag)] = df[col].shift(lag)
    if augment_with_poly:
        for col in df.columns:
            if 'targets' not in col:
                df[f'{col}_sqr'] = df[col]**2
                df[f'{col}_cub'] = df[col]**3
    # Drop rows with NaNs resulting from the shift operation
    if add_lags:
        cut_ = max_lags + order_diff
    else:
        cut_ = order_diff
    df_ = df.iloc[cut_:, :]
    if add_lags:
        df_train = df_[df_.index < end_train]
        df_test = df_[(df_.index >= start_pred) & (df_.index <= end_pred)]
        for lag in range(1, max_lags + 1):
            lag_colunms = df_train.columns.str.contains('_t-'+str(lag))
            # set the first lag rows to nans
            df_train.loc[:df_train.index[lag - 1],df_train.columns[lag_colunms]] = np.nan
            df_test.loc[:df_test.index[lag - 1], df_test.columns[lag_colunms]] = np.nan
            # backfill the nans
            df_train = df_train.bfill()
            df_test = df_test.bfill()
            # concatenate the training and testing data
            df_ = pd.concat([df_train, df_test])
    return df_

def create_2stage_dataframe(df_train_ensemble, df_test_ensemble, y_train, y_test, predictions_insample, predictions_outsample):
    assert df_train_ensemble.shape[0] == len(predictions_insample), "Length mismatch between train data and in-sample predictions"
    assert df_test_ensemble.shape[0] == len(predictions_outsample), "Length mismatch between test data and out-sample predictions"
    assert len(y_train) == len(predictions_insample), "Length mismatch between targets and in-sample predictions"
    assert len(y_test) == 96, "Length should be 96"
    assert len(predictions_outsample) == 96, "Length should be 96"
    " Create 2-stage ensemble dataframe."
    # Creating DataFrame for in-sample predictions
    df_insample = pd.DataFrame(predictions_insample, columns=['predictions'], index=df_train_ensemble.index)
    df_insample['targets'] = y_train
    # Creating DataFrame for out-sample predictions
    df_outsample = pd.DataFrame(predictions_outsample, columns=['predictions'], index=df_test_ensemble.index)
    df_outsample['targets'] = y_test
    # Concatenating in-sample and out-sample DataFrames
    df_2stage = pd.concat([df_insample, df_outsample], axis=0)
    return df_2stage

def create_var_ensemble_dataframe(quantiles, quantile_predictions_dict, df_test):
    " Create ensemble dataframe from quantile predictions."
    assert len(quantiles) == len(quantile_predictions_dict), "Length mismatch between quantiles and quantile predictions"
    assert df_test.shape[0] == len(quantile_predictions_dict[quantiles[0]]), "Length mismatch between test data and predictions"
    for i, quantile in enumerate(quantiles):
        if i == 0:
            df_pred_ensemble = pd.DataFrame(quantile_predictions_dict[quantile])
            df_pred_ensemble.columns = ['datetime', 'q' + str(int(quantile*100))]
            df_pred_ensemble.set_index('datetime', inplace=True)
        else:
            df_pred_quantile = pd.DataFrame(quantile_predictions_dict[quantile])
            df_pred_quantile.columns = ['datetime', 'q' + str(int(quantile*100))]
            df_pred_quantile.set_index('datetime', inplace=True)
            df_pred_ensemble = pd.concat([df_pred_ensemble, df_pred_quantile], axis=1)
    return df_pred_ensemble


def get_numpy_Xy_train_test_2stage(df_2stage_train, df_2stage_test):
    """
    Prepares training and testing data for a two-stage model by separating features and targets.
    """
    X_train_2stage = df_2stage_train.drop(columns=['targets']).values
    y_train_2stage = df_2stage_train['targets'].values
    X_test_2stage = df_2stage_test.drop(columns=['targets']).values
    return X_train_2stage, y_train_2stage, X_test_2stage


def create_pre_test_dataframe(df_buyer, df_ensemble, pre_start_prediction, end_prediction, buyer_name):
    " Create test dataframes for buyer and ensemble predictions"
    # Ensure the DataFrame indices are datetime types
    if not pd.api.types.is_datetime64_any_dtype(df_buyer.index):
        raise TypeError("The df_buyer_norm index must be a datetime type.")
    if not pd.api.types.is_datetime64_any_dtype(df_ensemble.index):
        raise TypeError("The df_ensemble index must be a datetime type.")
    # Filter the DataFrames based on the start prediction timestamp
    df_test_targ_pre = df_buyer[(df_buyer.index >= pre_start_prediction) & (df_buyer.index <= end_prediction)]
    df_test_ensemble_pre = df_ensemble[(df_ensemble.index >= pre_start_prediction) & (df_ensemble.index <= end_prediction)]
    # Assign the normalized target column to the ensemble DataFrame
    df_test_ensemble_pre.loc[:, 'norm_targ'] = df_test_targ_pre['norm_' + buyer_name].values
    return df_test_ensemble_pre

def prepare_pre_test_data(params, quantile, df_test_ensemble, df_test_ensemble_q10=pd.DataFrame([]), df_test_ensemble_q90=pd.DataFrame([])):
    """Prepare test set for 2-stage model.
    Args:
        params: dict, ensemble parameters
        quantile: float, quantile value
        df_test_ensemble: pd.DataFrame, test data
        df_test_ensemble_q10: pd.DataFrame, quantile 10% test data
        df_test_ensemble_q90: pd.DataFrame, quantile 90% test data
    Returns:
        X_test: np.array, test features
        y_test: np.array, test target
    """
    # Assertions for input validation
    assert isinstance(df_test_ensemble, pd.DataFrame), "df_test_ensemble should be a DataFrame"
    assert len(df_test_ensemble) == 96, "df_test_ensemble should have 96 rows"
    assert len(df_test_ensemble_q10) == 96 or df_test_ensemble_q10.empty, "df_test_ensemble_q10 should have 96 rows or be empty"
    assert len(df_test_ensemble_q90) == 96 or df_test_ensemble_q90.empty, "df_test_ensemble_q90 should have 96 rows or be empty"
    assert "norm_targ" in df_test_ensemble.columns, "'norm_targ' should be in df_test_ensemble columns"
    target_column = "norm_targ"
    # Get the test data (features and target)
    X_test = df_test_ensemble.drop(columns=[target_column]).values
    y_test = df_test_ensemble[target_column].values
    # If quantile is 0.5 and no need to augment, return the original test data
    if quantile == 0.5 and not params.get('augment_q50', False):
            return X_test, y_test
    # If quantile predictions need to be added
    if params['add_quantile_predictions']:
        # Extract quantile data, default to empty arrays if unavailable
        X_test_q10 = df_test_ensemble_q10.values if not df_test_ensemble_q10.empty else np.array([])
        X_test_q90 = df_test_ensemble_q90.values if not df_test_ensemble_q90.empty else np.array([])
        # Prepare quantile data dictionary
        quantile_data = {
            0.1: X_test_q10,
            0.9: X_test_q90,
        }
        # Add the median quantile data if available
        if not (df_test_ensemble_q10.empty or df_test_ensemble_q90.empty):
            quantile_data[0.5] = np.concatenate([X_test_q10, X_test_q90], axis=1)
        elif not df_test_ensemble_q10.empty:
            quantile_data[0.5] = X_test_q10
        elif not df_test_ensemble_q90.empty:
            quantile_data[0.5] = X_test_q90
        else:
            quantile_data[0.5] = np.array([])
        # Validate the requested quantile
        if quantile not in quantile_data:
            raise ValueError("Invalid quantile value. Must be 0.1, 0.5, or 0.9.")
        # Concatenate the selected quantile data if it's not empty
        if quantile_data[quantile].size != 0:
            X_test = np.concatenate([X_test, quantile_data[quantile]], axis=1)
    return X_test, y_test

