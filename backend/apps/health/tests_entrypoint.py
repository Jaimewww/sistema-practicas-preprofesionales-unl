"""Behavior of docker/entrypoint.sh around demo data.

The script runs against a fake ``python`` on PATH that records its arguments,
so these tests check which commands the entrypoint issues without Django or
PostgreSQL.
"""

import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path
from unittest import SkipTest

from django.test import SimpleTestCase

ENTRYPOINT = Path(__file__).resolve().parents[3] / "docker" / "entrypoint.sh"

FAKE_PYTHON = """#!/bin/sh
echo "$*" >> "$CALLS_LOG"
if [ "$*" = "manage.py help seed" ]; then
    exit "${FAKE_HELP_SEED_EXIT:-0}"
fi
exit 0
"""


class EntrypointSeedTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not ENTRYPOINT.exists() or shutil.which("sh") is None:
            raise SkipTest("docker/entrypoint.sh or sh is not available")

    def run_entrypoint(self, **env):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "python"
            fake.write_text(FAKE_PYTHON)
            fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
            log = Path(tmp) / "calls.log"
            base = {
                k: v for k, v in os.environ.items()
                if k not in {"POSTGRES_HOST", "DJANGO_SEED_DEMO"}
            }
            base.update(PATH=f"{tmp}:{os.environ['PATH']}", CALLS_LOG=str(log))
            base.update(env)
            result = subprocess.run(
                ["sh", str(ENTRYPOINT), "true"],
                env=base, capture_output=True, text=True, timeout=30,
            )
            calls = log.read_text().splitlines() if log.exists() else []
        return result, calls

    def test_without_flag_migrates_but_does_not_seed(self):
        result, calls = self.run_entrypoint()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("manage.py migrate --noinput", calls)
        self.assertNotIn("manage.py seed", calls)
        self.assertIn("DJANGO_SEED_DEMO is not True, skipping demo data", result.stdout)

    def test_flag_other_than_literal_true_does_not_seed(self):
        for value in ("true", "1", "yes", "False", ""):
            with self.subTest(value=value):
                result, calls = self.run_entrypoint(DJANGO_SEED_DEMO=value)

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("manage.py seed", calls)

    def test_flag_true_loads_demo_data_after_migrations(self):
        result, calls = self.run_entrypoint(DJANGO_SEED_DEMO="True")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("manage.py seed", calls)
        self.assertLess(
            calls.index("manage.py migrate --noinput"), calls.index("manage.py seed")
        )
        self.assertIn("entrypoint: loading demo data", result.stdout)

    def test_flag_true_without_seed_command_skips_demo_data(self):
        result, calls = self.run_entrypoint(
            DJANGO_SEED_DEMO="True", FAKE_HELP_SEED_EXIT="1"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("manage.py seed", calls)
        self.assertIn("entrypoint: no seed command yet, skipping demo data", result.stdout)
