import numpy as np

from joblib import Parallel, delayed

from .utils import extract_data_first_stage, validate_inputs_shapley_first_stage
from .utils import get_score_function, create_norm_import_scores_df


def run_col_permutation(seed, nr_features):
    """ Run column permutation.
    Args:
        seed: the seed
        nr_features: the number of features
    Returns:
        columns_permutated: the permuted columns
    """
    rng = np.random.default_rng(seed)
    columns_permutated = rng.permutation(nr_features)
    return columns_permutated

def run_row_permutation_predictor(seed, X_test, predictor_index):
    """ Run row permutation predictor.
    Args:
        seed: the seed
        X_test: the test data
        predictor_index: the predictor index
    Returns:
        predictor_permutated: the permuted predictor
    """
    rng = np.random.default_rng(seed)
    predictor_permutated = rng.permutation(X_test[: , predictor_index])
    return predictor_permutated

def run_row_permutation_set_features(seed, X_test, set_feat2permutate):
    """ Run row permutation set features. 
    Args:
        seed: the seed
        X_test: the test data
        set_feat2permutate: the set of features to permute
    Returns:
        X_set_permutated: the permuted set of features selected
    """
    rng = np.random.default_rng(seed)
    X_set_permutated = rng.permutation(X_test[:, set_feat2permutate])
    return X_set_permutated

def compute_row_perm_score(seed, fitted_model, set_feat2permutate, predictor_index, X_test_augm, y_test, score_function, X_test_perm_with, X_test_perm_without):
    """ Compute row permutation score.
    Args:
        seed: the seed
        fitted_model: the fitted model
        set_feat2permutate: the set of features to permute
        predictor_index: the predictor index
        X_test_augm: the augmented test data
        y_test: the target variable
        score_function: the score function
        X_test_perm_with: the permuted test data with the predictor
        X_test_perm_without: the permuted test data without the predictor
    Returns:
        decrese_error: the decrease in error
    """
    # compute error by WITHOUT PERMUTATING feature of interest (error should be lower)
    X_test_perm_without[:, set_feat2permutate] = run_row_permutation_set_features(seed, X_test_augm, set_feat2permutate)
    score_without_permutation = score_function(fitted_model, X_test_perm_without, y_test)['mean_loss']
    # compute error by PERMUTATING feature of interest (error should be higher)
    X_test_perm_with[:, set_feat2permutate] = run_row_permutation_set_features(seed, X_test_augm, set_feat2permutate)
    X_test_perm_with[:, predictor_index] = run_row_permutation_predictor(seed, X_test_augm, predictor_index)
    score_with_permutation = score_function(fitted_model, X_test_perm_with, y_test)['mean_loss']
    # return the difference in error
    decrese_error = max(0, score_with_permutation - score_without_permutation)
    return decrese_error

def compute_col_perm_score(seed, params_model, nr_features, X_test_augm, y_test, fitted_model, score_function, predictor_index, list_set_feat2permutate):
    """Compute score for a single predictor.
    Args:
        seed: the seed
        params_model: the model parameters
        nr_features: the number of features
        X_test_augm: the augmented test data
        y_test: the target variable
        fitted_model: the fitted model
        score_function: the score function
        predictor_index: the predictor index
        list_set_feat2permutate: the list of set of features permuted
    Returns:
        col_score: the column score
        str_set_feat2permutate: the set of features permuted
    """
    # Define the maximum number of iterations
    max_iterations = 2 * nr_features - 1
    iteration_count = 0
    # 1) Get the column permutation
    col_perm = run_col_permutation(seed, nr_features)
    # 2) Ensure that the first element of col_perm is not the predictor_index
    while col_perm[0] == predictor_index:
        seed += 1
        col_perm = run_col_permutation(seed, nr_features)
    # 3) Get the set of features to permute
    set_feat2permutate = col_perm[np.arange(0, np.where(col_perm == predictor_index)[0][0])]
    # transform set_feat2permutate to an unique string
    str_set_feat2permutate = ''.join(str(e) for e in set_feat2permutate)
    # 4) if the set of features to permute has already been computed and iteration is lower than max_iterations, 
    # find a new set of features to permute
    while str_set_feat2permutate in list_set_feat2permutate and iteration_count < max_iterations:
        iteration_count += 1
        seed += 1  # Increment seed to get a different permutation
        col_perm = run_col_permutation(seed, nr_features)
        set_feat2permutate = col_perm[np.arange(0, np.where(col_perm == predictor_index)[0][0])]
        # transform set_feat2permutate to an unique string
        str_set_feat2permutate = ''.join(str(e) for e in set_feat2permutate)
    # Permute features in the test set
    X_test_perm_with, X_test_perm_without = X_test_augm.copy(), X_test_augm.copy()
    # Compute row scores using parallel processing
    row_scores = Parallel(n_jobs=params_model['nr_jobs_shapley'])(
        delayed(compute_row_perm_score)(
            seed, fitted_model, set_feat2permutate, predictor_index, X_test_augm, 
            y_test, score_function, X_test_perm_with, X_test_perm_without
        ) for seed in range(params_model['nr_row_permutations'])
    )
    # Compute the final column score
    col_score = np.mean(row_scores)
    return col_score, str_set_feat2permutate

def first_stage_shapley_importance(y_test, params_model, quantile, info_previous_day_first_stage):
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
    y_test = (y_test - buyer_scaler_stats['mean_buyer']) / buyer_scaler_stats['std_buyer']
    # Validate inputs
    validate_inputs_shapley_first_stage(params_model, quantile, y_test, X_test_augm)
    # Define the score functions for different quantiles
    score_function = get_score_function(quantile)
    # Initialize the list to store the importance scores
    importance_scores = []
    # Loop through each predictor
    nr_features = X_test_augm.shape[1]
    for predictor_index in range(nr_features):
        # Get the predictor name
        predictor_name = df_train_ens_augm.drop(columns=['norm_targ']).columns[predictor_index]
        list_scores = []
        list_set_feat2permutate = []
        for seed in range(params_model['nr_col_permutations']):
            col_score, set_feat2permutate = compute_col_perm_score(seed, params_model, nr_features, X_test_augm, y_test, fitted_model, score_function, predictor_index, list_set_feat2permutate)
            # Append the importance score to the list
            list_scores.append(col_score)
            # Append the set of features to permute to the list
            list_set_feat2permutate.append(set_feat2permutate)
        # Increment the seed
        seed += 1
        # Compute the average marginal contribution
        shapley_score = np.mean(list_scores)
        # Append the importance score to the list
        importance_scores.append({'predictor': predictor_name, 
                                'contribution': shapley_score})
    # Create a DataFrame with the importance scores, sort, and normalize it
    results_df = create_norm_import_scores_df(importance_scores)
    return results_df