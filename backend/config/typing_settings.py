"""Load the real Django model registry for mypy without deployment settings."""

import os
from importlib import import_module
from unittest.mock import patch

with patch.dict(
    os.environ, {"DJANGO_DEBUG": "True", "POSTGRES_HOST": "", "POSTGRES_DB": ""}
):
    _app_settings = import_module("config.settings")

globals().update(
    {name: value for name, value in vars(_app_settings).items() if name.isupper()}
)
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
