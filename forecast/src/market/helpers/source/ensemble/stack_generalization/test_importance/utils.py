import pandas as pd
import pickle
from loguru import logger
from src.market.helpers.source.ensemble.stack_generalization.hyperparam_optimization.models.utils.cross_validation import score_func_10, score_func_50, score_func_90
from src.market.helpers.source.ensemble.stack_generalization.second_stage.create_data_second_stage import create_2stage_dataframe, create_augmented_dataframe_2stage

def load_model_info(file_path):
    " Load model info"
    assert file_path.endswith('.pickle'), 'The file must be a pickle file'
    try:
        with open(file_path, 'rb') as handle:
            return pickle.load(handle)
    except Exception as e:
        logger.error(f"Failed to load model info from {file_path}: {e}")
        return None

def extract_data_first_stage(info, quantile):
    " Extract data from the info dictionary for first-stage-ensemble."
    return (
            info[quantile]['fitted_model'],
            info[quantile]['X_test_augmented'],
            info[quantile]['df_train_ensemble_augmented'],
            info[quantile]["buyer_scaler_stats"]
        )

def extract_data_second_stage(info, quantile):
    """ Extract data from the info dictionary for second-stage-ensemble.
    """
    fitted_model = info[quantile]['fitted_model']
    y_train = info[quantile]['y_train'] 
    var_fitted_model = info[quantile]['var_fitted_model']
    X_test_augm = info[quantile]['X_test_augmented'] 
    df_test_ens = info[quantile]['df_test_ensemble'] 
    df_train_ens = info[quantile]['df_train_ensemble']
    df_train_ens_augm = info[quantile]['df_train_ensemble_augmented']  
    X_train_augmented = info[quantile]['X_train_augmented']
    buyer_scaler_stats = info[quantile]["buyer_scaler_stats"]
    return fitted_model, y_train, var_fitted_model, X_test_augm, df_test_ens, df_train_ens, df_train_ens_augm, X_train_augmented, buyer_scaler_stats

def validate_inputs_permutation_second_stage(params_model, quantile, y_test, X_test_augmented):
    assert params_model['nr_permutations'] > 0, "Number of permutations must be positive"
    assert quantile in [0.1, 0.5, 0.9], "Quantile must be one of 0.1, 0.5, 0.9"
    assert len(y_test) == len(X_test_augmented), "The length of y_test and X_test_augmented must be the same"

def validate_inputs_permutation_first_stage(params_model, quantile, y_test, X_test):
    " Validate the inputs."
    assert params_model['nr_permutations'] > 0, "Number of permutations must be positive"
    assert quantile in [0.1, 0.5, 0.9], "Quantile must be one of 0.1, 0.5, 0.9"
    assert len(y_test) == len(X_test), "The length of y_test and X_test_augmented must be the same"

def validate_inputs_shapley_second_stage(params_model, quantile, y_test, X_test_augmented):
    assert params_model['nr_row_permutations'] > 0, "Number of row permutations must be positive"
    assert params_model['nr_row_permutations'] > 0, "Number of col permutations must be positive"
    assert quantile in [0.1, 0.5, 0.9], "Quantile must be one of 0.1, 0.5, 0.9"
    assert len(y_test) == len(X_test_augmented), "The length of y_test and X_test_augmented must be the same"

def validate_inputs_shapley_first_stage(params_model, quantile, y_test, X_test):
    " Validate the inputs."
    assert params_model['nr_row_permutations'] > 0, "Number of row permutations must be positive"
    assert params_model['nr_row_permutations'] > 0, "Number of col permutations must be positive"
    assert quantile in [0.1, 0.5, 0.9], "Quantile must be one of 0.1, 0.5, 0.9"
    assert len(y_test) == len(X_test), "The length of y_test and X_test_augmented must be the same"

def get_score_function(quantile):
    " Get the score function for the quantile."
    score_functions = {
        0.1: score_func_10,
        0.5: score_func_50,
        0.9: score_func_90
    }
    return score_functions[quantile]

def prepare_second_stage_data(params_model, df_train_ensemble, df_test_ensemble, y_train, y_test, predictions_insample, predictions_outsample):
    " Prepare the second stage data."
    # Create the 2-stage DataFrame
    df_2stage = create_2stage_dataframe(df_train_ensemble, df_test_ensemble, y_train, y_test, predictions_insample, predictions_outsample)
    # Process the 2-stage DataFrame
    df_2stage_processed = create_augmented_dataframe_2stage(df_2stage, 
                                                            order_diff = params_model['order_diff'],
                                                            differentiate=params_model['differenciate_var'], 
                                                            max_lags=params_model['max_lags_var'], 
                                                            add_lags = params_model['add_lags_var'],
                                                            augment_with_poly=params_model['augment_with_poly_var'],
                                                            end_train=df_train_ensemble.index[-1], 
                                                            start_pred=df_test_ensemble.index[0], 
                                                            end_pred=df_test_ensemble.index[-1])
    return df_2stage_processed

def normalize_contributions(df):
    " Normalize the contributions."
    total_contribution = abs(df['contribution']).sum()
    df['contribution'] = abs(df['contribution'])/total_contribution
    return df

def create_norm_import_scores_df(importance_scores):
    """
    Create a DataFrame with the importance scores, sort it, drop specific rows, 
    and normalize the contributions.
    """
    # Create a DataFrame with the importance scores
    results_df = pd.DataFrame(importance_scores)
    # Drop the forecasters standard deviation and variance rows
    results_df = results_df[~results_df.predictor.isin(['forecasters_var', 'forecasters_std', 'forecasters_mean', 'forecasters_prod'])]
    # Normalize contributions
    results_df = normalize_contributions(results_df)
    # Sort the DataFrame by the contributions
    results_df = results_df.sort_values(by='contribution', ascending=False)
    return results_df

