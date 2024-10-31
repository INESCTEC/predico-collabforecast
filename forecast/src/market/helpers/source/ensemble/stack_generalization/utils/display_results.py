from loguru import logger

def display_forecasting_metrics(ens_params, rmse_ensemble, rmse_weighted_avg, rmse_equal_weights,
                                rmse_dayahead, rmse_dayahead_11h, rmse_week_ahead,
                                pinball_ensemble_q10=None, pinball_weighted_avg_q10=None, pinball_equal_weights_q10=None,
                                pinball_dayahead_q10=None, pinball_dayahead_11h_q10=None, pinball_week_ahead_q10=None,
                                pinball_ensemble_q90=None, pinball_weighted_avg_q90=None, pinball_equal_weights_q90=None,
                                pinball_dayahead_q90=None, pinball_dayahead_11h_q90=None, pinball_week_ahead_q90=None,
                                rmse_var_ensemble=None, rmse_var_weighted_avg=None, rmse_var_equal_weights=None,
                                rmse_var_dayahead=None, rmse_var_dayahead_11h=None, rmse_var_week_ahead=None):
    
    logger.info(' ')
    logger.info('------------- Wind Power Forecasting ------------------------------')
    logger.info('----------------- RMSE -----------------')
    logger.info(f'GBR Stacked {rmse_ensemble}')
    logger.info(f'Weighted Average {rmse_weighted_avg}')
    logger.info(f'Equal Weights {rmse_equal_weights}')
    logger.info(f'Day-Ahead {rmse_dayahead}')
    logger.info(f'Day-Ahead-11h {rmse_dayahead_11h}')
    logger.info(f'Week-Ahead {rmse_week_ahead}')
    logger.info(' ')

    if not ens_params['compute_abs_difference']:
        logger.info('----------------- PB Q10 -----------------')
        logger.info(f'PB Q10 GBR Stacked {pinball_ensemble_q10}')
        logger.info(f'PB Q10 Weig Avg {pinball_weighted_avg_q10}')
        logger.info(f'PB Q10 Eq Weig {pinball_equal_weights_q10}')
        logger.info(f'PB Q10 Day-Ahead {pinball_dayahead_q10}')
        logger.info(f'PB Q10 Day-Ahead-11h {pinball_dayahead_11h_q10}')
        logger.info(f'PB Q10 Week-Ahead {pinball_week_ahead_q10}')
        logger.info(' ')
        logger.info('----------------- PB Q90 -----------------')
        logger.info(f'GBR Stacked {pinball_ensemble_q90}')
        logger.info(f'Weig Avg {pinball_weighted_avg_q90}')
        logger.info(f'Eq Weig {pinball_equal_weights_q90}')
        logger.info(f'Day-Ahead {pinball_dayahead_q90}')
        logger.info(f'Day-Ahead-11h {pinball_dayahead_11h_q90}')
        logger.info(f'Week-Ahead {pinball_week_ahead_q90}')
        logger.info(' ')
        logger.info('----------------- Wind Power Variability Forecast -----------------')
        logger.info('----------------- RMSE -----------------')
        logger.info(f'GBR Stacked {rmse_var_ensemble}')
        logger.info(f'Weighted Average {rmse_var_weighted_avg}')
        logger.info(f'Equal Weights {rmse_var_equal_weights}')
        logger.info(f'Day-Ahead {rmse_var_dayahead}')
        logger.info(f'Day-Ahead-11h {rmse_var_dayahead_11h}')
        logger.info(f'Week-Ahead {rmse_var_week_ahead}')
        logger.info(' ')