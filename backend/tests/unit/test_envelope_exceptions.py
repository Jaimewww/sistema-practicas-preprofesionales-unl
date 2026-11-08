"""Envelope del contrato en el camino de error (S2-S4, #77).

Misma técnica de ruteo que ``test_envelope_renderer``: las vistas DRF viven en
este módulo y ``urlpatterns`` se activa con
``override_settings(ROOT_URLCONF=__name__)``, sin tocar ``config/urls.py``.

El 500 se observa con ``DEBUG`` apagado (semántica de producción) y también
encendido: el handler devuelve siempre el mismo cuerpo genérico, así que ni la
traza, ni el mensaje de la excepción, ni datos internos salen por el wire.
"""

from unittest import mock

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import SimpleTestCase, override_settings
from django.urls import path
from rest_framework.authentication import BasicAuthentication
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    NotAuthenticated,
    ParseError,
    PermissionDenied as PermisoDRF,
    ValidationError,
)
from rest_framework.views import APIView

CLAVES = {"success", "message", "data", "errors", "meta"}


class SondaValidacionView(APIView):
    def post(self, request):
        raise ValidationError(
            {"nombre": ["Este campo es obligatorio."], "edad": ["Debe ser un entero."]}
        )


class SondaDetalleView(APIView):
    def post(self, request):
        raise ParseError("Cuerpo ilegible.")


class ConflictoError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "El recurso ya existe."
    default_code = "semana_duplicada"


class SondaConflictoView(APIView):
    def post(self, request):
        raise ConflictoError()


class Sonda401View(APIView):
    # BasicAuthentication solo aporta el header WWW-Authenticate: sin él DRF
    # degrada el 401 a 403. La autenticación real (token/JWT) es de #79.
    authentication_classes = [BasicAuthentication]

    def get(self, request):
        raise NotAuthenticated()


class Sonda403View(APIView):
    def get(self, request):
        raise PermissionDenied()


class Sonda403DRFView(APIView):
    def get(self, request):
        raise PermisoDRF()


class Sonda403ConDetalleView(APIView):
    def get(self, request):
        raise PermisoDRF("Solo el coordinador de la carrera puede hacerlo.")


class Sonda404View(APIView):
    def get(self, request):
        raise Http404("no existe")


class Sonda500View(APIView):
    def get(self, request):
        raise RuntimeError("secreto que no debe salir")


urlpatterns = [  # urlconf de pruebas, activo por override_settings(ROOT_URLCONF=__name__)
    path("api/v1/sonda/validacion/", SondaValidacionView.as_view()),
    path("api/v1/sonda/detalle/", SondaDetalleView.as_view()),
    path("api/v1/sonda/conflicto/", SondaConflictoView.as_view()),
    path("api/v1/sonda/protegida/", Sonda401View.as_view()),
    path("api/v1/sonda/restringida/", Sonda403View.as_view()),
    path("api/v1/sonda/restringida-drf/", Sonda403DRFView.as_view()),
    path("api/v1/sonda/restringida-detalle/", Sonda403ConDetalleView.as_view()),
    path("api/v1/sonda/inexistente/", Sonda404View.as_view()),
    path("api/v1/sonda/falla/", Sonda500View.as_view()),
]


