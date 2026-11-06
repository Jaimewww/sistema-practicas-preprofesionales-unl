"""Configuración compartida de la suite bajo pytest-django (#80).

Tiene dos responsabilidades, ninguna de ellas reescribe pruebas:

1. **Settings y clave secreta efímera.** ``DJANGO_SETTINGS_MODULE`` y
   ``DJANGO_SECRET_KEY`` se exportan acá, no en ``pytest.ini``: pytest-django
   carga settings en ``pytest_load_initial_conftests``, antes de importar este
   archivo, así que el ini no puede declarar el módulo de settings si además
   queremos correr sin exportar la clave a mano. ``config.settings`` no trae
   valor por defecto para ``DJANGO_SECRET_KEY`` (contrato S4) y falla cerrada con
   DEBUG apagado. Si la variable no llega del entorno, este conftest genera una
   clave efímera de proceso con ``get_random_secret_key()``: nunca se imprime,
   nunca se escribe en disco y cada corrida usa una distinta (nada depende de su
   valor). Si CI o el compose de #81 la exportan, se respeta ese valor
   (``setdefault``).

2. **Marcado automático por ruta** (#80, S2). La suite existente es
   ``unittest.TestCase`` y se corre nativa bajo pytest-django, así que la
   clasificación sale del módulo, no de decoradores por prueba:

   ==================================================  ============
   Módulo de test                                      Marcador(es)
   ==================================================  ============
   ``tests/unit/**``                                   ``unit``
   ``tests/integration/**``                            ``integration``
   nombre con ``auth_seguridad``                       ``security``
   nombre con ``test_reportes_flujo``                  ``api``
   nombre con ``test_asignacion``                      ``api``
   nombre con ``test_api``                             ``api``
   ==================================================  ============

   Un módulo puede llevar varios: ``tests/integration/test_auth_seguridad.py``
   es ``integration`` + ``security``, y ``tests/unit/test_asignacion_*.py`` es
   ``unit`` + ``api``. Los cuatro marcadores están registrados en
   ``pytest.ini`` y ese archivo corre con ``--strict-markers``: este conftest
   solo aplica marcadores registrados, así que un marcador desconocido siempre
   falla en la configuración y nunca se ignora en silencio.
"""

import os
from pathlib import Path

import pytest

VARIABLE_CLAVE = "DJANGO_SECRET_KEY"
VARIABLE_SETTINGS = "DJANGO_SETTINGS_MODULE"


def _configurar_django_para_pytest():
    """Exporta settings + clave efímera y deja Django listo para pytest-django.

    Corre al importar este conftest, es decir después del preparse de
    pytest-django y antes de su ``pytest_configure``: por eso el setup se hace
    acá y el plugin lo ve idempotente (``apps.ready`` ya es True).
    """
    os.environ.setdefault(VARIABLE_SETTINGS, "config.settings")
    if not os.environ.get(VARIABLE_CLAVE):
        from django.core.management.utils import get_random_secret_key

        os.environ[VARIABLE_CLAVE] = get_random_secret_key()

    import django

    django.setup()


_configurar_django_para_pytest()

DIRECTORIO_TESTS = Path(__file__).resolve().parent / "tests"

# Marcadores por ruta de paquete: el prefijo se compara contra la ruta relativa
# a backend/tests/ para no depender del directorio desde el que se invoca.
MARCADORES_POR_CARPETA = {
    "unit/": "unit",
    "integration/": "integration",
}

# Marcadores por nombre de archivo: cubren la superficie HTTP y la de
# seguridad sin importar en qué carpeta viva el módulo.
MARCADORES_POR_NOMBRE = (
    ("auth_seguridad", "security"),
    ("test_reportes_flujo", "api"),
    ("test_asignacion", "api"),
    ("test_api", "api"),
)


def _marcadores_del_modulo(ruta):
    """Devuelve los marcadores que corresponden al archivo de test ``ruta``.

    La tabla SOLO se aplica bajo tests/: los módulos legacy de apps/prototipo,
    apps/health y config no reciben marcadores por diseño (decisión #80).
    """
    ruta = Path(str(ruta))
    try:
        relativa = ruta.resolve().relative_to(DIRECTORIO_TESTS).as_posix()
    except ValueError:  # fuera de tests/: sin clasificación automática
        return ()

    marcadores = [
        marcador
        for prefijo, marcador in MARCADORES_POR_CARPETA.items()
        if relativa.startswith(prefijo)
    ]
    marcadores.extend(
        marcador
        for fragmento, marcador in MARCADORES_POR_NOMBRE
        if fragmento in ruta.name
    )
    return tuple(marcadores)


def pytest_collection_modifyitems(items):
    """Aplica los marcadores de ruta; nunca duplica los ya declarados."""
    for item in items:
        for marcador in _marcadores_del_modulo(item.path):
            if item.get_closest_marker(marcador) is None:
                item.add_marker(getattr(pytest.mark, marcador))
