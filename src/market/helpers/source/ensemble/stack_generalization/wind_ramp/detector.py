import pandas as pd

from .emp_quantile_method import anomaly_model
from .alarm_policy import alarm_policy_rule


def wind_ramp_detector(ens_params, df_pred_variability_insample, df_pred_variability_outsample):
    """
    Detects wind ramp anomalies based on the Empirical Quantile technique.
    Args:
        ens_params (dict): ensemble parameters.
        df_pred_variability_insample (pd.DataFrame): DataFrame with variability predictions for the insample data.
        df_pred_variability_outsample (pd.DataFrame): DataFrame with variability predictions for the outsample data.
    Returns:
        alarm_status (int): alarm status.
        df_ramp_clusters (pd.DataFrame): DataFrame with ramp events (consecutive anomalous values).
    """
    assert isinstance(df_pred_variability_insample, pd.DataFrame), "df_pred_variability_insample must be a DataFrame"
    assert isinstance(df_pred_variability_outsample, pd.DataFrame), "df_pred_variability_outsample must be a DataFrame"

    # Process variability forecasts variables names
    df_pred_variability_insample.columns = df_pred_variability_insample.columns.map(lambda x: f'Q{x*100:.0f}') 
    df_pred_variability_outsample.columns = df_pred_variability_outsample.columns.map(lambda x: f'Q{x*100:.0f}')

    # detect IQW anomalies for wind ramps using emprical quantile
    df_pred_variability_outsample, alarm_status = anomaly_model(df_pred_variability_insample, 
                                                    df_pred_variability_outsample, 
                                                    threshold_quantile=ens_params['threshold_quantile'])
    # trigger alarm for wind ramps
    alarm_status, df_ramp_clusters = alarm_policy_rule(alarm_status, 
                                                        df_pred_variability_outsample, 
                                                        max_consecutive_points=ens_params['max_consecutive_points'])
    # if df_ramp_clusters is not empty, return alarm status and df_ramp_clusters
    if not df_ramp_clusters.empty:
        return alarm_status, df_ramp_clusters
    else:
        return alarm_status, None