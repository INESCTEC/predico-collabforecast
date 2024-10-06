import os

ENVIRONMENT = os.environ['DJANGO_APPLICATION_ENVIRONMENT']

if ENVIRONMENT == 'develop':
    SETTINGS_MODULE = 'api.settings.develop'

if ENVIRONMENT == 'production':
    SETTINGS_MODULE = 'api.settings.production'

if ENVIRONMENT == 'test':
    SETTINGS_MODULE = 'api.settings.test'
