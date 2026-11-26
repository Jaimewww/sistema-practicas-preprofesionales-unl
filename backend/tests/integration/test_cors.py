"""CORS del frontend Angular contra la API real (APE-006, S2-S3).

El frontend corre en ``ng serve`` (``http://localhost:4200``) y la API en otro
origen, así que el navegador exige CORS **solo para ese origen**. El contrato es
explícito: nada de ``CORS_ALLOW_ALL_ORIGINS``.

Las pruebas miran el HTTP (cabeceras y cuerpo del envelope), no la
configuración de Django: un preflight ``OPTIONS`` desde el origen permitido
recibe ``Access-Control-Allow-Origin``; uno desde otro origen no; y una
respuesta normal desde el origen permitido también la repite. El cuerpo sigue
siendo el envelope de ADR-0012: CORS agrega cabeceras, no cambia el contrato.
"""

from django.test import TestCase

RUTA = "/api/v1/practicas/"
ORIGEN_PERMITIDO = "http://localhost:4200"
ORIGEN_AJENO = "http://evil.example"
CABECERA_ORIGEN = "Access-Control-Allow-Origin"
CLAVES_ENVELOPE = {"success", "message", "data", "errors", "meta"}


class CorsPreflightTests(TestCase):
    """``ng serve`` en :4200 puede llamar a /api/v1/; cualquier otro origen no."""

    def preflight(self, origen):
        """Preflight real del navegador: OPTIONS con Origin + método pedido."""
        return self.client.options(
            RUTA,
            HTTP_ORIGIN=origen,
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
        )

    def test_preflight_desde_el_origen_permitido_recibe_la_cabecera(self):
        respuesta = self.preflight(ORIGEN_PERMITIDO)

        self.assertEqual(respuesta.headers.get(CABECERA_ORIGEN), ORIGEN_PERMITIDO)
        self.assertEqual(respuesta.status_code, 200)

    def test_preflight_desde_otro_origen_no_recibe_la_cabecera(self):
        respuesta = self.preflight(ORIGEN_AJENO)

        self.assertNotIn(CABECERA_ORIGEN, respuesta.headers)

    def test_get_desde_el_origen_permitido_tambien_recibe_la_cabecera(self):
        # Sin sesión la API responde 401 con el envelope; el navegador necesita
        # la cabecera CORS incluso en los errores para que el front los lea.
        respuesta = self.client.get(RUTA, HTTP_ORIGIN=ORIGEN_PERMITIDO)

        self.assertEqual(respuesta.headers.get(CABECERA_ORIGEN), ORIGEN_PERMITIDO)
        self.assertEqual(set(respuesta.json()), CLAVES_ENVELOPE)
