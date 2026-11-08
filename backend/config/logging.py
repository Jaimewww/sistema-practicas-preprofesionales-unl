"""Logging configuration (dictConfig), imported by settings.py."""

import os
import sys

# Keep the test run quiet; assertLogs still captures INFO records.
DEFAULT_LEVEL = 'WARNING' if sys.argv[1:2] == ['test'] else 'INFO'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'request_id': {'()': 'apps.observability.logging.RequestIdFilter'},
    },
    'formatters': {
        'json': {'()': 'apps.observability.logging.JsonFormatter'},
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
            'filters': ['request_id'],
        },
    },
    'root': {
        'handlers': ['console'],
        'level': os.getenv('DJANGO_LOG_LEVEL', DEFAULT_LEVEL),
    },
}
