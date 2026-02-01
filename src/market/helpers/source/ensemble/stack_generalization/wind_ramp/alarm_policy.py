import pandas as pd

def filter_consecutive_ramps(df_anomalies, max_consecutive_points):
    """
    Filters the DataFrame to only include rows where 'is_consecutive' is True and
    'consecutive_count' is greater than or equal to max_consecutive_points.
    args:
        df_anomalies: DataFrame with anomalous events
        max_consecutive_points: Maximum number of consecutive points
    """
    return df_anomalies[(df_anomalies['is_consecutive'] == True) & 
                    (df_anomalies['consecutive_count'] >= max_consecutive_points)]

def detect_anomalous_clusters(df, max_consecutive_points, time_interval='15T'):
    """
    Detects and clusters consecutive anomalous events in a DataFrame based on a specified time interval.
    args:
        df: DataFrame with anomalous events
        max_consecutive_points: Maximum number of consecutive points
        time_interval: Time interval for consecutive events
    returns:
        df_ramps: DataFrame with ramp events (consecutive anomalous values)
    """
    # Filter out the rows where anomalous events occur
    df_anomalous = df[df['is_anomalous']].reset_index()
    df_anomalous.rename(columns={'index': 'datetime'}, inplace=True)
    # Calculate the time difference between consecutive events
    df_anomalous['time_diff'] = df_anomalous['datetime'].diff()
    # Determine if events are consecutive based on the provided time interval
    df_anomalous['is_consecutive'] = df_anomalous['time_diff'] == pd.Timedelta(time_interval)
    # Define clusters by identifying the start of a new cluster where events are not consecutive
    df_anomalous['cluster_id'] = (~df_anomalous['is_consecutive']).cumsum()
    # Group by cluster_id to calculate the number of consecutive events in each cluster
    df_cluster_info = df_anomalous.groupby('cluster_id')['is_consecutive'].sum().rename('consecutive_count')
    # Merge the original DataFrame with the cluster information
    df_anomalous = df_anomalous.merge(df_cluster_info, on='cluster_id')
    # Consecutive count + 1 to include the current event
    df_anomalous['consecutive_count'] += 1
    # Set ''datetime'' as the index for the final DataFrame
    df_anomalous.set_index('datetime', inplace=True)
    # Filter DataFrame based on consecutive conditions
    df_ramps = filter_consecutive_ramps(df_anomalous, max_consecutive_points)
    return df_ramps.drop(columns=['time_diff', 'is_consecutive', 'is_anomalous'])

def alarm_policy_rule(alarm_status, df_outsample, max_consecutive_points):
    """
    Check if a Ramp Alarm is triggered based on the number of outliers.
    """
    # If alarm is triggered and max_consecutive_points is specified
    df_ramp_clusters = pd.DataFrame()  # Default empty DataFrame
    if alarm_status == 1 and max_consecutive_points != 0:
        # Detect clusters of anomalous events
        df_ramp_clusters = detect_anomalous_clusters(df_outsample,  max_consecutive_points)
        # Update alarm status based on the presence of anomalous clusters
        alarm_status = int(not df_ramp_clusters.empty)
    return alarm_status, df_ramp_clusters