@override_settings(ROOT_URLCONF=__name__)
class EnvelopeDeErrorTests(SimpleTestCase):
    """S3: el handler envuelve validación, autenticación, permisos, 404 y 500."""

    def test_400_de_validacion_mapea_campo_a_lista(self):
        cuerpo = self.client.post("/api/v1/sonda/validacion/").json()

        self.assertEqual(set(cuerpo), CLAVES)
        self.assertIs(cuerpo["success"], False)
        self.assertEqual(cuerpo["message"], "Datos inválidos.")
        self.assertEqual(
            cuerpo["errors"],
            {
                "nombre": ["Este campo es obligatorio."],
                "edad": ["Debe ser un entero."],
            },
        )
        self.assertIsNone(cuerpo["data"])
        self.assertEqual(cuerpo["meta"], {})

    def test_400_de_api_exception_usa_detail(self):
        cuerpo = self.client.post("/api/v1/sonda/detalle/").json()

        self.assertIs(cuerpo["success"], False)
        self.assertEqual(cuerpo["message"], "Solicitud inválida.")
        self.assertEqual(
            cuerpo["errors"], {"detail": "Cuerpo ilegible.", "code": "parse_error"}
        )

    def test_409_conserva_su_detail_y_su_code_propio(self):
        respuesta = self.client.post("/api/v1/sonda/conflicto/")

        self.assertEqual(respuesta.status_code, 409)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["message"], "Solicitud inválida.")
        self.assertEqual(
            cuerpo["errors"],
            {"detail": "El recurso ya existe.", "code": "semana_duplicada"},
        )

    def test_401_autenticacion_requerida(self):
        respuesta = self.client.get("/api/v1/sonda/protegida/")

        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(respuesta["WWW-Authenticate"], 'Basic realm="api"')
        cuerpo = respuesta.json()
        self.assertIs(cuerpo["success"], False)
        self.assertEqual(cuerpo["message"], "Autenticación requerida.")
        self.assertEqual(
            cuerpo["errors"],
            {"detail": "Se requiere autenticación.", "code": "no_autenticado"},
        )

    def test_403_permiso_denegado(self):
        respuesta = self.client.get("/api/v1/sonda/restringida/")

        self.assertEqual(respuesta.status_code, 403)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["message"], "Permiso denegado.")
        self.assertEqual(
            cuerpo["errors"],
            {
                "detail": "No tiene permiso para esta operación.",
                "code": "permiso_denegado",
            },
        )

    def test_403_de_drf_sin_texto_propio_usa_el_generico_en_espanol(self):
        errores = self.client.get("/api/v1/sonda/restringida-drf/").json()["errors"]

        self.assertEqual(
            errores,
            {
                "detail": "No tiene permiso para esta operación.",
                "code": "permiso_denegado",
            },
        )

    def test_403_conserva_el_detail_escrito_por_el_servidor(self):
        respuesta = self.client.get("/api/v1/sonda/restringida-detalle/")

        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(
            respuesta.json()["errors"],
            {
                "detail": "Solo el coordinador de la carrera puede hacerlo.",
                "code": "permiso_denegado",
            },
        )

    def test_404_recurso_no_encontrado(self):
        respuesta = self.client.get("/api/v1/sonda/inexistente/")

        self.assertEqual(respuesta.status_code, 404)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["message"], "Recurso no encontrado.")
        self.assertEqual(
            cuerpo["errors"], {"detail": "No encontrado.", "code": "no_encontrado"}
        )

    def test_500_generico_sin_trazas_ni_datos_sensibles(self):
        for debug in (False, True):
            with self.subTest(DEBUG=debug), override_settings(DEBUG=debug), \
                    self.assertLogs("apps.contrato.exceptions", level="ERROR") as registro:
                respuesta = self.client.get("/api/v1/sonda/falla/")

                self.assertEqual(respuesta.status_code, 500)
                cuerpo = respuesta.json()
                self.assertEqual(set(cuerpo), CLAVES)
                self.assertIs(cuerpo["success"], False)
                self.assertEqual(cuerpo["message"], "Error interno del servidor.")
                self.assertEqual(
                    cuerpo["errors"],
                    {"detail": "Ocurrió un error inesperado.", "code": "error_interno"},
                )
                self.assertIsNone(cuerpo["data"])
                self.assertEqual(cuerpo["meta"], {})
                texto = respuesta.content.decode()
                for fuga in ("Traceback", "RuntimeError", "secreto"):
                    self.assertNotIn(fuga, texto)
                # La traza va al log del servidor, nunca al cuerpo.
                self.assertEqual(len(registro.output), 1)

    def test_errores_manejados_marcan_rollback_de_la_transaccion(self):
        casos = (
            ("post", "/api/v1/sonda/validacion/"),
            ("post", "/api/v1/sonda/detalle/"),
            ("post", "/api/v1/sonda/conflicto/"),
            ("get", "/api/v1/sonda/protegida/"),
            ("get", "/api/v1/sonda/restringida/"),
            ("get", "/api/v1/sonda/inexistente/"),
        )
        for metodo, url in casos:
            with self.subTest(url=url), mock.patch(
                "apps.contrato.exceptions.set_rollback"
            ) as set_rollback:
                getattr(self.client, metodo)(url)

                set_rollback.assert_called_once_with()

    def test_500_tambien_marca_rollback(self):
        with mock.patch("apps.contrato.exceptions.set_rollback") as set_rollback, \
                self.assertLogs("apps.contrato.exceptions", level="ERROR"):
            self.client.get("/api/v1/sonda/falla/")

        set_rollback.assert_called_once_with()

    def test_errores_no_de_validacion_llevan_code_legible_por_maquina(self):
        casos = (
            ("post", "/api/v1/sonda/detalle/"),
            ("post", "/api/v1/sonda/conflicto/"),
            ("get", "/api/v1/sonda/protegida/"),
            ("get", "/api/v1/sonda/restringida/"),
            ("get", "/api/v1/sonda/inexistente/"),
        )
        for metodo, url in casos:
            with self.subTest(url=url):
                errores = getattr(self.client, metodo)(url).json()["errors"]

                self.assertEqual(set(errores), {"detail", "code"})
                self.assertRegex(errores["code"], r"^[a-z_]+$")

    def test_validacion_no_lleva_code(self):
        errores = self.client.post("/api/v1/sonda/validacion/").json()["errors"]

        self.assertNotIn("code", errores)

    def test_matriz_de_errores_comparte_claves_y_success_falso(self):
        casos = (
            ("post", "/api/v1/sonda/validacion/", 400),
            ("post", "/api/v1/sonda/detalle/", 400),
            ("get", "/api/v1/sonda/protegida/", 401),
            ("get", "/api/v1/sonda/restringida/", 403),
            ("get", "/api/v1/sonda/inexistente/", 404),
        )
        for metodo, url, esperado in casos:
            with self.subTest(metodo=metodo, url=url):
                respuesta = getattr(self.client, metodo)(url)

                self.assertEqual(respuesta.status_code, esperado)
                cuerpo = respuesta.json()
                self.assertEqual(set(cuerpo), CLAVES)
                self.assertIs(cuerpo["success"], False)
                self.assertIsNone(cuerpo["data"])
                self.assertIsInstance(cuerpo["errors"], dict)
                self.assertIsInstance(cuerpo["message"], str)
                self.assertLessEqual(len(cuerpo["message"]), 60)
                self.assertEqual(cuerpo["meta"], {})
