"""Envelope del contrato en el camino exitoso y maquinaria OpenAPI (S2-S4, #77).

Técnica de ruteo: las vistas DRF del contrato se definen DENTRO de este módulo y
el módulo expone su propio ``urlpatterns``; cada ``TestCase`` corre con
``override_settings(ROOT_URLCONF=__name__)``, de modo que el resolvedor importa
este mismo módulo ya cargado en ``sys.modules``. Ninguna ruta de prueba toca
``config/urls.py``: en producción solo viven ``/api/v1/schema/`` y
``/api/v1/docs/`` (los endpoints de negocio de ``/api/v1/`` son de #78).

El esquema se ejercita dos veces: con el urlconf de producción (las rutas de
schema y Swagger existen y sirven YAML/HTML) y con el urlconf de este módulo (las
rutas DRF bajo ``/api/v1/`` quedan documentadas con request, response y errores).
"""

import json
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

import yaml
from django.conf import settings
from django.test import SimpleTestCase, override_settings
from django.urls import path
from drf_spectacular.utils import OpenApiTypes, extend_schema, inline_serializer
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

CLAVES = {"success", "message", "data", "errors", "meta"}

SondaEntrada = inline_serializer(
    name="SondaEntrada", fields={"nombre": serializers.CharField()}
)
SondaSalida = inline_serializer(
    name="SondaSalida", fields={"id": serializers.IntegerField()}
)


class SondaListaView(APIView):
    def get(self, request):
        return Response({"items": [{"id": 1}], "total": 1})


