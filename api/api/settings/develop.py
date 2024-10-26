from .base import *

DEBUG = True
ACCOUNT_VERIFICATION = os.getenv('ACCOUNT_VERIFICATION', 'false').lower() == 'true'  # noqa

# Logging:
MAIN_LOG_HANDLERS.append("console")
