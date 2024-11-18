import numpy as np

from joblib import Parallel, delayed

from .utils import extract_data_second_stage, validate_inputs_permutation_second_stage
from .utils import get_score_function, create_norm_import_scores_df, prepare_second_stage_data


def decrease_performance(base_score, permuted_scores):
    """ Calculate the mean decrease in performance.
    Args:
        base_score (float): The base score.
        permuted_scores (list): The permuted scores.
    Returns:
        decrease_performance (float): The mean decrease in performance.
    """
    decrease_performance = max(0, np.mean(permuted_scores) - base_score)
    return decrease_performance
    
def permute_predictor(X, index, seed):
    """Permute the predictor.
    Args:
        X (np.array): The data.
        index (int): The index of the predictor to permute.
        seed (int): The seed for the random number generator.
    Returns:
        X (np.array): The data with the permuted predictor.
    """
    rng = np.random.default_rng(seed)
    X[:, index] = rng.permutation(X[:, index])
    return X

def compute_second_stage_score(seed, parameters_model, 
                                    fitted_model, var_fitted_model, X_test_augmented_prev, df_train_ensemble, df_test_ensemble_prev, y_train, 
                                    y_test, score_function, predictions_insample, forecast_range, permutate=False, predictor_index=None):
    """Compute the permuted score for a single predictor in the second stage model.
    Args:
        seed (int): The seed for the random number generator.
        parameters_model (dict): The parameters of the model.
        fitted_model (object): The fitted model.
        var_fitted_model (object): The variance of the fitted model.
        X_test_augmented_prev (np.array): The augmented test data from the previous day.
        df_train_ensemble (pd.DataFrame): The training data for the ensemble.
        df_test_ensemble_prev (pd.DataFrame): The test data from the previous day for the ensemble.
        y_train (np.array): The target variable for the training data.
        y_test (np.array): The target variable from the previous day.
        score_function (function): The score function.
        predictions_insample (np.array): The predictions from the first-stage model.
        forecast_range (list): The forecast range.
        permutate (bool): Whether to permute the predictor.
        predictor_index (int): The index of the predictor to permute.
    Returns:
        score (float): The score.
    """
    # Generate predictions from the first-stage model
    X_test = X_test_augmented_prev.copy()
    if permutate:
        # Permute the predictor if permute is True
        X_test = permute_predictor(X_test, predictor_index, seed)
    predictions_outsample = fitted_model.predict(X_test)
    # Prepare second stage data
    df_2stage_processed = prepare_second_stage_data(parameters_model, df_train_ensemble, df_test_ensemble_prev, y_train, y_test, predictions_insample, predictions_outsample)
    df_2stage_test = df_2stage_processed[(df_2stage_processed.index >= forecast_range[0]) & (df_2stage_processed.index <= forecast_range[-1])]
    X_test_2stage, y_test_2stage = df_2stage_test.drop(columns=['targets']).values, df_2stage_test['targets'].values
    # Compute and return the score
    score = score_function(var_fitted_model, X_test_2stage, y_test_2stage)['mean_loss']
    return score

def second_stage_permutation_importance(y_test, parameters_model, quantile, info, forecast_range):
    """
    Compute permutation importances for the second stage model.
    Args:
        y_test (np.array): The target variable from the previous day.
        parameters_model (dict): The parameters of the model.
        quantile (float): The quantile.
        info (dict): The information dictionary.
        forecast_range (list): The forecast range.
    Returns:
        results_df (pd.DataFrame): The DataFrame with the normalized importance scores.
    """
    # Get the info from the previous day
    fitted_model, y_train, var_fitted_model, X_test_augm, df_test_ens, df_train_ens, df_train_ens_augm, X_train_augmented, buyer_scaler_stats = extract_data_second_stage(info, quantile)
    # Standardize the target variable
    y_test = (y_test - buyer_scaler_stats['mean_buyer'])/buyer_scaler_stats['std_buyer']
    # Initial validations 
    validate_inputs_permutation_second_stage(parameters_model, quantile, y_test,  X_test_augm)
    # Get the score function
    score_function = get_score_function(quantile)
    # Compute the base score
    seed = 42
    predictions_insample = fitted_model.predict(X_train_augmented)
    base_score = compute_second_stage_score(seed, parameters_model,  
                                                fitted_model, 
                                                var_fitted_model, 
                                                X_test_augm, 
                                                df_train_ens, 
                                                df_test_ens, 
                                                y_train, 
                                                y_test, score_function, predictions_insample, forecast_range)
    # Compute importance scores for each predictor
    importance_scores = []
    for predictor_index in range(X_test_augm.shape[1]):
        # Get the predictor name
        predictor_name = df_train_ens_augm.drop(columns=['norm_targ']).columns[predictor_index]
        # Compute permuted scores in parallel
        permuted_scores = Parallel(n_jobs=parameters_model['nr_jobs_permutation'])(delayed(compute_second_stage_score)(seed, 
                                                                                        parameters_model, 
                                                                                        fitted_model, 
                                                                                        var_fitted_model, 
                                                                                        X_test_augm, 
                                                                                        df_train_ens, 
                                                                                        df_test_ens, 
                                                                                        y_train,
                                                                                        y_test, 
                                                                                        score_function, 
                                                                                        predictions_insample, 
                                                                                        forecast_range, 
                                                                                        permutate=True, predictor_index=predictor_index) 
                                                                                        for seed in range(parameters_model['nr_permutations']))
        # Calculate mean contribution for the predictor
        mean_contribution = decrease_performance(base_score, permuted_scores) 
        importance_scores.append({'predictor': predictor_name, 
                                'contribution': mean_contribution})
    # Create a DataFrame with normalize contributions
    results_df = create_norm_import_scores_df(importance_scores)
    return results_df