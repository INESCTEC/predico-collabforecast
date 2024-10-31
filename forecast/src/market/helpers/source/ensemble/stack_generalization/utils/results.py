import pandas as pd
from loguru import logger

def collect_quantile_ensemble_predictions(quantiles, test_data, predictions):
    " Collect quantile ensemble predictions as a list of dictionaries."
    assert test_data.shape[0] == len(predictions[quantiles[0]]), "Length mismatch between test data and predictions"    
    quantile_predictions_dict = {}
    try:
        for quantile in quantiles:
            quantile_ensemble_predictions = []
            if test_data.shape[0] != len(predictions[quantile]):
                raise ValueError("Length mismatch between test data and predictions for quantile {}".format(quantile))
            for i in range(len(predictions[quantile])):
                quantile_ensemble_predictions.append({'datetime': test_data.index[i],
                                                        'predictions': predictions[quantile][i]})
            quantile_predictions_dict[quantile] = quantile_ensemble_predictions
    except Exception as e:
        logger.exception("An error occurred:", e)
        return None
    return quantile_predictions_dict

def create_ensemble_dataframe(quantiles, quantile_predictions_dict, df_test):
    " Create ensemble dataframe from quantile predictions."
    assert len(quantiles) == len(quantile_predictions_dict), "Length mismatch between quantiles and quantile predictions"
    assert df_test.shape[0] == len(quantile_predictions_dict[quantiles[0]]), "Length mismatch between test data and predictions"
    assert 'targets' in df_test.columns, 'targets column not found in test data'
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

def melt_dataframe(df_ensemble):
    " Melt dataframe results"
    return pd.melt(df_ensemble.reset_index(), id_vars='datetime', value_vars=df_ensemble.columns) 