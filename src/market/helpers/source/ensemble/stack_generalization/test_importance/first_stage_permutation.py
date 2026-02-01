import numpy as np

from joblib import Parallel, delayed

from .utils import extract_data_first_stage, validate_inputs_permutation_first_stage
from .utils import get_score_function, create_norm_import_scores_df


def decrease_performance(base_score, permuted_scores):
    """Calculate the mean decrease in performance.
    Args:
        base_score: the base score
        permuted_scores: the permuted scores
    Returns:
        mean_decreas: the mean decrease in performance
    """
    mean_decrease = max(0, np.mean(permuted_scores) - base_score)
    return mean_decrease

def permute_predictor(X, index, seed):
    """ Permute the predictor.
    Args:
        X: the data
        index: the index of the predictor
        seed: the seed
    Returns:
        X: the permuted data
    """
    rng = np.random.default_rng(seed)
    X[:, index] = rng.permutation(X[:, index])
    return X

def compute_first_stage_score(seed, X_test_augm, y_test, fitted_model, score_function, permutate=False, predictor_index=None):
    """ Compute  score for a single predictor. 
    Args:
        seed: the seed
        X_test_augm: the augmented test data
        y_test: the target variable
        fitted_model: the fitted model
        score_function: the score function
        permutate: whether to permute the predictor
        predictor_index: the index of the predictor
    Returns:
        score: the score
    """
    # Generate predictions from the first-stage model
    X_test = X_test_augm.copy()
    if permutate:
        # Permute the predictor if permute is True
        X_test = permute_predictor(X_test, predictor_index, seed)
    score = score_function(fitted_model, X_test, y_test)['mean_loss']
    return score

def first_stage_permutation_importance(y_test, params_model, quantile, info_previous_day_first_stage):
    """ Compute permutation importances for the first stage model.
    Args:
        y_test: the target variable
        params_model: the model parameters
        quantile: the quantile
        info_previous_day_first_stage: the info from the previous day
    Returns:
        results_df: the importance scores
    """
    # get info previous day
    fitted_model, X_test_augm, df_train_ens_augm, buyer_scaler_stats = extract_data_first_stage(info_previous_day_first_stage, quantile)
    # Standardize the target variable
    y_test = (y_test - buyer_scaler_stats['mean_buyer'])/buyer_scaler_stats['std_buyer']
    # Validate inputs
    validate_inputs_permutation_first_stage(params_model, quantile, y_test, X_test_augm)
    # Define the score functions for different quantiles
    score_function = get_score_function(quantile)
    # Compute the original score
    seed=42
    base_score = compute_first_stage_score(seed, X_test_augm, y_test, fitted_model, score_function)
    # Initialize the list to store the importance scores
    importance_scores = []
    # Loop through each predictor
    for predictor_index in range(X_test_augm.shape[1]):
        # Get the predictor name
        predictor_name = df_train_ens_augm.drop(columns=['norm_targ']).columns[predictor_index]
        # Compute the permuted scores in parallel
        permuted_scores = Parallel(n_jobs=params_model['nr_jobs_permutation'])(delayed(compute_first_stage_score)(seed, X_test_augm, 
                                                                                y_test, fitted_model, score_function,
                                                                                permutate=True, predictor_index=predictor_index) 
                                                                                for seed in range(params_model['nr_permutations']))
        # Compute the mean contribution
        mean_contribution = decrease_performance(base_score, permuted_scores)
        # Append the importance score to the list
        importance_scores.append({'predictor': predictor_name, 
                                'contribution': mean_contribution})
    # Create a DataFrame with the importance scores and sort, and normalize the contributions
    results_df = create_norm_import_scores_df(importance_scores)
    return results_df