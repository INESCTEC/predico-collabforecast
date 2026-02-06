# flake8: noqa

import os
from loguru import logger

# Pathing:
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Logs Configs:
LOGS_DIR = os.path.join(BASE_PATH, "files", "logs")

# Scores CSV backup configs:
SCORES_DIR = os.path.join(BASE_PATH, "files", "scores_backup")
os.makedirs(SCORES_DIR, exist_ok=True)

# -- Initialize Logger:
logs_kw = dict(
    format="{time:YYYY-MM-DD HH:mm:ss} | {level:<5} | {message}",
    rotation="1 week",
    compression="zip",
    backtrace=True,
)
logger.add(os.path.join(LOGS_DIR, "info_log.log"), level="INFO", **logs_kw)
logger.add(os.path.join(LOGS_DIR, "debug_log.log"), level="DEBUG", **logs_kw)

# REST Configs:
RESTAPI_PROTOCOL = os.environ.get("RESTAPI_PROTOCOL", "http")
RESTAPI_HOST = os.environ.get("RESTAPI_HOST", "")
RESTAPI_PORT = os.environ.get("RESTAPI_PORT", "")
N_REQUEST_RETRIES = os.environ.get("N_REQUEST_RETRIES", 3)

# Market Configs:
MARKET_EMAIL = os.environ.get("MARKET_EMAIL", "")
MARKET_PASSWORD = os.environ.get("MARKET_PASSWORD", "")
N_JOBS = int(os.environ.get("N_JOBS", 1))
MARKET_FORECAST_HORIZON = "D+1"
MARKET_DATA_TIME_RESOLUTION = "15Min"
QUANTILES = ["q10", "q50", "q90"]
ENSEMBLE_MODELS = ["weighted_avg"]


# Database configs:
DATABASES = {
    "default": {
        "NAME": os.environ.get("POSTGRES_DB", default=""),
        "USER": os.environ.get("POSTGRES_USER", default=""),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", default=""),
        "HOST": os.environ.get("POSTGRES_HOST", default=""),
        "PORT": int(os.environ.get("POSTGRES_PORT", default=5432)),
    }
}

# Sessions files directory:
SESSIONS_DIR = os.path.join(BASE_PATH, "files", "sessions")

# Forecasters submission assessment:
# 1) Number of days used to calculate forecast scores in the assessment report
# (these values are used as weights to the weighted avg ensembles)
SCORES_CALCULATION_DAYS = 6

# 2) Check if a forecaster has a minimum of N days with submissions
# in the previous Y days (lookback). Forecasters that do not fulfil this
# requirement will not be considered in the ensemble.
MIN_SUBMISSION_DAYS_LOOKBACK = 7  # Analysis for the past X days
MIN_SUBMISSION_DAYS = 6  # Must have at least X days with submissions

# 3) Grace period (in days from start of month) during which score recalculation
# includes the previous month. After this day, only the current month is updated.
SCORE_RECALC_GRACE_PERIOD_DAYS = 2

if MIN_SUBMISSION_DAYS > MIN_SUBMISSION_DAYS_LOOKBACK:
    raise ValueError(
        "MIN_SUBMISSION_DAYS must be less than or equal to "
        "MIN_SUBMISSION_DAYS_LOOKBACK."
    )
