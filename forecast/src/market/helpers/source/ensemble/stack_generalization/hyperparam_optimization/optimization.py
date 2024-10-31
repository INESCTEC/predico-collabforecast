from loguru import logger
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import QuantileRegressor, Lasso

from .models.quantile_gbr import optimize_gbr
from .models.quantile_lr import optimize_lr


def optimize_model(X_train, y_train, quantile, nr_cv_splits, model_type, solver, gbr_config_params, lr_config_params):
    " Optimize selected model hyperparameters."
    if model_type == 'GBR':
        best_score, best_params = optimize_gbr(X_train, y_train, quantile, nr_cv_splits, gbr_config_params)
    elif model_type == 'LR':
        best_score, best_params = optimize_lr(X_train, y_train, quantile, nr_cv_splits, solver, lr_config_params)
    else:
        raise ValueError('"model_type" is not valid')
    logger.info(f'best_score {round(best_score, 3)}')
    logger.info(f'best_params {best_params}')
    return best_score, best_params


def initialize_model(model_type, quantile, best_params, solver):
    " Initialize selected model."
    assert best_params is not None, "Best parameters must be provided"
    if model_type == 'GBR':
        if quantile == 0.5:
            model = HistGradientBoostingRegressor(**best_params)
        else:
            model = HistGradientBoostingRegressor(loss="quantile", quantile=quantile, **best_params)
    elif model_type == 'LR':
        if quantile == 0.5:
            model = Lasso(**best_params)
        else:
            model = QuantileRegressor(quantile=quantile, solver=solver, **best_params)
    else:
        raise ValueError('"model_type" is not valid')
    return model