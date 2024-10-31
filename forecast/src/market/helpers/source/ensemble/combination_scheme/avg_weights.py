import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_pinball_loss


def calculate_weights(df_val_norm_diff):
    " Calculate weights based on the pinball loss of the forecasts"
    assert len(df_val_norm_diff) > 0, 'Dataframe is empty'
    lst_cols = [name for name in list(df_val_norm_diff.columns) if 'mostrecent' not in name]
    targ_col = [name for name in lst_cols if 'measured' in name]
    targets =  df_val_norm_diff[targ_col[0]]
    lst_cols_forecasts = [name for name in lst_cols if 'measured' not in name]
    lst_q10_weight = []
    lst_q50_weight = []
    lst_q90_weight = []
    for col in lst_cols_forecasts:
        if 'forecast' in col:
            forecast = df_val_norm_diff[col]
            q50_pb_loss = mean_squared_error(targets.values,  forecast.values)  # mean_pinball_loss(targets.values,  forecast.values, alpha=0.5)
            lst_q50_weight.append({col : 1/q50_pb_loss})
        elif 'confidence10' in col:
            forecast = df_val_norm_diff[col]
            q10_pb_loss = mean_pinball_loss(targets.values,  forecast.values, alpha=0.1)
            lst_q10_weight.append({col : 1/q10_pb_loss})
        elif 'confidence90' in col:
            forecast = df_val_norm_diff[col]
            q90_pb_loss = mean_pinball_loss(targets.values,  forecast.values, alpha=0.9)
            lst_q90_weight.append({col : 1/q90_pb_loss})
        else:
            raise ValueError('Not a valid column')
    return lst_cols_forecasts, lst_q10_weight, lst_q50_weight, lst_q90_weight
    
def normalize_weights(lst_weight):
    " Normalize weights, the sum should be 1"
    assert len(lst_weight) > 0, 'List of weights is empty'  
    total_sum = sum(list(loss.values())[0] for loss in lst_weight)
    norm_lst_weight = [{key: value/total_sum for key, value in d.items()} for d in lst_weight]
    return norm_lst_weight

def calculate_combination_forecast(df_test_norm_diff, lst_cols_forecasts, norm_lst_q50_pb_loss, norm_lst_q10_pb_loss, norm_lst_q90_pb_loss):
    " Calculate the combination forecast based on the pinball loss-based weights"
    combination_forecast = np.zeros(len(df_test_norm_diff))
    combination_quantile10 = np.zeros(len(df_test_norm_diff))
    combination_quantile90 = np.zeros(len(df_test_norm_diff))
    for col in lst_cols_forecasts:
        if 'forecast' in col:
            forecast = df_test_norm_diff[col]
            weight = [list(weight.values())[0] for weight in norm_lst_q50_pb_loss if col in weight][0]
            combination_forecast += forecast * weight
        elif 'confidence10' in col:
            forecast = df_test_norm_diff[col]
            weight = [list(weight.values())[0] for weight in norm_lst_q10_pb_loss if col in weight][0]
            combination_quantile10 += forecast * weight
        elif 'confidence90' in col:
            forecast = df_test_norm_diff[col]
            weight = [list(weight.values())[0] for weight in norm_lst_q90_pb_loss if col in weight][0]
            combination_quantile90 += forecast * weight
        else:
            raise ValueError('Not a valid column')
    return combination_forecast, combination_quantile10, combination_quantile90

def create_weighted_avg_df(df_test_norm_diff, combination_forecast, combination_quantile10, combination_quantile90):
    " Create dataframe with the weighted average forecast"
    assert len(df_test_norm_diff) == len(combination_forecast) == len(combination_quantile10) == len(combination_quantile90), 'Length mismatch'
    df_weighted_avg = pd.DataFrame({
        'Q10': combination_quantile10,
        'mean_prediction': combination_forecast,
        'Q90': combination_quantile90
    }, index=df_test_norm_diff.index)
    df_weighted_avg['diff_norm_measured'] = df_test_norm_diff['diff_norm_measured']
    return df_weighted_avg

def calculate_weighted_avg(df_train_norm_diff, df_test_norm_diff, start_predictions, window_size_valid=1, var=False):
    " Calculate the weights based on the pinball loss of the forecasts "
    if var:
        df_diff = pd.concat([df_train_norm_diff, df_test_norm_diff], axis=0).diff().dropna()
        df_train_norm_diff, df_test_norm_diff = df_diff[df_diff.index < start_predictions], df_diff[df_diff.index >= start_predictions]
        window_validation =  pd.to_datetime(start_predictions, utc=True) - pd.Timedelta(days=window_size_valid)
        df_val_norm_diff = df_train_norm_diff[df_train_norm_diff.index.to_series().between(window_validation, start_predictions)]
        lst_cols_forecasts, lst_q10_weight, lst_q50_weight, lst_q90_weight = calculate_weights(df_val_norm_diff)
        norm_lst_q50_weight = normalize_weights(lst_q50_weight) 
        norm_lst_q10_weight = normalize_weights(lst_q10_weight) 
        norm_lst_q90_weight = normalize_weights(lst_q90_weight) 
        combination_forecast, _, _ = calculate_combination_forecast(df_test_norm_diff, lst_cols_forecasts, norm_lst_q50_weight, norm_lst_q10_weight, norm_lst_q90_weight)
        df_weighted_avg = pd.DataFrame({
                'mean_prediction': combination_forecast,
            }, index=df_test_norm_diff.index)
        df_weighted_avg['diff_norm_measured'] = df_test_norm_diff['diff_norm_measured']
        dict_weights = {0.5:norm_lst_q50_weight}
        return df_weighted_avg, dict_weights
    
    window_validation =  pd.to_datetime(start_predictions, utc=True) - pd.Timedelta(days=window_size_valid)
    df_val_norm_diff = df_train_norm_diff[df_train_norm_diff.index.to_series().between(window_validation, start_predictions)]
    lst_cols_forecasts, lst_q10_weight, lst_q50_weight, lst_q90_weight = calculate_weights(df_val_norm_diff)
    norm_lst_q50_weight = normalize_weights(lst_q50_weight) 
    norm_lst_q10_weight = normalize_weights(lst_q10_weight) 
    norm_lst_q90_weight = normalize_weights(lst_q90_weight) 
    combination_forecast, combination_quantile10, combination_quantile90 = calculate_combination_forecast(df_test_norm_diff, lst_cols_forecasts, norm_lst_q50_weight, norm_lst_q10_weight, norm_lst_q90_weight)
    df_weighted_avg = pd.DataFrame({
            'Q10': combination_quantile10,
            'mean_prediction': combination_forecast,
            'Q90': combination_quantile90
        }, index=df_test_norm_diff.index)
    df_weighted_avg['diff_norm_measured'] = df_test_norm_diff['diff_norm_measured']
    dict_weights = {0.5:norm_lst_q50_weight, 0.1:norm_lst_q10_weight, 0.9: norm_lst_q90_weight}
    return df_weighted_avg, dict_weights