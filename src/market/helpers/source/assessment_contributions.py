import os

from loguru import logger
from .ensemble.stack_generalization.test_importance.utils import load_model_info
from .ensemble.stack_generalization.test_importance.forecasters_contributions import calculate_contributions


def compute_forecasters_contributions(buyer_resource_name, ens_params, df_y_test, previous_day_forecast_range, use_case, challenge_id):
    " Compute the contributions of the forecasters for the buyer resource"
    assert isinstance(buyer_resource_name, str), 'The buyer_resource_name must be a string'
    file_name = 'wp_' + ens_params['model_type'] + '_wpr_' + ens_params['var_model_type'] + '.pickle'
    file_info = os.path.join(ens_params['save_info'], str(challenge_id), file_name)
    logger.info(f"Load model info from file: {file_info}")
    results_challenge_dict = load_model_info(file_info)
    if results_challenge_dict is None:
        raise FileNotFoundError(f"File not found in {file_info}.")
    logger.info(f"Get the contributions for the buyer resource: {buyer_resource_name}")
    results_contributions_ = calculate_contributions(results_challenge_dict, ens_params, df_y_test, previous_day_forecast_range)

    results_contributions_ = results_contributions_[use_case]

    # Convert dict keys to quantile str:
    results_contributions = {}
    for variable, contributions in results_contributions_.items():
        formatted_key = f"q{int(variable * 100):02d}"  # Format the key as qXX
        results_contributions[formatted_key] = contributions

    return results_contributions
