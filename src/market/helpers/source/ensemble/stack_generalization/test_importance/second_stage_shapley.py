import numpy as np

from joblib import Parallel, delayed

from .utils import extract_data_second_stage, validate_inputs_shapley_second_stage
from .utils import get_score_function, create_norm_import_scores_df, prepare_second_stage_data


def run_col_permutation(seed, nr_features):
    """Run column permutation.
    Args:
        seed (int): The seed for the random number generator.
        nr_features (int): The number of features.
    Returns:
        cols_permutated (np.array): The permuted columns.
    """
    rng = np.random.default_rng(seed)
    cols_permutated = rng.permutation(nr_features)
    return cols_permutated

def run_row_permutation_predictor(seed, X_test, predictor_index):
    """ Run row permutation predictor.
    Args:
        seed (int): The seed for the random number generator.
        X_test (np.array): The test data.
        predictor_index (int): The index of the predictor to permute.
    Returns:
        predictor_permutated (np.array): The permuted predictor
    """
    rng = np.random.default_rng(seed)
    predictor_permutated = rng.permutation(X_test[: , predictor_index])
    return predictor_permutated

def run_row_permutation_set_features(seed, X_test, set_feat2permutate):
    """ Run row permutation set features.
    Args:
        seed (int): The seed for the random number generator.
        X_test (np.array): The test data.
        set_feat2permutate (np.array): The set of features to permute.
    Returns:
        X_set_permutated (np.array): The permuted set of features.
    """
    rng = np.random.default_rng(seed)
    X_set_permutated = rng.permutation(X_test[:, set_feat2permutate])
    return X_set_permutated

def compute_row_perm_score(seed, params_model, set_feat2perm, predictor_index, y_test, fit_model, y_train, var_fit_model, X_test_augm, df_test_ens, df_train_ens_augm, pred_insample, score_function, X_test_perm_with, X_test_perm_without, forecast_range):
    """ Compute row permutation score.
    Args:
        seed (int): The seed for the random number generator.
        params_model (dict): The parameters of the model.
        set_feat2perm (np.array): The set of features to permute.
        predictor_index (int): The index of the predictor to permute.
        y_test (np.array): The target variable from the previous day.
        fit_model (object): The fitted model.
        y_train (np.array): The target variable for the training data.
        var_fit_model (object): The variance of the fitted model.
        X_test_augm (np.array): The augmented test data from the previous day.
        df_test_ens (pd.DataFrame): The test data from the previous day for the ensemble.
        df_train_ens_augm (pd.DataFrame): The training data for the ensemble.
        pred_insample (np.array): The predictions from the first-stage model.
        score_function (function): The score function.
        X_test_perm_with (np.array): The test data with the permuted predictor.
        X_test_perm_without (np.array): The test data without the permuted predictor.
        forecast_range (list): The forecast range.
    Returns:
        decrease_error (float): The decrease in error.
    """
    # compute error by PERMUTATING WITHOUT feature of interest
    X_test_perm_without[:, set_feat2perm] = run_row_permutation_set_features(seed, X_test_augm, set_feat2perm)
    pred_outsample_perm_without = fit_model.predict(X_test_perm_without)
    df_2stage_without_perm = prepare_second_stage_data(params_model, df_train_ens_augm, df_test_ens, y_train, y_test, pred_insample, pred_outsample_perm_without)
    df_2stage_test_without_perm = df_2stage_without_perm[(df_2stage_without_perm.index >= forecast_range[0]) & (df_2stage_without_perm.index <= forecast_range[-1])]
    X_test_2stage_without_perm, y_test_2stage_without_perm = df_2stage_test_without_perm.drop(columns=['targets']).values, df_2stage_test_without_perm['targets'].values
    score_without_perm = score_function(var_fit_model, X_test_2stage_without_perm, y_test_2stage_without_perm)['mean_loss']
    # compute error by PERMUTATING WITH feature of interest
    X_test_perm_with[:, set_feat2perm] = run_row_permutation_set_features(seed, X_test_augm, set_feat2perm)
    X_test_perm_with[:, predictor_index] = run_row_permutation_predictor(seed, X_test_augm, predictor_index)
    pred_outsample_perm_with = fit_model.predict(X_test_perm_with)
    df_2stage_with_perm = prepare_second_stage_data(params_model, df_train_ens_augm, df_test_ens, y_train, y_test, pred_insample, pred_outsample_perm_with)
    df_2stage_test_with_perm = df_2stage_with_perm[(df_2stage_with_perm.index >= forecast_range[0]) & (df_2stage_with_perm.index <= forecast_range[-1])]
    X_test_2stage_with_perm, y_test_2stage_with_perm = df_2stage_test_with_perm.drop(columns=['targets']).values, df_2stage_test_with_perm['targets'].values
    score_with_perm = score_function(var_fit_model, X_test_2stage_with_perm, y_test_2stage_with_perm)['mean_loss']
    # return the difference in error
    decrease_error = max(0, score_with_perm - score_without_perm)
    return decrease_error

