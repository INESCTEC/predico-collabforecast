import gc
import pickle
import pytz
from loguru import logger
import pandas as pd

from .utils.session_ml_info import (
    load_or_initialize_results, set_timestamps, get_buyer_resource_name
)
from .utils.data_preprocess import (
    scale_forecasters_dataframe, scale_buyer_dataframe,
    buyer_scaler_statistics, impute_mean_for_nan
)
from .utils.data_preprocess import rescale_predictions, rescale_targets
from .utils.data_preprocess import (
    set_non_negative_predictions, drop_nans_with_warning,
    check_minimum_data_training
)
from .ensemble.stack_generalization.feature_engineering.data_augmentation import create_augmented_dataframe  # noqa
from .ensemble.stack_generalization.data_preparation.data_train_test import (
    split_train_test_data, split_quantile_train_test_data,
    concatenate_feat_targ_dataframes, get_numpy_Xy_train_test,
    get_numpy_Xy_train_test_quantile, extract_quantile_columns
)
from .ensemble.stack_generalization.ensemble_model import (
    predico_ensemble_predictions_per_quantile,
    predico_ensemble_variability_predictions
)
from .ensemble.stack_generalization.second_stage.create_data_second_stage import (
    create_2stage_dataframe, create_augmented_dataframe_2stage,
    create_var_ensemble_dataframe, get_numpy_Xy_train_test_2stage,
    prepare_pre_test_data
)
from .ensemble.stack_generalization.utils.results import (
    collect_quantile_ensemble_predictions,
    create_ensemble_dataframe, melt_dataframe
)


