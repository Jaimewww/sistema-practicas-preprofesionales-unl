"""Envelope del contrato en el camino de error (S2-S4, #77).

Misma técnica de ruteo que ``test_envelope_renderer``: las vistas DRF viven en
este módulo y ``urlpatterns`` se activa con
``override_settings(ROOT_URLCONF=__name__)``, sin tocar ``config/urls.py``.

El 500 se observa con ``DEBUG`` apagado (semántica de producción) y también
encendido: el handler devuelve siempre el mismo cuerpo genérico, así que ni la
traza, ni el mensaje de la excepción, ni datos internos salen por el wire.

Reconciliación de #79 (auth-first, doc L4): con ``DEFAULT_PERMISSION_CLASSES =
IsAuthenticated`` estas sondas ya no responden 400/404/500 sin credenciales. Los
casos originales se conservan **autenticados** (actor forzado, sin tocar la base)
y se agrega el caso nuevo de S4-79: el mismo camino inexistente responde 401 sin
credenciales y 404 ya autenticado. Ninguna aserción original se debilitó.
"""

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import SimpleTestCase, override_settings
from django.urls import path
from rest_framework.authentication import BasicAuthentication
from rest_framework.exceptions import NotAuthenticated, ParseError, ValidationError
from rest_framework.test import APIClient
from rest_framework.views import APIView

from apps.usuarios.models import Usuario

CLAVES = {"success", "message", "data", "errors", "meta"}


class SondaValidacionView(APIView):
    def post(self, request):
        raise ValidationError(
            {"nombre": ["Este campo es obligatorio."], "edad": ["Debe ser un entero."]}
        )


class SondaDetalleView(APIView):
    def post(self, request):
        raise ParseError("Cuerpo ilegible.")


class Sonda401View(APIView):
    # BasicAuthentication solo aporta el header WWW-Authenticate: sin él DRF
    # degrada el 401 a 403. La autenticación real (token/JWT) es de #79.
    authentication_classes = [BasicAuthentication]

    def get(self, request):
        raise NotAuthenticated()


class Sonda403View(APIView):
    def get(self, request):
        raise PermissionDenied()


class Sonda404View(APIView):
    def get(self, request):
        raise Http404("no existe")


class Sonda500View(APIView):
    def get(self, request):
        raise RuntimeError("secreto que no debe salir")


urlpatterns = [  # urlconf de pruebas, activo por override_settings(ROOT_URLCONF=__name__)
    path("api/v1/sonda/validacion/", SondaValidacionView.as_view()),
    path("api/v1/sonda/detalle/", SondaDetalleView.as_view()),
    path("api/v1/sonda/protegida/", Sonda401View.as_view()),
    path("api/v1/sonda/restringida/", Sonda403View.as_view()),
    path("api/v1/sonda/inexistente/", Sonda404View.as_view()),
    path("api/v1/sonda/falla/", Sonda500View.as_view()),
]


@override_settings(ROOT_URLCONF=__name__)
class EnvelopeDeErrorTests(SimpleTestCase):
    """S3: el handler envuelve validación, autenticación, permisos, 404 y 500."""

    def setUp(self):
        # #79: la API real es auth-first; las sondas conservan su caso original ya
        # autenticado, con un actor forzado que no consulta la base.
        self.cliente = APIClient()
        self.cliente.force_authenticate(
            user=Usuario(username="probador", rol=Usuario.Rol.ESTUDIANTE)
        )

    def test_400_de_validacion_mapea_campo_a_lista(self):
        cuerpo = self.cliente.post("/api/v1/sonda/validacion/").json()

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
        cuerpo = self.cliente.post("/api/v1/sonda/detalle/").json()

        self.assertIs(cuerpo["success"], False)
        self.assertEqual(cuerpo["message"], "Solicitud inválida.")
        self.assertEqual(cuerpo["errors"], {"detail": "Cuerpo ilegible."})

    def test_401_autenticacion_requerida(self):
        respuesta = self.client.get("/api/v1/sonda/protegida/")

        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(respuesta["WWW-Authenticate"], 'Basic realm="api"')
        cuerpo = respuesta.json()
        self.assertIs(cuerpo["success"], False)
        self.assertEqual(cuerpo["message"], "Autenticación requerida.")
        self.assertEqual(cuerpo["errors"], {"detail": "Se requiere autenticación."})

    def test_403_permiso_denegado(self):
        respuesta = self.cliente.get("/api/v1/sonda/restringida/")

        self.assertEqual(respuesta.status_code, 403)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["message"], "Permiso denegado.")
        self.assertEqual(
            cuerpo["errors"], {"detail": "No tiene permiso para esta operación."}
        )

    def test_404_recurso_no_encontrado(self):
        respuesta = self.cliente.get("/api/v1/sonda/inexistente/")

        self.assertEqual(respuesta.status_code, 404)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["message"], "Recurso no encontrado.")
        self.assertEqual(cuerpo["errors"], {"detail": "No encontrado."})

    def test_401_antes_que_404_sin_credenciales(self):
        """S4-79: la autenticación corre primero; el 404 llega ya autenticado."""
        anonima = self.client.get("/api/v1/sonda/inexistente/")
        autenticada = self.cliente.get("/api/v1/sonda/inexistente/")

        self.assertEqual(anonima.status_code, 401)
        self.assertEqual(anonima.json()["message"], "Autenticación requerida.")
        self.assertEqual(autenticada.status_code, 404)

    def test_500_generico_sin_trazas_ni_datos_sensibles(self):
        for debug in (False, True):
            with self.subTest(DEBUG=debug), override_settings(DEBUG=debug), \
                    self.assertLogs("apps.contrato.exceptions", level="ERROR") as registro:
                respuesta = self.cliente.get("/api/v1/sonda/falla/")

                self.assertEqual(respuesta.status_code, 500)
                cuerpo = respuesta.json()
                self.assertEqual(set(cuerpo), CLAVES)
                self.assertIs(cuerpo["success"], False)
                self.assertEqual(cuerpo["message"], "Error interno del servidor.")
                self.assertEqual(
                    cuerpo["errors"], {"detail": "Ocurrió un error inesperado."}
                )
                self.assertIsNone(cuerpo["data"])
                self.assertEqual(cuerpo["meta"], {})
                texto = respuesta.content.decode()
                for fuga in ("Traceback", "RuntimeError", "secreto"):
                    self.assertNotIn(fuga, texto)
                # La traza va al log del servidor, nunca al cuerpo.
                self.assertEqual(len(registro.output), 1)

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
                # La sonda 401 declara BasicAuthentication y se observa anónima; el
                # resto corre autenticado para alcanzar su estado propio (#79).
                cliente = self.client if esperado == 401 else self.cliente
                respuesta = getattr(cliente, metodo)(url)

                self.assertEqual(respuesta.status_code, esperado)
                cuerpo = respuesta.json()
                self.assertEqual(set(cuerpo), CLAVES)
                self.assertIs(cuerpo["success"], False)
                self.assertIsNone(cuerpo["data"])
                self.assertIsInstance(cuerpo["errors"], dict)
                self.assertIsInstance(cuerpo["message"], str)
                self.assertLessEqual(len(cuerpo["message"]), 60)
                self.assertEqual(cuerpo["meta"], {})