def compute_col_perm_score(seed, params_model, nr_features, y_test, fitted_model, y_train, var_fitted_model, X_test_augm, df_test_ens, df_train_ens_augm, predictions_insample, score_function, predictor_index, forecast_range, list_set_feat2permutate):
    """Compute  score for a single predictor.
    Args:
        seed (int): The seed for the random number generator.
        params_model (dict): The parameters of the model.
        nr_features (int): The number of features.
        y_test (np.array): The target variable from the previous day.
        fitted_model (object): The fitted model.
        y_train (np.array): The target variable for the training data.
        var_fitted_model (object): The variance of the fitted model.
        X_test_augm (np.array): The augmented test data from the previous day.
        df_test_ens (pd.DataFrame): The test data from the previous day for the ensemble.
        df_train_ens_augm (pd.DataFrame): The training data for the ensemble.
        predictions_insample (np.array): The predictions from the first-stage model.
        score_function (function): The score function.
        predictor_index (int): The index of the predictor to permute.
        forecast_range (list): The forecast range.
        list_set_feat2permutate (list): The list of set of features to permute.
    Returns:
        col_score (float): The score.
        str_set_feat2permutate (str): The set of features to permute.
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
    X_test_perm_with, X_test_perm_without = X_test_augm.copy(), X_test_augm.copy()
    # Compute the scores for each set of combination set
    row_scores = Parallel(n_jobs=params_model['nr_jobs_shapley'])(delayed(compute_row_perm_score)(seed,
                                                                    params_model,
                                                                    set_feat2permutate,
                                                                    predictor_index,
                                                                    y_test,
                                                                    fitted_model, y_train, var_fitted_model, X_test_augm, df_test_ens, df_train_ens_augm,
                                                                    predictions_insample,
                                                                    score_function,
                                                                    X_test_perm_with,
                                                                    X_test_perm_without,
                                                                    forecast_range
                                                                    ) for seed in range(params_model['nr_row_permutations']))
    # Compute the average marginal contribution
    col_score = np.mean(row_scores)
    return col_score, str_set_feat2permutate

def second_stage_shapley_importance(y_test, params_model, quantile, info, forecast_range):
    """ Compute permutation importances for the first stage model.
    Args:
        y_test (np.array): The target variable from the previous day.
        params_model (dict): The parameters of the model.
        quantile (float): The quantile.
        info (dict): The information dictionary.
        forecast_range (list): The forecast range.
    Returns:
        results_df (pd.DataFrame): The DataFrame with the normalized importance scores.
    """
    # get info previous day
    fitted_model, y_train, var_fitted_model, X_test_augm, df_test_ens, df_train_ens, df_train_ens_augm, X_train_augmented, buyer_scaler_stats = extract_data_second_stage(info, quantile)
    # Standardize the observed target
    y_test = (y_test - buyer_scaler_stats['mean_buyer'])/buyer_scaler_stats['std_buyer']
    # Get In-sample Predictions
    predictions_insample = fitted_model.predict(X_train_augmented)
    # Validate inputs
    validate_inputs_shapley_second_stage(params_model, quantile, y_test, X_test_augm)
    # Define the score functions for different quantiles
    score_function = get_score_function(quantile)
    # Initialize the list to store the importance scores
    importance_scores = []
    # Loop through each predictor
    nr_features = X_test_augm.shape[1]
    for predictor_index in range(nr_features):
        # Get the predictor name
        predictor_name = df_train_ens_augm.drop(columns=['norm_targ']).columns[predictor_index]
        col_scores = []
        list_set_feat2permutate = []
        for seed in range(params_model['nr_col_permutations']):
            col_score, set_feat2permutate = compute_col_perm_score(seed, 
                                                                params_model,
                                                                nr_features, 
                                                                y_test, 
                                                                fitted_model, y_train, var_fitted_model, X_test_augm, df_test_ens, 
                                                                df_train_ens,
                                                                predictions_insample, 
                                                                score_function, 
                                                                predictor_index,
                                                                forecast_range, 
                                                                list_set_feat2permutate)
            # Append the importance score to the list
            col_scores.append(col_score)
            # Append the set of features to permute to the list
            list_set_feat2permutate.append(set_feat2permutate)
        # Increment the seed
        seed += 1
        shapley_score = np.mean(col_scores)  # Compute the average marginal contribution
        # Append the importance score to the list
        importance_scores.append({'predictor': predictor_name, 
                                'contribution': shapley_score})
    # Create a DataFrame with the importance scores, sort, and normalize it
    results_df = create_norm_import_scores_df(importance_scores)
    return results_df