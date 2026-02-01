import numpy as np

from sklearn.model_selection import TimeSeriesSplit
from sklearn.ensemble import HistGradientBoostingRegressor

from .utils.cross_validation import evaluate

def optimize_gbr(X_train, y_train, quantile, nr_cv_splits, params):
    " Hyperparameter optimization for Quantile Gradient Boosting Regressor."
    assert isinstance(X_train, np.ndarray), "X_train should be a numpy array"
    assert isinstance(y_train, np.ndarray), "y_train should be a numpy array"
    assert quantile in [0.1, 0.5, 0.9], "Invalid quantile value. Must be 0.1, 0.5, or 0.9."
    assert isinstance(nr_cv_splits, int), "nr_cv_splits should be an integer"
    assert isinstance(params, dict), "params should be a dictionary"
    assert 'learning_rate' in params, "learning_rate must be provided"
    #assert 'max_features' in params, "max_features must be provided"
    assert 'max_depth' in params, "max_depth must be provided"
    assert 'max_iter' in params, "max_iter must be provided"
    assert params['learning_rate'] is not None, 'learning_rate must be provided'
    #assert params['max_features'] is not None, 'max_features must be provided'
    assert params['max_depth'] is not None, 'max_depth must be provided'
    assert params['max_iter'] is not None, 'max_iter must be provided'
    best_gbr_params = None
    best_score=np.exp(10000)
    ts_cv = TimeSeriesSplit(n_splits=nr_cv_splits)
    for learning_rate in params['learning_rate']:
        #for max_feat in params['max_features']:
            for max_depth in params['max_depth']:
                for n_estimators in params['max_iter']:
                    gbr_params = dict(
                        learning_rate=learning_rate,
                        #max_features = max_feat,
                        max_iter=n_estimators,
                        max_depth=max_depth,
                        random_state=42)
                    if quantile == 0.5:
                        gbr = HistGradientBoostingRegressor(**gbr_params)
                    else:
                        gbr = HistGradientBoostingRegressor(loss="quantile", quantile=quantile, **gbr_params)
                    mean_cv_score = evaluate(gbr, X_train, y_train, cv=ts_cv, quantile=quantile) 
                    if mean_cv_score < best_score:
                        best_score = mean_cv_score
                        best_gbr_params = gbr_params
    return best_score, best_gbr_params