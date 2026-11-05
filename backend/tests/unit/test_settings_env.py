"""Contrato de entorno de ``config.settings`` (S4, issue #76).

Cada escenario importa ``backend/config/settings.py`` en un proceso nuevo con
``os.environ`` limpio —sin ``DJANGO_*`` ni ``POSTGRES_*`` heredadas— y lo ejecuta
con ``runpy.run_path``: así el fallo cerrado de ``DJANGO_SECRET_KEY`` se observa
de verdad y la configuración ya cargada de la suite nunca se toca.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase

BACKEND = Path(__file__).resolve().parents[2]
CLAVE_DEMO = "clave-de-prueba-para-el-probe"
ENTORNO_POSTGRES = {
    "POSTGRES_HOST": "base.interna",
    "POSTGRES_PORT": "6543",
    "POSTGRES_DB": "practicas",
    "POSTGRES_USER": "practicas_app",
    "POSTGRES_PASSWORD": "secreto-del-compose",
}

PROBE = """
import json
import runpy

ajustes = runpy.run_path("config/settings.py")
base = ajustes["DATABASES"]["default"]
print(json.dumps({
    "SECRET_KEY": ajustes["SECRET_KEY"],
    "DEBUG": ajustes["DEBUG"],
    "ALLOWED_HOSTS": ajustes["ALLOWED_HOSTS"],
    "ENGINE": base["ENGINE"],
    "NAME": str(base["NAME"]),
    "USER": base.get("USER", ""),
    "PASSWORD": base.get("PASSWORD", ""),
    "HOST": base.get("HOST", ""),
    "PORT": str(base.get("PORT", "")),
}))
"""


def ejecutar(**entorno):
    """Importa settings en otro proceso con el entorno heredado limpio."""
    limpio = {
        clave: valor
        for clave, valor in os.environ.items()
        if not clave.startswith(("DJANGO_", "POSTGRES_"))
    }
    limpio.update(entorno)
    limpio["PYTHONPATH"] = str(BACKEND)
    return subprocess.run(
        [sys.executable, "-c", PROBE],
        check=False,
        cwd=BACKEND,
        env=limpio,
        capture_output=True,
        text=True,
        timeout=60,
    )


def ejecutar_con_clave(**entorno):
    """Probe del camino feliz: la clave de demo se pone antes de importar."""
    entorno.setdefault("DJANGO_SECRET_KEY", CLAVE_DEMO)
    return ejecutar(**entorno)


def ajustes(**entorno):
    resultado = ejecutar_con_clave(**entorno)
    if resultado.returncode != 0:
        raise AssertionError(resultado.stderr)
    return json.loads(resultado.stdout)


class SecretKeyTests(SimpleTestCase):
    """S4: ``DJANGO_SECRET_KEY`` sin valor por defecto en código, fallo cerrado."""

    def test_ausente_y_debug_apagado_falla_cerrado(self):
        resultado = ejecutar()

        self.assertEqual(resultado.returncode, 1, resultado.stderr)
        self.assertEqual(resultado.stdout, "")
        self.assertIn("Traceback", resultado.stderr)
        self.assertIn("ImproperlyConfigured", resultado.stderr)
        self.assertIn("DJANGO_SECRET_KEY", resultado.stderr)

    def test_ausente_y_debug_encendido_arranca_con_clave_efimera(self):
        """S4 literal: solo falla si falta Y DEBUG está apagado; en dev es efímera."""
        resultado = ejecutar(DJANGO_DEBUG="True")

        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        cuerpo = json.loads(resultado.stdout)
        self.assertIs(cuerpo["DEBUG"], True)
        self.assertNotEqual(cuerpo["SECRET_KEY"], "")
        # La clave efímera no es un valor fijado en el código: cada proceso
        # genera una distinta y el literal de la clave demo NO está en settings.
        second = ejecutar(DJANGO_DEBUG="True")
        self.assertNotEqual(json.loads(second.stdout)["SECRET_KEY"], cuerpo["SECRET_KEY"])

    def test_se_lee_del_entorno(self):
        self.assertEqual(ajustes()["SECRET_KEY"], CLAVE_DEMO)


class BordesDeSeleccionPostgresTests(SimpleTestCase):
    """El conmutador de base reacciona solo a HOST o DB, no a PORT solitario."""

    def test_solo_postgres_port_no_activa_postgres(self):
        base = ajustes(POSTGRES_PORT="6543")
        self.assertEqual(base["ENGINE"], "django.db.backends.sqlite3")

    def test_postgres_host_vacio_no_activa_postgres(self):
        base = ajustes(POSTGRES_HOST="")
        self.assertEqual(base["ENGINE"], "django.db.backends.sqlite3")


class DebugTests(SimpleTestCase):
    """``DJANGO_DEBUG`` se parsea desde el entorno y apagado es el defecto."""

    def test_apagado_por_defecto(self):
        self.assertIs(ajustes()["DEBUG"], False)

    def test_solo_el_literal_true_enciende_debug(self):
        self.assertIs(ajustes(DJANGO_DEBUG="True")["DEBUG"], True)

    def test_cualquier_otro_valor_deja_debug_apagado(self):
        for valor in ("true", "1", "YES", "False", "false", "0", "quizá"):
            with self.subTest(valor=valor):
                self.assertIs(ajustes(DJANGO_DEBUG=valor)["DEBUG"], False)


class AllowedHostsTests(SimpleTestCase):
    """``DJANGO_ALLOWED_HOSTS`` es una lista separada por comas."""

    def test_lee_la_lista_y_descarta_espacios_y_vacios(self):
        ajustes_hosts = ajustes(DJANGO_ALLOWED_HOSTS="a.example, b.example ,")

        self.assertEqual(ajustes_hosts["ALLOWED_HOSTS"], ["a.example", "b.example"])

    def test_la_lista_sin_espacios_se_comporta_igual(self):
        ajustes_hosts = ajustes(DJANGO_ALLOWED_HOSTS="a.example,b.example")

        self.assertEqual(ajustes_hosts["ALLOWED_HOSTS"], ["a.example", "b.example"])

    def test_sin_variable_queda_vacia(self):
        self.assertEqual(ajustes()["ALLOWED_HOSTS"], [])


class DatabasesTests(SimpleTestCase):
    """S4: motor PostgreSQL con ``POSTGRES_*``; sqlite solo como respaldo local."""

    def test_sin_variables_usa_sqlite_local(self):
        base = ajustes()

        self.assertEqual(base["ENGINE"], "django.db.backends.sqlite3")
        self.assertTrue(base["NAME"].endswith("db.sqlite3"))
        self.assertEqual(base["PASSWORD"], "")
        self.assertEqual(base["USER"], "")

    def test_postgres_host_activa_el_motor_y_lee_las_variables(self):
        base = ajustes(**ENTORNO_POSTGRES)

        self.assertEqual(base["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(base["NAME"], "practicas")
        self.assertEqual(base["USER"], "practicas_app")
        self.assertEqual(base["PASSWORD"], "secreto-del-compose")
        self.assertEqual(base["HOST"], "base.interna")
        self.assertEqual(base["PORT"], "6543")

    def test_solo_postgres_db_tambien_activa_postgres(self):
        base = ajustes(POSTGRES_DB="practicas")

        self.assertEqual(base["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(base["NAME"], "practicas")
        self.assertEqual(base["HOST"], "localhost")
        self.assertEqual(base["PORT"], "5432")

    def test_sin_password_no_inventa_credenciales(self):
        base = ajustes(POSTGRES_HOST="base.interna")

        self.assertEqual(base["PASSWORD"], "")
        self.assertEqual(base["USER"], "")
