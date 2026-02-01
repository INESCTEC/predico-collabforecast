import pandas as pd

def calculate_equal_weights(df_test_norm_diff):
    " Calculate the mean prediction and quantiles using equal weights"
    assert 'diff_norm_measured' in df_test_norm_diff.columns, "diff_norm_measured column is missing"
    Q10 = df_test_norm_diff[['diff_norm_weekaheadconfidence10', 
                                'diff_norm_dayaheadconfidence10', 
                                'diff_norm_dayahead11hconfidence10']].mean(axis=1)
    MEAN = df_test_norm_diff[['diff_norm_weekaheadforecast', 
                                'diff_norm_dayaheadforecast', 
                                'diff_norm_dayahead11hforecast']].mean(axis=1)
    Q90 = df_test_norm_diff[['diff_norm_weekaheadconfidence90', 
                                'diff_norm_dayaheadconfidence90', 
                                'diff_norm_dayahead11hconfidence90']].mean(axis=1)
    df_equal_weights = pd.DataFrame({
        'Q10': Q10,
        'mean_prediction': MEAN,
        'Q90': Q90
    }, index=df_test_norm_diff.index)
    df_equal_weights['diff_norm_measured'] = df_test_norm_diff['diff_norm_measured']
    return df_equal_weights