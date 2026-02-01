from loguru import logger

from .second_stage_permutation import second_stage_permutation_importance
from .second_stage_shapley import second_stage_shapley_importance


def wind_power_variability_importance(results_challenge_dict, ens_params, y_test, forecast_range, results_contributions):
    """Get the importance of the wind power ramp
    Args:
        results_challenge_dict: Dictionary with the results of the challenge
        ens_params: Dictionary with the ensemble parameters
        y_test_prev: Series with the true values
        forecast_range: Dictionary with the forecast range
        results_contributions: Dictionary with the contributions of the forecasters
    Returns:
        results_contributions: Dictionary with the contributions of the forecasters
    """
    assert 'wind_power_ramp' in results_challenge_dict.keys(), 'The key wind_power_variability is not present in the results_challenge_dict'
    assert 'info_contributions' in results_challenge_dict['wind_power_ramp'].keys(), 'The key info_contributions is not present in the results_challenge_dict'
    assert 'quantiles' in ens_params.keys(), 'The key quantiles is not present in the ens_params'
    assert 'nr_permutations' in ens_params.keys(), 'The key nr_permutations is not present in the ens_params'
    logger.opt(colors=True).info(f'<blue>--</blue>' * 79)
    logger.opt(colors=True).info(f'<blue>Wind Power Variability</blue>')
    # Get the info from the previous day
    info_previous_day_second_stage = results_challenge_dict['wind_power_ramp']['info_contributions']
    logger.info(f'Contribution method: {ens_params["contribution_method"]}')
    for quantile in ens_params['quantiles']:
        logger.opt(colors=True).info(f'<blue>Quantile: {quantile}</blue>')
        if ens_params['contribution_method'] == 'shapley':
            col_permutation = ens_params['nr_col_permutations']
            row_permutation = ens_params['nr_row_permutations']
            logger.info(f'Number of column permutations: {col_permutation}')
            logger.info(f'Number of row permutations: {row_permutation}')
            # Get the contributions using the SHAPLEY method
            df_contributions = second_stage_shapley_importance(
                                                                y_test=y_test, 
                                                                params_model=ens_params, 
                                                                quantile=quantile, 
                                                                info=info_previous_day_second_stage, 
                                                                forecast_range = forecast_range
                                                            )
        elif ens_params['contribution_method'] == 'permutation':
            num_permutations = ens_params['nr_permutations']
            logger.info(f'Number of permutations: {num_permutations}')
            # Get the contributions
            df_contributions = second_stage_permutation_importance(
                y_test=y_test, 
                parameters_model=ens_params, 
                quantile=quantile, 
                info=info_previous_day_second_stage, 
                forecast_range = forecast_range
            )
        # Get the predictor name
        df_contributions['predictor'] = df_contributions['predictor'].apply(lambda x: x.split('_')[1])
        # Save the contributions
        results_contributions['wind_power_ramp'][quantile] = dict(df_contributions.groupby('predictor')['contribution'].sum())
    return results_contributions