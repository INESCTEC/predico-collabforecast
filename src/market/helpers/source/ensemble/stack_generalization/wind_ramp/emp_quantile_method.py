import numpy as np


def get_quantile(score_data, threshold):
    " Get the quantile threshold of the data. "
    return np.quantile(score_data, threshold)

def get_anomalies(data, threshold):
    " Get the anomalies based on the quantile threshold. "
    return data[data > threshold]  # Get the anomalies

def detect_anomalies(pred_var_outsample, quantile_anomaly_threshold, testing_pi_values):
    """
    Detect anomalies based on the quantile threshold and normalize probability alarms.
    """
    # Mark data points as anomalous based on the threshold
    pred_var_outsample['is_anomalous'] = is_anomalous( testing_pi_values, quantile_anomaly_threshold)
    return pred_var_outsample

def is_anomalous(testing_pi_values, quantile_anomaly_threshold):
    """
    Determine if data points are anomalous based on the KDE and threshold.
    """
    return testing_pi_values > quantile_anomaly_threshold  

def anomaly_model(df_insample, df_outsample, threshold_quantile):
    """
    Detect anomalies using the Empirical Quantile technique.
    """
    # compute IQW column for df_insample and df_outsample
    df_insample['IQW'] = df_insample['Q90'] - df_insample['Q10']
    df_outsample['IQW'] = df_outsample['Q90'] - df_outsample['Q10']

    # get the IQW values for training and testing data
    preprocessed_training_eq = df_insample['IQW'].values
    testing_eq = df_outsample['IQW'].values 
    # get quantile for anomalies
    quantile_anomaly_threshold = get_quantile(preprocessed_training_eq, threshold_quantile)
    # get points with density above quantile threshold
    #anomalies_eq = get_anomalies(testing_eq, quantile_anomaly_threshold)
    # detect anomalies 
    df_outsample = detect_anomalies(df_outsample, quantile_anomaly_threshold, testing_eq)
    # set alarm status
    alarm_status = 1 if np.any(df_outsample['is_anomalous'] == True) else 0
    return df_outsample, alarm_status