def create_ensemble_forecasts(ens_params,
                              launch_time,
                              forecast_range,
                              df_buyer,
                              df_market,
                              challenge_usecase,
                              challenge_id):
    """ Create ensemble forecasts for wind power and wind power variability using forecasters predictions
    Args:
        ens_params (dict): dictionary with the parameters for the ensemble learning.
        launch_time (datetime): launch time.
        forecast_range (list): forecast range.
        df_buyer (pd.DataFrame): DataFrame with the buyer data.
        df_market (pd.DataFrame): DataFrame with the market data.
        challenge_usecase (str): challenge usecase.
        challenge_id (int): challenge id.
    Returns:
        forecasts (pd.DataFrame): DataFrame with the ensemble forecasts.
        results_challenge_dict (dict): dictionary with the results for the ensemble learning.
        """

    # Set Coordinated Universal Time
    utc = pytz.UTC

    # Set the launch time and forecast range
    timestamps = set_timestamps(launch_time, forecast_range, utc)

    end_observation_timestamp = timestamps['end_observation_timestamp']  # training end timestamp
    start_prediction_timestamp = timestamps['start_prediction_timestamp']  # start prediction timestamp
    end_prediction_timestamp = timestamps['end_prediction_timestamp']  # end prediction timestamp

    # Load or initialize results
    file_info, iteration, best_results, best_results_var = load_or_initialize_results(params=ens_params, challenge_id=challenge_id)

    # Extract quantile columns with checks
    df_ensemble_quantile50 = extract_quantile_columns(df_market, 'q50')  # get the quantile 50 predictions
    # impute mean for NaN values by looping over columns
    if not df_ensemble_quantile50.empty:
        df_ensemble_quantile50 = impute_mean_for_nan(df_ensemble_quantile50)

    df_ensemble_quantile10 = extract_quantile_columns(df_market, 'q10')  # get the quantile 10 predictions
    # impute mean for NaN values by looping over columns
    if not df_ensemble_quantile10.empty:
        df_ensemble_quantile10 = impute_mean_for_nan(df_ensemble_quantile10)

    df_ensemble_quantile90 = extract_quantile_columns(df_market, 'q90')  # get the quantile 90 predictions
    # impute mean for NaN values by looping over columns
    if not df_ensemble_quantile90.empty:
        df_ensemble_quantile90 = impute_mean_for_nan(df_ensemble_quantile90)

    # Ensure at least one quantile DataFrame is not empty
    if df_ensemble_quantile50.empty:
        raise ValueError("Quantile columns 'q50' were not found in the DataFrame.")

    # get buyer resource name
    buyer_resource_name = get_buyer_resource_name(df_buyer)

    # Check if the model type is LR then normalize must be True
    if ens_params['model_type'] == 'LR':
        assert ens_params['normalize'] == True or ens_params['standardize'] == True, "Normalize or Standardize must be True for model_type 'LR'"

    # ML ENGINE PREDICO PLATFORM
    logger.info(' ')
    logger.opt(colors=True).info(f'<fg 250,128,114> PREDICO Machine Learning Engine </fg 250,128,114> ')
    logger.info('   ')
    logger.opt(colors=True).info(f'<fg 250,128,114> Iteration {iteration} </fg 250,128,114>')
    logger.info('  ')
    logger.opt(colors=True).info(f'<fg 250,128,114> Launch Time: {end_observation_timestamp} </fg 250,128,114> ')
    logger.info('  ')
    logger.opt(colors=True).info(f'<fg 250,128,114> Predictions from {str(start_prediction_timestamp)} to {str(end_prediction_timestamp)} </fg 250,128,114> ')
    logger.info('  ')
    logger.opt(colors=True).info(f'<fg 250,128,114> Buyer Resource Name: {buyer_resource_name} </fg 250,128,114>')

    # check rescale_features is true if Normalize is True or Standardize is True
    assert not (ens_params['normalize'] or ens_params['standardize'] and not ens_params['scale_features']), 'scale_features must be True if normalize or standardize is True'

    # check if normalize and standardize are not both True
    assert not (ens_params['normalize'] and ens_params['standardize']), 'normalize and standardize cannot both be True'

    # scale features
    buyer_scaler_stats = buyer_scaler_statistics(ens_params, df_buyer, end_observation_timestamp, buyer_resource_name)

    # Logging
    logger.opt(colors=True).info(f'<fg 250,128,114> Collecting forecasters prediction for ensemble learning - model: {ens_params["model_type"]} </fg 250,128,114>')
    logger.info('  ')
    logger.opt(colors=True).info(f'<fg 250,128,114> Forecasters Ensemble DataFrame </fg 250,128,114>')
    logger.info('   ')

    # Scale dataframes
    df_ensemble_normalized, df_ensemble_normalized_quantile10, df_ensemble_normalized_quantile90 = scale_forecasters_dataframe(ens_params, buyer_scaler_stats, df_ensemble_quantile50, df_ensemble_quantile10, df_ensemble_quantile90, end_observation_timestamp)

    # Augment dataframes
    logger.info('   ')
    logger.opt(colors=True).info(f'<fg 250,128,114> Augment DataFrame </fg 250,128,114>')
    df_ensemble_normalized_lag = create_augmented_dataframe(
        df_ensemble_normalized,
        max_lags=ens_params['max_lags'],
        forecasters_diversity=ens_params['forecasters_diversity'],
        add_lags=ens_params['add_lags'],
        augment_with_poly=ens_params['augment_with_poly'],
        augment_with_roll_stats=ens_params['augment_with_roll_stats'],
        differenciate=ens_params['differenciate'],
        end_train=end_observation_timestamp,
        start_pred = start_prediction_timestamp,
        end_pred = end_prediction_timestamp)

    # Augment dataframes quantile predictions
    if ens_params['add_quantile_predictions']:
        logger.opt(colors=True).info(f'<fg 250,128,114> -- Augment quantile predictions </fg 250,128,114>')

        if not df_ensemble_normalized_quantile10.empty:
            # Augment with predictions quantile 10
            df_ensemble_normalized_lag_quantile10 = create_augmented_dataframe(
                df_ensemble_normalized_quantile10,
                max_lags=ens_params['max_lags'],
                forecasters_diversity=ens_params['forecasters_diversity'],
                add_lags=ens_params['add_lags'],
                augment_with_poly=ens_params['augment_with_poly'],
                augment_with_roll_stats=ens_params['augment_with_roll_stats'],
                differenciate=ens_params['differenciate'],
                end_train=end_observation_timestamp,
                start_pred = start_prediction_timestamp,
                end_pred = end_prediction_timestamp)
        else:
            df_ensemble_normalized_lag_quantile10 = pd.DataFrame()

        if not df_ensemble_normalized_quantile90.empty:
            # Augment with predictions quantile 90
            df_ensemble_normalized_lag_quantile90 = create_augmented_dataframe(
                df_ensemble_normalized_quantile90,
                max_lags=ens_params['max_lags'],
                forecasters_diversity=ens_params['forecasters_diversity'],
                add_lags=ens_params['add_lags'],
                augment_with_poly=ens_params['augment_with_poly'],
                augment_with_roll_stats=ens_params['augment_with_roll_stats'],
                differenciate=ens_params['differenciate'],
                end_train=end_observation_timestamp,
                start_pred = start_prediction_timestamp,
                end_pred = end_prediction_timestamp)
        else:
            df_ensemble_normalized_lag_quantile90 = pd.DataFrame()
    else:
        df_ensemble_normalized_lag_quantile10, df_ensemble_normalized_lag_quantile90 = pd.DataFrame(), pd.DataFrame()

    # Scale buyer dataframe
    df_buyer_norm = scale_buyer_dataframe(ens_params, buyer_scaler_stats, df_buyer)

    # Split train and test dataframes
    df_train_ensemble, df_test_ensemble = split_train_test_data(df=df_ensemble_normalized_lag,
                                                                end_train=end_observation_timestamp,
                                                                start_prediction=start_prediction_timestamp,
                                                                end_prediction=end_prediction_timestamp)

    df_train_norm, df_test_norm = split_train_test_data(df=df_buyer_norm,
                                                        end_train=end_observation_timestamp,
                                                        start_prediction=start_prediction_timestamp,
                                                        end_prediction=end_prediction_timestamp)

    df_train_ensemble, df_test_ensemble = concatenate_feat_targ_dataframes(buyer_resource_name = buyer_resource_name,
                                                                           df_train_ensemble=df_train_ensemble,
                                                                           df_test_ensemble=df_test_ensemble,
                                                                           df_train=df_train_norm, df_test=df_test_norm,
                                                                           max_lag=ens_params['max_lags'])

    # # Split train and test dataframes quantile predictions
    if ens_params['add_quantile_predictions']:
        if not df_ensemble_normalized_quantile10.empty:
            # Quantile 10
            df_train_ensemble_quantile10, df_test_ensemble_quantile10 = split_quantile_train_test_data(df_ensemble_normalized_lag_quantile10,
                                                                                                       end_observation_timestamp,
                                                                                                       start_prediction_timestamp,
                                                                                                       end_prediction_timestamp)
        else:
            df_train_ensemble_quantile10, df_test_ensemble_quantile10 = pd.DataFrame(), pd.DataFrame()

        if not df_ensemble_normalized_quantile90.empty:
            # Quantile 90
            df_train_ensemble_quantile90, df_test_ensemble_quantile90 = split_quantile_train_test_data(df_ensemble_normalized_lag_quantile90,
                                                                                                       end_observation_timestamp,
                                                                                                       start_prediction_timestamp,
                                                                                                       end_prediction_timestamp)
        else:
            df_train_ensemble_quantile90, df_test_ensemble_quantile90 = pd.DataFrame(), pd.DataFrame()
    else:
        df_train_ensemble_quantile10 = df_test_ensemble_quantile10 = df_train_ensemble_quantile90 = df_test_ensemble_quantile90 = pd.DataFrame()

    # Assert df_test matches df_ensemble_test
    assert (df_test_norm.index == df_test_ensemble.index).all(), 'Datetime index are not equal'

    # assert df_train_ensemble.isna().sum().sum() == 0
    drop_nans_with_warning(df_train_ensemble)
    # Reindex train ensemble quantile dataframes accordingly:
    df_train_ensemble_quantile10 = df_train_ensemble_quantile10.reindex(df_train_ensemble.index)
    df_train_ensemble_quantile90 = df_train_ensemble_quantile90.reindex(df_train_ensemble.index)

    # raise exception if not enough data
    check_minimum_data_training(df_train_ensemble, minimum_rows = 4*24*20)  # minimum 20 days of data

    # Make X-y train and test sets
    X_train, y_train, X_test, _ = get_numpy_Xy_train_test(df_train_ensemble, df_test_ensemble)

    # Make X-y train and test sets quantile
    X_train_quantile10, X_test_quantile10, X_train_quantile90, X_test_quantile90 = get_numpy_Xy_train_test_quantile(ens_params,
                                                                                                                    df_train_ensemble_quantile10,
                                                                                                                    df_test_ensemble_quantile10,
                                                                                                                    df_train_ensemble_quantile90,
                                                                                                                    df_test_ensemble_quantile90
                                                                                                                    )

    # Run ensemble learning
    logger.info('   ')
    logger.opt(colors=True).info(f'<fg 250,128,114> Compute Ensemble Predictions </fg 250,128,114>')

    # dictioanry to store predictions
    predictions = {}
    previous_day_results_first_stage = {}

    # Loop over quantiles
    for quantile in ens_params['quantiles']:
        # Run ensemble learning
        results_quantiel_wp = predico_ensemble_predictions_per_quantile(ens_params=ens_params,
                                                                        X_train=X_train,
                                                                        X_test=X_test,
                                                                        y_train=y_train,
                                                                        df_train_ensemble=df_train_ensemble,
                                                                        predictions=predictions,
                                                                        quantile=quantile,
                                                                        best_results=best_results,
                                                                        iteration=iteration,
                                                                        X_train_quantile10=X_train_quantile10,
                                                                        X_test_quantile10=X_test_quantile10,
                                                                        df_train_ensemble_quantile10=df_train_ensemble_quantile10,
                                                                        X_train_quantile90=X_train_quantile90,
                                                                        X_test_quantile90=X_test_quantile90,
                                                                        df_train_ensemble_quantile90=df_train_ensemble_quantile90)

        # Extract results
        predictions = results_quantiel_wp['predictions']
        best_results = results_quantiel_wp['best_results']
        fitted_model = results_quantiel_wp['fitted_model']
        X_train_augmented = results_quantiel_wp['X_train_augmented']
        X_test_augmented = results_quantiel_wp['X_test_augmented']
        df_train_ensemble_augmented = results_quantiel_wp['df_train_ensemble_augmented']

        # Store results
        previous_day_results_first_stage[quantile] = {
            "fitted_model": fitted_model,
            "X_train_augmented": X_train_augmented,
            "X_test_augmented": X_test_augmented,
            "df_train_ensemble_augmented": df_train_ensemble_augmented,
            "buyer_scaler_stats": buyer_scaler_stats
        }

        # compute variability predictions with as input the predictions of the first stage
        if ens_params['compute_second_stage'] and quantile == 0.5:
            logger.info('   ')
            logger.opt(colors=True).info(f'<fg 72,201,176> Compute Variability Predictions </fg 72,201,176>')

            # Prepare test data second stage
            X_test_augmented, y_test = prepare_pre_test_data(ens_params, quantile, df_test_ensemble, df_test_ensemble_quantile10, df_test_ensemble_quantile90)
            assert 92 <= len(X_test_augmented) <= 100, 'Test dataframe must have between 92 and 100 rows'
            assert 92 <= len(y_test) <= 100, 'Test dataframe must have between 92 and 100 rows'
            assert len(X_test_augmented) == len(y_test), 'Test dataframe must have the same nr of rows in inputs and targets'

            predictions_insample = fitted_model.predict(X_train_augmented)
            predictions_outsample = fitted_model.predict(X_test_augmented)

            # Create 2-stage dataframe
            df_2stage = create_2stage_dataframe(df_train_ensemble, df_test_ensemble, y_train, y_test, predictions_insample, predictions_outsample)

            # Augment 2-stage dataframe
            df_2stage_buyer = create_augmented_dataframe_2stage(df_2stage,
                                                                order_diff = ens_params['order_diff'],
                                                                differentiate=ens_params['differenciate_var'],
                                                                max_lags=ens_params['max_lags_var'],
                                                                add_lags = ens_params['add_lags_var'],
                                                                augment_with_poly=ens_params['augment_with_poly_var'],
                                                                end_train=end_observation_timestamp,
                                                                start_pred = start_prediction_timestamp,
                                                                end_pred = end_prediction_timestamp)

            # Split 2-stage dataframe
            df_2stage_train, df_2stage_test =  split_train_test_data(df=df_2stage_buyer,
                                                                     end_train=end_observation_timestamp,
                                                                     start_prediction=start_prediction_timestamp,
                                                                     end_prediction=end_prediction_timestamp)

            # Split 2-stage dataframe
            X_train_2stage, y_train_2stage, X_test_2stage = get_numpy_Xy_train_test_2stage(df_2stage_train, df_2stage_test)

            # dictioanry to store variability predictions
            variability_predictions = {}
            previous_day_results_second_stage = {}

            # dictioanry to store insample and outsample predictions
            variability_predictions_insample = {}
            variability_predictions_outsample = {}

            # Loop over quantiles
            for quantile in ens_params['quantiles']:
                # Run ensemble learning
                results_quantile_wpv = predico_ensemble_variability_predictions(ens_params=ens_params,
                                                                                X_train_2stage=X_train_2stage,
                                                                                y_train_2stage=y_train_2stage,
                                                                                X_test_2stage=X_test_2stage,
                                                                                variability_predictions=variability_predictions,
                                                                                quantile=quantile,
                                                                                iteration=iteration,
                                                                                best_results_var=best_results_var,
                                                                                variability_predictions_insample =  variability_predictions_insample,
                                                                                variability_predictions_outsample = variability_predictions_outsample
                                                                                )

                # Extract results
                variability_predictions = results_quantile_wpv['variability_predictions']
                variability_predictions_insample = results_quantile_wpv['variability_predictions_insample']
                variability_predictions_outsample = results_quantile_wpv['variability_predictions_outsample']
                best_results_var = results_quantile_wpv['best_results_var']
                var_fitted_model = results_quantile_wpv['var_fitted_model']

                # Store results
                previous_day_results_second_stage[quantile] = {
                    "fitted_model": fitted_model,
                    "var_fitted_model": var_fitted_model,
                    "X_train_augmented": X_train_augmented,
                    "X_test_augmented": X_test_augmented,
                    "df_train_ensemble_augmented": df_train_ensemble_augmented,
                    "df_train_ensemble": df_train_ensemble,
                    "df_test_ensemble": df_test_ensemble,
                    "y_train": y_train,
                    "buyer_scaler_stats": buyer_scaler_stats
                }

                # Rescale predictions for predictions
                variability_predictions = rescale_predictions(variability_predictions, ens_params, buyer_scaler_stats, quantile, stage='2nd')
                # insample and outsample predictions for wind ramp detection
                variability_predictions_insample = rescale_predictions(variability_predictions_insample, ens_params, buyer_scaler_stats, quantile, stage='2nd')
                variability_predictions_outsample = rescale_predictions(variability_predictions_outsample, ens_params, buyer_scaler_stats, quantile, stage='2nd')

                # Transform predictions to dataframe with index name 'datetime'
                var_pred_insample_df = pd.DataFrame(variability_predictions_insample, index=df_2stage_train.index)
                var_pred_outsample_df = pd.DataFrame(variability_predictions_outsample, index=df_2stage_test.index)

            # Rescale inputs for predictions
            target_name = 'targets'
            df_2stage_test = rescale_targets(ens_params, buyer_scaler_stats, df_2stage_test, target_name, stage='2nd')

            # Collect quantile variability predictions
            var_predictions_dict = collect_quantile_ensemble_predictions(
                ens_params['quantiles'],
                df_2stage_test,
                variability_predictions)

            # collect results as dataframe
            df_var_ensemble = create_var_ensemble_dataframe(
                ens_params['quantiles'],
                var_predictions_dict,
                df_2stage_test
            )

            # melt dataframe
            df_var_ensemble_melt = melt_dataframe(df_var_ensemble)
            del df_2stage, df_2stage_buyer, df_2stage_train
            gc.collect()

        # Rescale predictions
        predictions = rescale_predictions(predictions, ens_params, buyer_scaler_stats, quantile, stage='1st')

        # Ensure predictions are positive
        predictions = set_non_negative_predictions(predictions, quantile)

        # Delete variables
        del X_train_augmented, X_test_augmented, df_train_ensemble_augmented
        gc.collect()  # garbage collection

    # Rescale observations
    target_name = 'norm_' + buyer_resource_name
    df_test = rescale_targets(ens_params, buyer_scaler_stats, df_test_norm, target_name, stage='1st')

    # Collect quantile predictions
    quantile_predictions_dict = collect_quantile_ensemble_predictions(ens_params['quantiles'],
                                                                      df_test,
                                                                      predictions)

    # collect results as dataframe
    df_pred_ensemble = create_ensemble_dataframe(ens_params['quantiles'],
                                                 quantile_predictions_dict,
                                                 df_test)

    # melt dataframe
    df_pred_ensemble_melt = melt_dataframe(df_pred_ensemble)

    # collect results as dictionary of dictionaries
    results_challenge_dict = {'iteration': iteration,
                              'wind_power':
                                  {'predictions': df_pred_ensemble_melt,
                                   'info_contributions': previous_day_results_first_stage,
                                   'best_results': best_results},
                              'wind_power_ramp':
                                  {'predictions': df_var_ensemble_melt,
                                   'info_contributions': previous_day_results_second_stage,
                                   'best_results': best_results_var,
                                   'predictions_outsample': var_pred_outsample_df,
                                   'predictions_insample': var_pred_insample_df}
                              }

    # assert challenge_usecase is either wind_power or wind_power_ramp
    assert challenge_usecase == 'wind_power' or challenge_usecase == 'wind_power_ramp', 'challenge_usecase must be either "wind_power" or "wind_power_ramp"'

    # save results
    with open(file_info, 'wb') as handle:
        pickle.dump(results_challenge_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

    # return forecasts
    forecasts = results_challenge_dict[challenge_usecase]['predictions']

    return forecasts, results_challenge_dict
