# flake8: noqa

import os
from loguru import logger
from dataclasses import dataclass

# solver for quantile regression
from sklearn.utils.fixes import parse_version, sp_version
# set solver for quantile regression
solver = "highs" if sp_version >= parse_version("1.6.0") else "interior-point"

# Pathing:
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Logs Configs:
LOGS_DIR = os.path.join(BASE_PATH, "files", "logs")

# -- Initialize Logger:
logs_kw = dict(
    format="{time:YYYY-MM-DD HH:mm:ss} | {level:<5} | {message}",
    rotation="1 week",
    compression="zip",
    backtrace=True,
)
logger.add(os.path.join(LOGS_DIR, "info_log.log"), level='INFO', **logs_kw)
logger.add(os.path.join(LOGS_DIR, "debug_log.log"), level='DEBUG', **logs_kw)

# REST Configs:
RESTAPI_PROTOCOL = os.environ.get('RESTAPI_PROTOCOL', "http")
RESTAPI_HOST = os.environ.get('RESTAPI_HOST', "")
RESTAPI_PORT = os.environ.get('RESTAPI_PORT', "")
N_REQUEST_RETRIES = os.environ.get('N_REQUEST_RETRIES', 3)

# Market Configs:
MARKET_EMAIL = os.environ.get('MARKET_EMAIL', "")
MARKET_PASSWORD = os.environ.get('MARKET_PASSWORD', "")
N_JOBS = int(os.environ.get("N_JOBS", 1))
MARKET_FORECAST_HORIZON = "D+1"
MARKET_DATA_TIME_RESOLUTION = "15Min"
QUANTILES = ["q10", "q50", "q90"]


# Database configs:
DATABASES = {
    'default': {
        'NAME': os.environ.get("POSTGRES_DB", default=''),
        'USER': os.environ.get("POSTGRES_USER", default=''),
        'PASSWORD': os.environ.get("POSTGRES_PASSWORD", default=''),
        'HOST': os.environ.get("POSTGRES_HOST", default=''),
        'PORT': int(os.environ.get("POSTGRES_PORT", default=5432)),
    }
}

# Model configs:
SESSIONS_DIR = os.path.join(BASE_PATH, "files", "sessions")
MODEL_FILES_DIR = os.path.join(BASE_PATH, "files", "models")
os.makedirs(MODEL_FILES_DIR, exist_ok=True)


@dataclass(frozen=True)
class Stack:
    params = dict(

        # path to save the model
        save_info=MODEL_FILES_DIR, 

        # prediction pipeline
        quantiles=[0.1, 0.9, 0.5],
        baseline_model='diff_norm_dayahead',

        # ------- Ensemble Learning

        # scaler
        scale_features = True,
        axis=0,
        normalize = False,
        standardize = True,

        # feature augmentation
        add_quantile_predictions=True,
        augment_q50=False,

        solver = solver,
        nr_cv_splits=5,
        hyperparam_update_every_days=1,

        # ----- wind power

        # select-model
        model_type='LR',  # 'GBR' or 'LR'
        
        # feature-engineering
        forecasters_diversity=True,
        add_lags=True,
        max_lags=2,
        augment_with_poly=True,
        augment_with_roll_stats=False,
        differenciate=False,

        # gradient boosting regressor
        gbr_config_params={'learning_rate': [0.00001, 0.0001, 0.001, 0.005, 0.01],
                            'max_features': [.85, .95, 1.0],
                            'max_depth': [3, 4],
                            'max_iter': [350]},

        # linear regression
        lr_config_params={'alpha': [0.000001, 0.00001, 0.0001, 0.001, 0.005],
                            'fit_intercept': [True, False]},

        # ------ wind power variability

        # select-model
        var_model_type='LR',  # 'GBR' or 'LR'

        # feature-engineering
        add_lags_var=True,
        max_lags_var = 3,
        order_diff = 1,
        augment_with_poly_var=True,
        differenciate_var = False,

        # gradient boosting regressor
        var_gbr_config_params={'learning_rate': [0.001, 0.005, 0.01],
                                'max_features': [.85, .95, 1.0],
                                'max_depth': [3, 4],
                                'max_iter': [10]},

        # linear regression
        var_lr_config_params={'alpha': [0.000001, 0.00001, 0.0001, 0.001, 0.005],
                                'fit_intercept': [True, False]},

        # ------ wind power ramp detection

        # preprocessing
        preprocess_ramps=False,
        percentage = 0.3,
        installed_capacity = None,
        # quantile threshold
        threshold_quantile=0.97,
        # alarm policy
        max_consecutive_points=3, 


        # ------ forecasters contribution assessment
        contribution_method = 'shapley',  # 'shapley' or 'permutation'

        # permutation importance
        nr_permutations = 50,
        nr_jobs_permutation = 4, # number of jobs for the permutation importance

        # shapely importance
        nr_row_permutations = 10,
        nr_col_permutations = 10,
        nr_jobs_shapley = -1, # number of jobs for the shapley importance

        compute_second_stage=True,
    )
