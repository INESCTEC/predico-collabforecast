import numpy as np

from sklearn.model_selection import cross_validate
from sklearn.metrics import mean_pinball_loss, mean_squared_error


def score_func_10(estimator, X, y):
    " Evaluate model using Pnball loss for 10% quantile."
    assert X.shape[0] == y.shape[0], "X and y should have the same number of rows"
    y_pred = estimator.predict(X)
    return {
        "mean_loss": mean_pinball_loss(y, y_pred, alpha=0.1),
    }

def score_func_50(estimator, X, y):
    " Evaluate model using MSE loss for 50% quantile."
    assert X.shape[0] == y.shape[0], "X and y should have the same number of rows"
    y_pred = estimator.predict(X)
    return {
        "mean_loss": mean_squared_error(y, y_pred), # mean_pinball_loss(y, y_pred, alpha=0.5),
    }

def score_func_90(estimator, X, y):
    " Evaluate model using Pinball loss for 90% quantile."
    assert X.shape[0] == y.shape[0], "X and y should have the same number of rows"
    y_pred = estimator.predict(X)
    return {
        "mean_loss": mean_pinball_loss(y, y_pred, alpha=0.9),
    }


def evaluate(model, X, y, cv, quantile):
    " Evaluate model using cross-validation."
    assert isinstance(X, np.ndarray), "X should be a numpy array"
    assert isinstance(y, np.ndarray), "y should be a numpy array"
    assert quantile in [0.1, 0.5, 0.9], "Invalid quantile value. Must be 0.1, 0.5, or 0.9."
    score_func = {0.1: score_func_10,
                0.5: score_func_50,
                0.9: score_func_90}
    cv_results = cross_validate(
        model,
        X,
        y,
        cv=cv,
        scoring=score_func[quantile],
        n_jobs=1
    )
    score_mean = cv_results['test_mean_loss'].mean()
    return score_mean