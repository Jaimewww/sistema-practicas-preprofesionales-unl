"""El demo X-Rol vive fuera de ``/api/v1/`` y la API real no lo obedece (#79, L9).

El demo del prototipo elige personas sintéticas con ``X-Rol`` y no autentica a nadie.
Antes compartía el prefijo ``/api/v1/`` con la API real y solo ``DEBUG`` lo separaba;
ahora vive en ``/prototipo/api/v1/`` y la frontera de la API real no depende de una
bandera (RNF-01, ADR 0011): una ruta de negocio con ``X-Rol`` y sin token responde 401
con el envelope, con ``DEBUG`` encendido y apagado.
"""

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.prototipo import facade

PAYLOAD = {"semana": 1, "horas_reportadas": 8}
RUTAS_DEL_DEMO = (
    "alertas/",
    "practicas/1/historial/",
    "pendientes/reporte-1-8/",
    "practicas/7/cierre/",
    "anexos/802/legalizacion/",
)
RUTAS_DE_NEGOCIO = (
    ("get", "/api/v1/practicas/"),
    ("get", "/api/v1/practicas/1/"),
    ("post", "/api/v1/practicas/1/reportes/"),
)
CLAVES_ENVELOPE = {"success", "message", "data", "errors", "meta"}


class DemoFueraDeApiV1Tests(TestCase):
    def test_el_demo_responde_bajo_prototipo_con_debug_encendido(self):
        with override_settings(DEBUG=True):
            respuesta = self.client.get(
                "/prototipo/api/v1/alertas/", headers={"x-rol": "coordinador"}
            )

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("alertas", respuesta.json())

    def test_el_demo_se_cierra_con_debug_apagado(self):
        with override_settings(DEBUG=False):
            respuesta = self.client.get(
                "/prototipo/api/v1/alertas/", headers={"x-rol": "coordinador"}
            )

        self.assertEqual(respuesta.status_code, 404)

    def test_las_rutas_del_demo_ya_no_existen_bajo_api_v1(self):
        for debug in (True, False):
            for ruta in RUTAS_DEL_DEMO:
                with self.subTest(debug=debug, ruta=ruta), override_settings(DEBUG=debug):
                    for metodo in ("get", "post", "patch"):
                        respuesta = getattr(self.client, metodo)(
                            f"/api/v1/{ruta}", headers={"x-rol": "coordinador"}
                        )
                        self.assertEqual(respuesta.status_code, 404)


class RutasDeNegocioIgnoranXRolTests(TestCase):
    """Con X-Rol y sin token no hay identidad: 401 con el envelope, en cualquier modo."""

    def test_x_rol_sin_token_responde_401_con_debug_encendido_y_apagado(self):
        cliente = APIClient()
        for debug in (True, False):
            for rol in facade.ROLES_DEMO:
                for metodo, ruta in RUTAS_DE_NEGOCIO:
                    with self.subTest(debug=debug, rol=rol, ruta=ruta), \
                            override_settings(DEBUG=debug):
                        respuesta = getattr(cliente, metodo)(
                            ruta, PAYLOAD if metodo == "post" else None,
                            format="json", headers={"x-rol": rol},
                        )

                        self.assertEqual(respuesta.status_code, 401)
                        cuerpo = respuesta.json()
                        self.assertEqual(set(cuerpo), CLAVES_ENVELOPE)
                        self.assertIs(cuerpo["success"], False)
                        self.assertEqual(cuerpo["errors"]["code"], "no_autenticado")
