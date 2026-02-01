from loguru import logger

from .feature_engineering.data_augmentation import augment_with_quantiles
from .hyperparam_optimization.optimization import optimize_model, initialize_model


def initialize_train_and_predict(predictions, model_type, quantile, best_params, solver, X_train, y_train, X_test, 
                                insample=False, 
                                predictions_insample=None, 
                                predictions_outsample=None):
    """
    Initializes, fits a model, and makes predictions.
    """
    # Initialize model with best params
    model = initialize_model(model_type, quantile, best_params, solver)
    # Fit model
    fitted_model = model.fit(X_train, y_train)
    # Make predictions
    predictions[quantile] = fitted_model.predict(X_test)
    # Return fitted model and predictions
    if not insample:
        return fitted_model, predictions
    elif insample:
        predictions_insample[quantile] = fitted_model.predict(X_train)
        predictions_outsample[quantile] = fitted_model.predict(X_test) 
        return fitted_model, predictions, predictions_insample, predictions_outsample

def predico_ensemble_predictions_per_quantile(ens_params, 
                                                X_train, X_test, y_train,
                                                df_train_ensemble,
                                                predictions, quantile,
                                                iteration, 
                                                best_results,
                                                X_train_quantile10=None,
                                                X_test_quantile10=None,
                                                df_train_ensemble_quantile10=None,
                                                X_train_quantile90=None,
                                                X_test_quantile90=None,
                                                df_train_ensemble_quantile90=None):
    """ Run ensemble predictions for a specific quantile."""
    logger.info('   ')
    logger.opt(colors=True).info(f'<fg 250,128,114> Run ensemble predictions for quantile {quantile} </fg 250,128,114>')

    # Initialize variables
    add_quantiles = ens_params['add_quantile_predictions']
    augment_q50 = ens_params['augment_q50']
    nr_cv_splits = ens_params['nr_cv_splits']
    model_type = ens_params['model_type']
    solver = ens_params['solver']
    hyperparam_update_every_days = ens_params['hyperparam_update_every_days']
    gbr_config_params = ens_params['gbr_config_params']
    lr_config_params = ens_params['lr_config_params']

    assert model_type in ['GBR', 'LR'], 'Invalid model type'

    # Initialize variables
    X_train_augmented, X_test_augmented, df_train_ensemble_augmented = X_train, X_test, df_train_ensemble

    # Augment the training and testing data with the quantiles predictions
    if add_quantiles:
        logger.opt(colors=True).info(f'<fg 250,128,114> Augmenting training and testing data with quantiles </fg 250,128,114>')

        # Augment the training and testing data with the quantiles predictions
        X_train_augmented, X_test_augmented, df_train_ensemble_augmented = augment_with_quantiles(
            X_train, X_test, df_train_ensemble,
            X_train_quantile10, X_test_quantile10,
            df_train_ensemble_quantile10,
            X_train_quantile90, X_test_quantile90,
            df_train_ensemble_quantile90,
            quantile, augment_q50=augment_q50)
        
    # Optimize model hyperparameters
    if iteration % hyperparam_update_every_days == 0:  # Optimize hyperparameters every hyperparam_update_every_days
        logger.opt(colors=True).info(f'<fg 250,128,114> Optimizing model hyperparameters - updating every {hyperparam_update_every_days} days</fg 250,128,114>')

        # Optimize model hyperparameters
        best_score, best_params = optimize_model(X_train_augmented, y_train,
                                                    quantile,
                                                    nr_cv_splits, model_type,
                                                    solver, gbr_config_params,
                                                    lr_config_params)
        # Store best results
        best_results[quantile] = [('best_score', best_score),
                                    ('params', best_params)]
    else:
        logger.opt(colors=True).info(f'<fg 250,128,114> Using best hyperparameters from first iteration </fg 250,128,114>')
        best_params = best_results[quantile][1][1]

    # Initialize, fit and predict
    fitted_model, predictions = initialize_train_and_predict(predictions, model_type, quantile, best_params, solver, X_train_augmented, y_train, X_test_augmented)

    # Store results
    results = {'predictions': predictions,
                'best_results': best_results,
                'fitted_model': fitted_model,
                'X_train_augmented': X_train_augmented,
                'X_test_augmented': X_test_augmented,
                'df_train_ensemble_augmented': df_train_ensemble_augmented}
    return results


def predico_ensemble_variability_predictions(ens_params,
                                                X_train_2stage, 
                                                y_train_2stage,
                                                X_test_2stage,
                                                variability_predictions, 
                                                quantile,
                                                iteration,
                                                best_results_var,
                                                variability_predictions_insample,
                                                variability_predictions_outsample):
    " Run ensemble variability predictions"
    logger.opt(colors=True).info(f'<fg 72,201,176> Run ensemble variability predictions for quantile {quantile} </fg 72,201,176>')

    # Initialize variables
    nr_cv_splits=ens_params['nr_cv_splits']
    var_model_type=ens_params['var_model_type']
    solver=ens_params['solver']
    var_gbr_config_params=ens_params['var_gbr_config_params']
    var_lr_config_params=ens_params['var_lr_config_params']
    hyperparam_update_every_days=ens_params['hyperparam_update_every_days']
    
    assert var_model_type in ['GBR', 'LR'], 'Invalid model type'

    # Optimize model hyperparameters
    if iteration % hyperparam_update_every_days == 0:  # Optimize hyperparameters every hyperparam_update_every_days
        logger.opt(colors=True).info(f'<fg 72,201,176> Optimizing model hyperparameters - updating every {hyperparam_update_every_days} days</fg 72,201,176>')

        # Optimize model hyperparameters
        best_score, best_params_var = optimize_model(X_train_2stage,
                                                        y_train_2stage, 
                                                        quantile,
                                                        nr_cv_splits,
                                                        var_model_type,
                                                        solver,
                                                        var_gbr_config_params,
                                                        var_lr_config_params)
        
        # Store best results
        best_results_var[quantile] = [('best_score', best_score),
                                        ('params', best_params_var)]
    else:
        logger.opt(colors=True).info(f'<fg 72,201,176> Using best hyperparameters from first iteration </fg 72,201,176>')
        best_params_var = best_results_var[quantile][1][1]

    # Initialize, fit and predict
    var_fitted_model, variability_predictions, variability_predictions_insample, variability_predictions_outsample = initialize_train_and_predict(variability_predictions, var_model_type, quantile, best_params_var, solver, X_train_2stage, y_train_2stage, X_test_2stage,
                                                                                insample=True,
                                                                                predictions_insample = variability_predictions_insample,
                                                                                predictions_outsample = variability_predictions_outsample)
    
    # store results
    results = {'variability_predictions': variability_predictions,
                'best_results_var': best_results_var,
                'var_fitted_model': var_fitted_model,
                'variability_predictions_insample': variability_predictions_insample,
                'variability_predictions_outsample': variability_predictions_outsample}
    return results