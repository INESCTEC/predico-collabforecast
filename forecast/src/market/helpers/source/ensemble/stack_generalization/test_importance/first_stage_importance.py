from loguru import logger

from .first_stage_permutation import first_stage_permutation_importance
from .first_stage_shapley import first_stage_shapley_importance

def wind_power_importance(results_challenge_dict, ens_params, y_test, results_contributions):
    """ Get the importance of the wind power 
    Args:
        results_challenge_dict: Dictionary with the results of the challenge
        ens_params: Dictionary with the ensemble parameters
        y_test: Series with the true values
        results_contributions: Dictionary with the contributions of the forecasters
    Returns:
        results_contributions: Dictionary with the contributions of the forecasters"""
    # Validate inputs
    assert 'wind_power' in results_challenge_dict.keys(), 'The key wind_power_variability is not present in the results_challenge_dict'
    assert 'info_contributions' in results_challenge_dict['wind_power'].keys(), 'The key info_contributions is not present in the results_challenge_dict'
    assert 'quantiles' in ens_params.keys(), 'The key quantiles is not present in the ens_params'
    assert 'nr_permutations' in ens_params.keys(), 'The key nr_permutations is not present in the ens_params'
    # Log the information
    logger.opt(colors=True).info(f'<blue>--</blue>' * 79)
    logger.opt(colors=True).info(f'<blue>Wind Power</blue>')
    # Get the info from the previous day
    info_previous_day_first_stage = results_challenge_dict['wind_power']['info_contributions']
    logger.info(f'Contribution method: {ens_params["contribution_method"]}')
    # Get the contributions per quantile
    for quantile in ens_params['quantiles']:
        logger.opt(colors=True).info(f'<blue>Quantile: {quantile}</blue>')
        # Get the contributions
        if ens_params['contribution_method'] == 'shapley':
            col_permutation = ens_params['nr_col_permutations']
            row_permutation = ens_params['nr_row_permutations']
            logger.info(f'Number of column permutations: {col_permutation}')
            logger.info(f'Number of row permutations: {row_permutation}')
            # Compute the contributions using the Shapley method
            df_contributions = first_stage_shapley_importance(
                                                            y_test=y_test, 
                                                            params_model=ens_params, 
                                                            quantile=quantile, 
                                                            info_previous_day_first_stage=info_previous_day_first_stage
                                                            )
        elif ens_params['contribution_method'] == 'permutation':
            num_permutations = ens_params['nr_permutations']
            logger.info(f'Number of permutations: {num_permutations}')
            # Compute the contributions using the permutation method
            df_contributions = first_stage_permutation_importance(
                                                                    y_test=y_test, 
                                                                    params_model=ens_params, 
                                                                    quantile=quantile, 
                                                                    info_previous_day_first_stage=info_previous_day_first_stage
                                                                )
        else:
            raise ValueError('The contribution method is not implemented')
        # Get the predictor name
        df_contributions['predictor'] = df_contributions['predictor'].apply(lambda x: x.split('_')[1])
        # Save the contributions
        results_contributions['wind_power'][quantile] = dict(df_contributions.groupby('predictor')['contribution'].sum())
    return results_contributions