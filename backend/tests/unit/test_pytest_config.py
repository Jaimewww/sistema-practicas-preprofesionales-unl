"""Sondas de regresión para la configuración de pytest y de cobertura (#80, S2/S3/S4).

Son ``SimpleTestCase`` (no funciones sueltas de pytest) para que corran igual con
``manage.py test`` y con ``python -m pytest``: la suite tiene un solo conjunto de
pruebas, no uno por runner. Cada sonda lanza un pytest hijo desde ``backend/``.
"""

import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from django.test import SimpleTestCase

RAIZ = Path(__file__).resolve().parents[2]


def _correr(*args, **entorno_extra):
    """Shell limpio simulado: sin clave ni settings heredados del runner padre."""
    entorno = {**os.environ, **entorno_extra}
    for clave in ("DJANGO_SECRET_KEY", "DJANGO_SETTINGS_MODULE"):
        entorno.pop(clave, None)
    return subprocess.run(
        [sys.executable, "-m", "pytest", *args], cwd=RAIZ, env=entorno,
        capture_output=True, text=True,
    )


def _ids_recolectados(*args):
    """Ids de los tests que pytest recolecta con ``args`` (``--collect-only -q``)."""
    r = _correr("--collect-only", "-q", *args)
    assert r.returncode == 0, r.stdout + r.stderr
    return [linea for linea in r.stdout.splitlines() if "::" in linea]


class PytestConfigTests(SimpleTestCase):
    def test_cov_documentado_mide_apps_y_config_y_escribe_xml(self):
        """S3: ``--cov`` sin valor lee ``source`` de .coveragerc y escribe el XML.

        Sonar lee ``backend/coverage.xml``; el reporte debe medir ``apps`` y
        ``config`` y no los tests ni el conftest.
        """
        with tempfile.TemporaryDirectory() as tmp:
            reporte = Path(tmp) / "coverage.xml"
            r = _correr(
                "--cov", f"--cov-report=xml:{reporte}", "--cov-report=term-missing",
                "--collect-only", "-q",
                COVERAGE_FILE=str(Path(tmp) / ".coverage"),
            )
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue(reporte.exists(), "pytest --cov no escribió el XML")
            raiz = ET.parse(reporte).getroot()
            fuentes = [Path(f.text).name for f in raiz.iter("source")]
            archivos = [c.get("filename") for c in raiz.iter("class")]
        # Con dos `source` coverage escribe cada archivo relativo a su fuente:
        # los de config/ cuelgan de "." y los de apps/ de su app.
        self.assertEqual(sorted(fuentes), ["apps", "config"])
        self.assertIn("settings.py", archivos)
        self.assertIn("usuarios/models.py", archivos)
        medidos_de_tests = [
            f for f in archivos
            if f == "conftest.py" or f.startswith("tests/") or "test" in Path(f).stem
        ]
        self.assertEqual(medidos_de_tests, [], "--cov midió tests o conftest")

    def test_la_cobertura_vive_en_coveragerc_y_no_en_pytest_ini(self):
        """pytest-cov no lee ``[coverage:*]`` de pytest.ini: sería letra muerta."""
        secciones = [
            linea for linea in (RAIZ / "pytest.ini").read_text().splitlines()
            if linea.startswith("[coverage")
        ]
        self.assertEqual(secciones, [])
        coveragerc = (RAIZ / ".coveragerc").read_text()
        self.assertIn("[run]", coveragerc)
        self.assertIn("source", coveragerc)

    def test_arranca_sin_django_secret_key_y_no_la_filtra(self):
        r = _correr("--collect-only", "-q")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("DJANGO_SECRET_KEY", r.stdout + r.stderr)

    def test_strict_markers_sin_registro_falla(self):
        """Sin marcadores registrados, ``--strict-markers`` falla y nombra el marcador.

        No se fija el exit code (pytest cambia entre INTERNALERROR=3 y usage=4
        según la versión): importa que no pase en silencio.
        """
        r = _correr("--collect-only", "-q", "-o", "markers=")
        salida = r.stdout + r.stderr
        self.assertNotEqual(r.returncode, 0, salida)
        self.assertRegex(salida, r"'(unit|integration|api|security)' not found")

    def test_security_marca_los_modulos_de_seguridad(self):
        ids = _ids_recolectados("-m", "security")
        modulos = {i.split("::")[0] for i in ids}
        self.assertIn("tests/unit/test_seguridad.py", modulos)
        self.assertIn("tests/integration/test_auth_seguridad.py", modulos)
        self.assertIn("tests/integration/test_auth_sesion.py", modulos)

    def test_api_marca_los_tests_del_envelope(self):
        ids = _ids_recolectados("-m", "api")
        modulos = {i.split("::")[0] for i in ids}
        self.assertIn("tests/unit/test_envelope_exceptions.py", modulos)
        self.assertIn("tests/unit/test_envelope_renderer.py", modulos)
