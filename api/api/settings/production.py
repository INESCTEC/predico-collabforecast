from .base import *

DEBUG = False

# Logging:
# -- Normal log handlers:
MAIN_LOG_HANDLERS.append("console")
MAIN_LOG_HANDLERS.append("json_debug")
EXCEPTION_LOG_HANDLERS.append("console")
EXCEPTION_LOG_HANDLERS.append("json_debug")