class SondaCrearView(APIView):
    @extend_schema(
        request=SondaEntrada, responses={201: SondaSalida, 400: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        return Response({"id": 7}, status=status.HTTP_201_CREATED)


class SondaBorrarView(APIView):
    def delete(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)


urlpatterns = [  # urlconf de pruebas, activo por override_settings(ROOT_URLCONF=__name__)
    path("api/v1/sonda/", SondaListaView.as_view()),
    path("api/v1/sonda/nueva/", SondaCrearView.as_view()),
    path("api/v1/sonda/actual/", SondaBorrarView.as_view()),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="api-v1-spectacular"),
    path(
        "api/v1/docs/",
        SpectacularSwaggerView.as_view(url_name="api-v1-spectacular"),
        name="api-v1-docs",
    ),
]


@override_settings(ROOT_URLCONF=__name__)
class EnvelopeExitosoTests(SimpleTestCase):
    """S2-S4: el renderer envuelve la carga cruda de toda respuesta < 400."""

    def test_200_envuelve_la_carga_y_usa_meta_vacio(self):
        respuesta = self.client.get("/api/v1/sonda/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta["Content-Type"].startswith("application/json"))
        cuerpo = respuesta.json()
        self.assertEqual(set(cuerpo), CLAVES)
        self.assertIs(cuerpo["success"], True)
        self.assertEqual(cuerpo["message"], "Operación exitosa.")
        self.assertEqual(cuerpo["data"], {"items": [{"id": 1}], "total": 1})
        self.assertIsNone(cuerpo["errors"])
        self.assertEqual(cuerpo["meta"], {})

    def test_201_envuelve_y_usa_el_mensaje_de_creacion(self):
        respuesta = self.client.post("/api/v1/sonda/nueva/", data={})

        self.assertEqual(respuesta.status_code, 201)
        cuerpo = respuesta.json()
        self.assertEqual(set(cuerpo), CLAVES)
        self.assertIs(cuerpo["success"], True)
        self.assertEqual(cuerpo["message"], "Recurso creado.")
        self.assertEqual(cuerpo["data"], {"id": 7})
        self.assertIsNone(cuerpo["errors"])
        self.assertEqual(cuerpo["meta"], {})

    def test_204_va_sin_cuerpo(self):
        respuesta = self.client.delete("/api/v1/sonda/actual/")

        self.assertEqual(respuesta.status_code, 204)
        self.assertEqual(respuesta.content, b"")


class ConfiguracionContratoTests(SimpleTestCase):
    """La decisión de wiring: un único renderer, handler propio y AutoSchema."""

    def test_envelope_es_el_unico_renderer_por_defecto(self):
        # Sin BrowsableAPIRenderer ni un JSONRenderer duplicado: no hay camino
        # por el que una respuesta DRF salga sin envelope.
        self.assertEqual(
            settings.REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"],
            ["apps.contrato.renderer.SuccessEnvelopeRenderer"],
        )
        self.assertEqual(
            settings.REST_FRAMEWORK["EXCEPTION_HANDLER"],
            "apps.contrato.exceptions.envelope_exception_handler",
        )
        self.assertEqual(
            settings.REST_FRAMEWORK["DEFAULT_SCHEMA_CLASS"],
            "drf_spectacular.openapi.AutoSchema",
        )


class SchemaYSwaggerTests(SimpleTestCase):
    """S3: schema YAML en ``/api/v1/schema/`` y Swagger UI en ``/api/v1/docs/``."""

    def test_esquema_de_produccion_responde_yaml(self):
        respuesta = self.client.get("/api/v1/schema/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta["Content-Type"].startswith("application/vnd.oai.openapi"))
        texto = respuesta.content.decode()
        self.assertTrue(texto.startswith("openapi:"))
        self.assertIn("title: Sistema de Prácticas Profesionales UNL", texto)
        # SERVE_INCLUDE_SCHEMA=False: la maquinaria no se auto-documenta.
        self.assertNotIn("/api/v1/schema/", texto)
        self.assertNotIn("/api/v1/docs/", texto)

    @override_settings(ROOT_URLCONF=__name__)
    def test_esquema_documenta_request_response_y_errores_de_v1(self):
        respuesta = self.client.get("/api/v1/schema/")

        self.assertEqual(respuesta.status_code, 200)
        documento = yaml.safe_load(respuesta.content.decode())
        self.assertIn("/api/v1/sonda/", documento["paths"])
        operacion = documento["paths"]["/api/v1/sonda/nueva/"]["post"]
        self.assertEqual(set(operacion["responses"]), {"201", "400"})
        self.assertIn("SondaEntrada", str(operacion["requestBody"]))
        self.assertIn("SondaSalida", str(operacion["responses"]["201"]))
        self.assertIn("SondaSalida", documento["components"]["schemas"])

    def test_swagger_ui_responde_html_con_la_url_del_esquema(self):
        respuesta = self.client.get("/api/v1/docs/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta["Content-Type"].startswith("text/html"))
        html = respuesta.content.decode()
        self.assertIn("swagger-ui", html)
        self.assertIn("/api/v1/schema/", html)


class RutasNoApiSinEnvelopeTests(SimpleTestCase):
    """PRESERVE: ``/health/`` no es DRF y sigue devolviendo su JSON crudo."""

    # /health/ (develop) hace SELECT 1 contra la base: SimpleTestCase lo prohíbe.
    databases = {"default"}

    def test_health_responde_igual_que_antes(self):
        respuesta = self.client.get("/health/")

        self.assertEqual(respuesta.status_code, 200)
        # El cuerpo crudo de develop (con ``checks``); lo que se protege es que
        # NO se envuelva: sin ``success``/``data``/``errors``/``meta``.
        self.assertEqual(
            respuesta.json(), {"status": "ok", "checks": {"database": "ok"}}
        )



class SerializacionRicaTests(SimpleTestCase):
    """F1 del verifier: fechas, Decimals y UUIDs se serializan como Django."""

    def test_fechas_decimales_uuid_se_serializan(self):
        from django.test import RequestFactory

        sonda = SondaSerializacion.as_view()
        respuesta = sonda(RequestFactory().get("/probes/", HTTP_ACCEPT="application/json"))
        respuesta.render()
        cuerpo = json.loads(respuesta.content.decode("utf-8"))

        self.assertEqual(cuerpo["success"], True)
        self.assertEqual(cuerpo["data"]["fecha"], "2026-01-02")
        self.assertEqual(cuerpo["data"]["monto"], "1.5")
        self.assertEqual(cuerpo["data"]["ts"], "2026-01-02T03:00:00")
        self.assertEqual(cuerpo["data"]["id"], "00000000-0000-0000-0000-000000000001")


class SondaSerializacion(APIView):
    """Vista de prueba (no rutas de producción): carga rica para el encoder."""

    def get(self, request):
        return Response(
            {
                "fecha": date(2026, 1, 2), "monto": Decimal("1.5"),
                "ts": datetime(2026, 1, 2, 3), "id": UUID(int=1),
            }
        )
