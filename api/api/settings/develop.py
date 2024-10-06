from .base import *

DEBUG = True
ACCOUNT_VERIFICATION = os.getenv('ACCOUNT_VERIFICATION', 'false').lower() == 'true'  # noqa

# Logging:
# Note: currently only request/response logs are being issued.
# See logger call in `api.renderers.CustomRenderer`
# -- Normal log handlers:
MAIN_LOG_HANDLERS.append("console")
# MAIN_LOG_HANDLERS.append("json_file")
# MAIN_LOG_HANDLERS.append("text_file")

# -- Database log handlers (save DB queries for debug):
# DB_LOG_HANDLERS.append("console")
# DB_LOG_HANDLERS.append("text_file")
