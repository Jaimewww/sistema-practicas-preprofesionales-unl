import importlib
import os
from unittest import mock

from django.test import SimpleTestCase

from config import settings as settings_module


class DebugDefaultTests(SimpleTestCase):
    """DEBUG must stay off unless DJANGO_DEBUG=True is set explicitly."""

    def _debug_with_env(self, env):
        base = {k: v for k, v in os.environ.items() if k != "DJANGO_DEBUG"}
        with mock.patch.dict(os.environ, {**base, **env}, clear=True):
            return importlib.reload(settings_module).DEBUG

    def tearDown(self):
        importlib.reload(settings_module)

    def test_debug_is_off_when_variable_is_unset(self):
        self.assertFalse(self._debug_with_env({}))

    def test_debug_is_on_when_variable_is_true(self):
        self.assertTrue(self._debug_with_env({"DJANGO_DEBUG": "True"}))

    def test_debug_is_off_for_any_other_value(self):
        self.assertFalse(self._debug_with_env({"DJANGO_DEBUG": "False"}))
        self.assertFalse(self._debug_with_env({"DJANGO_DEBUG": "1"}))
