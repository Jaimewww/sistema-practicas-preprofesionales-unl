"""Acción autenticada de captura de la fecha real de inicio (T11, S1/S3).
``POST /api/v1/practicas/{practica_id}/inicio/`` es el adaptador HTTP fino del
servicio de dominio de T10: el actor sale del usuario autenticado del servidor
(nunca del cuerpo ni de ``X-Rol``), el rol ``coordinador`` y el alcance de
carrera se comprueban **antes** de mirar el cuerpo, y la práctica ajena o
inexistente responde el mismo 404 aunque el cuerpo venga malformado.

El cuerpo es un objeto JSON con una sola clave, ``fecha`` (``AAAA-MM-DD``); se
rechazan las claves extra y los cuerpos que no son objeto. El dominio decide lo
demás: 400 por campo (incluida una segunda fecha distinta, sin revelar la
guardada), 409 ``practica_no_en_curso`` y 200 con ``id`` y
``fecha_inicio_real``, también cuando se repite exactamente la misma fecha.
Ningún rechazo escribe: ni filas de práctica, ni estado, ni historial.
"""

from collections.abc import Callable
from datetime import date, timedelta
from typing import Any, Protocol, cast
from unittest import mock

import yaml
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.auditoria.models import HistorialEstado
from apps.carreras.models import Carrera
from apps.practicas.api import (
    MENSAJE_CAMPO_NO_ADMITIDO_INICIO,
    MENSAJE_CUERPO_INICIO,
    MENSAJE_INICIO,
)
from apps.practicas.models import Practica
from apps.practicas.services import (
    MENSAJE_ESTADO_INICIO,
    MENSAJE_FECHA_FUTURA,
    MENSAJE_FECHA_YA_REGISTRADA,
)
from apps.usuarios.models import Usuario
from tests.integration.test_reportes_flujo import FlujoFixturesMixin, crear_usuario

INICIO = "/api/v1/practicas/{}/inicio/"
RUTA_SCHEMA = "/api/v1/practicas/{practica_id}/inicio/"
CAMPOS_RESPUESTA = {"id", "fecha_inicio_real"}


def hoy() -> date:
    """Fecha local del servidor, leída en cada uso y no al importar el módulo."""
    return timezone.localdate()


def hace(dias: int) -> date:
    """Fecha local desplazada ``dias`` (negativo = futuro)."""
    return hoy() - timedelta(days=dias)


def iso(fecha: date) -> str:
    return fecha.strftime("%Y-%m-%d")


class RespuestaAPI(Protocol):
    """Lo que estas pruebas leen de la respuesta HTTP de la API.

    El cliente de pruebas de DRF devuelve un ``HttpResponse`` al que Django le
    agrega ``.json()`` en tiempo de ejecución; ni Django ni DRF declaran ese
    método, así que el contrato que usa la prueba se declara acá.
    """

    status_code: int
    content: bytes

    def json(self) -> Any: ...


class InicioPracticaFixturesMixin(FlujoFixturesMixin):
    """Reutiliza el flujo de reportes: dos carreras, seis roles y varios estados."""

    carrera: Carrera
    practica: Practica
    ajena: Practica
    cerrada: Practica
    cancelada: Practica
    estudiante: Usuario
    par: Usuario
    tutor: Usuario
    externo: Usuario
    coordinador: Usuario
    coordinador_par: Usuario
    director: Usuario
    secretaria: Usuario

    assertEqual: Callable[..., None]
    assertIn: Callable[..., None]
    assertNotIn: Callable[..., None]
    assertIsNone: Callable[..., None]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.director = crear_usuario("director1", Usuario.Rol.DIRECTOR, cls.carrera)
        cls.secretaria = crear_usuario(
            "secretaria1", Usuario.Rol.SECRETARIA, cls.carrera
        )

    def publicar(self, usuario, practica=None, cuerpo=None, crudo=None) -> RespuestaAPI:
        """``POST`` de la ruta; ``crudo`` envía el texto tal cual como cuerpo."""
        objetivo = self.practica if practica is None else practica
        pk = objetivo.pk if isinstance(objetivo, Practica) else objetivo
        cliente = self.cliente(usuario)
        if crudo is not None:
            respuesta = cliente.post(
                INICIO.format(pk), data=crudo, content_type="application/json"
            )
        else:
            datos = {} if cuerpo is None else cuerpo
            respuesta = cliente.post(INICIO.format(pk), datos, format="json")
        # El cliente de pruebas de DRF no declara el tipo de su respuesta.
        return cast(RespuestaAPI, respuesta)

    def guardar_fecha(self, fecha, practica=None):
        """Escribe una fecha previa en la fila, sin pasar por el servicio."""
        objetivo = practica or self.practica
        Practica.objects.filter(pk=objetivo.pk).update(fecha_inicio_real=fecha)
        objetivo.refresh_from_db()
        return objetivo

    def fotografia_completa(self):
        """Filas de práctica, historial y conteos: un rechazo no cambia nada."""
        practicas = tuple(
            Practica.objects.order_by("pk").values_list(
                "pk",
                "estado",
                "fecha_inicio_real",
                "motivo_suspension",
                "motivo_cancelacion",
            )
        )
        historial = tuple(
            HistorialEstado.objects.order_by("pk").values_list(
                "pk",
                "practica_id",
                "estado_anterior",
                "estado_nuevo",
                "motivo",
                "autor_id",
                "fecha",
            )
        )
        return super().fotografia(), practicas, historial

    def assertExito(self, respuesta, estado=200):
        self.assertEqual(respuesta.status_code, estado)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["success"], True)
        self.assertEqual(cuerpo["message"], "Operación exitosa.")
        self.assertEqual(cuerpo["errors"], None)
        self.assertEqual(cuerpo["meta"], {})
        return cuerpo["data"]

    def assertRechazo(self, respuesta, estado, mensaje, errores):
        self.assertEqual(respuesta.status_code, estado)
        self.assertEqual(
            respuesta.json(),
            {
                "success": False,
                "message": mensaje,
                "data": None,
                "errors": errores,
                "meta": {},
            },
        )

    def assertSinEscrituras(self, antes):
        self.assertEqual(self.fotografia_completa(), antes)


class InicioPracticaExitoTests(InicioPracticaFixturesMixin, TestCase):
    """El coordinador de la carrera guarda solo la fecha real de inicio."""

    def test_el_coordinador_de_la_carrera_registra_la_fecha(self):
        fecha = hace(30)
        antes = {
            clave: valor
            for clave, valor in Practica.objects.filter(pk=self.practica.pk)
            .values()
            .get()
            .items()
            if clave != "fecha_inicio_real"
        }
        historial_antes = tuple(
            HistorialEstado.objects.filter(practica=self.practica).values_list(
                "pk", "estado_anterior", "estado_nuevo", "motivo"
            )
        )

        data = self.assertExito(
            self.publicar(self.coordinador, cuerpo={"fecha": iso(fecha)})
        )

        self.assertEqual(
            data, {"id": self.practica.pk, "fecha_inicio_real": iso(fecha)}
        )
        guardada = Practica.objects.filter(pk=self.practica.pk).values().get()
        self.assertEqual(guardada["fecha_inicio_real"], fecha)
        sin_fecha = {k: v for k, v in guardada.items() if k != "fecha_inicio_real"}
        self.assertEqual(sin_fecha, antes)
        historial_despues = tuple(
            HistorialEstado.objects.filter(practica=self.practica).values_list(
                "pk", "estado_anterior", "estado_nuevo", "motivo"
            )
        )
        self.assertEqual(historial_despues, historial_antes)
        self.assertTrue(historial_antes, "la práctica preparada tiene historial")

    def test_la_fecha_de_hoy_se_acepta(self):
        data = self.assertExito(
            self.publicar(self.coordinador, cuerpo={"fecha": iso(hoy())})
        )
        self.assertEqual(data["fecha_inicio_real"], iso(hoy()))

    def test_repetir_la_misma_fecha_responde_200_sin_escribir(self):
        guardada = hace(40)
        self.guardar_fecha(guardada)
        antes = self.fotografia_completa()

        data = self.assertExito(
            self.publicar(self.coordinador, cuerpo={"fecha": iso(guardada)})
        )

        self.assertEqual(
            data, {"id": self.practica.pk, "fecha_inicio_real": iso(guardada)}
        )
        self.assertSinEscrituras(antes)

    def test_el_cuerpo_no_puede_fijar_la_practica(self):
        """El ``id`` sale del path: el cuerpo solo trae ``fecha``."""
        antes = self.fotografia_completa()
        respuesta = self.publicar(
            self.coordinador,
            cuerpo={"fecha": iso(hace(30)), "practica": self.ajena.pk},
        )
        self.assertRechazo(
            respuesta,
            400,
            "Datos inválidos.",
            {"practica": [MENSAJE_CAMPO_NO_ADMITIDO_INICIO]},
        )
        self.assertSinEscrituras(antes)


class InicioPracticaValidacionTests(InicioPracticaFixturesMixin, TestCase):
    """Entrada estricta: una sola clave ``fecha`` con formato ISO y no futura."""

    def test_un_cuerpo_que_no_es_objeto_responde_400_y_no_escribe(self):
        antes = self.fotografia_completa()
        for cuerpo in ([{"fecha": iso(hace(30))}], ["fecha"], "fecha", 7):
            with self.subTest(cuerpo=cuerpo):
                self.assertRechazo(
                    self.publicar(self.coordinador, cuerpo=cuerpo),
                    400,
                    "Datos inválidos.",
                    {"non_field_errors": [MENSAJE_CUERPO_INICIO]},
                )
        self.assertSinEscrituras(antes)

    def test_las_claves_extra_se_rechazan_y_nada_se_escribe(self):
        antes = self.fotografia_completa()
        for campo in ("estado", "id", "fecha_inicio_real", "autor"):
            with self.subTest(campo=campo):
                respuesta = self.publicar(
                    self.coordinador,
                    cuerpo={"fecha": iso(hace(30)), campo: "x"},
                )
                self.assertRechazo(
                    respuesta,
                    400,
                    "Datos inválidos.",
                    {campo: [MENSAJE_CAMPO_NO_ADMITIDO_INICIO]},
                )
        self.assertSinEscrituras(antes)

    def test_la_fecha_es_obligatoria(self):
        antes = self.fotografia_completa()
        respuesta = self.publicar(self.coordinador, cuerpo={})
        self.assertEqual(respuesta.status_code, 400)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["message"], "Datos inválidos.")
        self.assertEqual(list(cuerpo["errors"]), ["fecha"])
        self.assertSinEscrituras(antes)

    def test_una_fecha_malformada_se_rechaza_en_su_campo(self):
        antes = self.fotografia_completa()
        valores = ("2026-02-30", "06/04/2026", "2026-04-06T00:00:00Z", None, 20260406)
        for valor in valores:
            with self.subTest(valor=valor):
                respuesta = self.publicar(self.coordinador, cuerpo={"fecha": valor})
                self.assertEqual(respuesta.status_code, 400)
                cuerpo = respuesta.json()
                self.assertEqual(cuerpo["message"], "Datos inválidos.")
                self.assertEqual(list(cuerpo["errors"]), ["fecha"])
        self.assertSinEscrituras(antes)

    def test_una_fecha_futura_se_rechaza_sin_escribir(self):
        antes = self.fotografia_completa()
        self.assertRechazo(
            self.publicar(self.coordinador, cuerpo={"fecha": iso(hace(-1))}),
            400,
            "Datos inválidos.",
            {"fecha": [MENSAJE_FECHA_FUTURA]},
        )
        self.assertSinEscrituras(antes)

    def test_un_cuerpo_que_no_es_json_valido_responde_400_sin_escribir(self):
        antes = self.fotografia_completa()
        respuesta = self.publicar(self.coordinador, crudo="{no es json")
        self.assertEqual(respuesta.status_code, 400)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["message"], "Solicitud inválida.")
        self.assertEqual(cuerpo["errors"]["code"], "parse_error")
        self.assertSinEscrituras(antes)

    def test_una_segunda_fecha_distinta_se_rechaza_sin_revelar_la_guardada(self):
        guardada = hace(40)
        self.guardar_fecha(guardada)
        antes = self.fotografia_completa()

        respuesta = self.publicar(self.coordinador, cuerpo={"fecha": iso(hace(30))})

        self.assertRechazo(
            respuesta,
            400,
            "Datos inválidos.",
            {"fecha": [MENSAJE_FECHA_YA_REGISTRADA]},
        )
        self.assertNotIn(iso(guardada), respuesta.content.decode())
        self.assertEqual(
            Practica.objects.get(pk=self.practica.pk).fecha_inicio_real, guardada
        )
        self.assertSinEscrituras(antes)


class InicioPracticaAlcanceTests(InicioPracticaFixturesMixin, TestCase):
    """Rol y alcance de carrera antes del cuerpo; 404 indistinguible e idéntico."""

    def test_la_practica_ajena_y_la_inexistente_dan_el_mismo_404(self):
        antes = self.fotografia_completa()
        ajena = self.publicar(
            self.coordinador, self.ajena, cuerpo={"fecha": iso(hace(30))}
        )
        inexistente = self.publicar(
            self.coordinador, 999_999, cuerpo={"fecha": iso(hace(30))}
        )
        otra_carrera = self.publicar(
            self.coordinador_par, self.practica, cuerpo={"fecha": iso(hace(30))}
        )

        for respuesta in (ajena, otra_carrera):
            self.assertEqual(respuesta.json(), inexistente.json())
        self.assertRechazo(
            inexistente,
            404,
            "Recurso no encontrado.",
            {"detail": "No encontrado.", "code": "no_encontrado"},
        )
        self.assertSinEscrituras(antes)

    def test_el_404_es_identico_aunque_el_cuerpo_venga_malformado(self):
        antes = self.fotografia_completa()
        cuerpos = ({}, {"fecha": "no-es-fecha"}, {"otra": 1}, [1], "texto")
        referencia = self.publicar(self.coordinador, 999_999, cuerpo={})
        self.assertEqual(referencia.status_code, 404)

        for cuerpo in cuerpos:
            with self.subTest(cuerpo=cuerpo):
                ajena = self.publicar(self.coordinador, self.ajena, cuerpo=cuerpo)
                inexistente = self.publicar(self.coordinador, 999_999, cuerpo=cuerpo)
                self.assertEqual(ajena.status_code, 404)
                self.assertEqual(ajena.json(), inexistente.json())
                self.assertEqual(ajena.json(), referencia.json())
        self.assertSinEscrituras(antes)

    def test_anonimo_y_cuenta_inactiva_reciben_401_sin_escribir(self):
        inactivo = crear_usuario("inactivo1", Usuario.Rol.COORDINADOR, self.carrera)
        Usuario.objects.filter(pk=inactivo.pk).update(is_active=False)
        antes = self.fotografia_completa()

        for actor in (None, inactivo, Usuario(username="fantasma")):
            with self.subTest(actor=getattr(actor, "username", "anonimo")):
                self.assertRechazo(
                    self.publicar(actor, cuerpo={"fecha": iso(hace(30))}),
                    401,
                    "Autenticación requerida.",
                    {"detail": "Se requiere autenticación.", "code": "no_autenticado"},
                )
        self.assertSinEscrituras(antes)

    def test_los_demas_roles_reciben_403_sin_escribir(self):
        antes = self.fotografia_completa()
        actores = {
            "estudiante": self.estudiante,
            "tutor_academico": self.tutor,
            "tutor_entidad": self.externo,
            "director": self.director,
            "secretaria": self.secretaria,
        }
        for rol, actor in actores.items():
            with self.subTest(rol=rol):
                self.assertRechazo(
                    self.publicar(actor, cuerpo={"fecha": iso(hace(30))}),
                    403,
                    "Permiso denegado.",
                    {"detail": MENSAJE_INICIO, "code": "permiso_denegado"},
                )
        self.assertSinEscrituras(antes)

    def test_el_rol_se_comprueba_antes_que_la_existencia_y_el_cuerpo(self):
        """Un rol ajeno recibe 403 aunque la práctica no exista ni el cuerpo valga."""
        respuesta = self.publicar(self.estudiante, 999_999, cuerpo={})
        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(respuesta.json()["errors"]["code"], "permiso_denegado")


class InicioPracticaEstadoTests(InicioPracticaFixturesMixin, TestCase):
    """Solo una práctica «en curso» admite la declaración; el 409 no escribe."""

    def test_una_practica_que_no_esta_en_curso_responde_409(self):
        asignada = self.crear(self.par)
        antes = self.fotografia_completa()
        for practica in (asignada, self.cerrada, self.cancelada):
            with self.subTest(practica=practica.pk, estado=practica.estado):
                self.assertRechazo(
                    self.publicar(
                        self.coordinador, practica, cuerpo={"fecha": iso(hace(30))}
                    ),
                    409,
                    "Solicitud inválida.",
                    {
                        "detail": MENSAJE_ESTADO_INICIO.format(estado=practica.estado),
                        "code": "practica_no_en_curso",
                    },
                )
        self.assertSinEscrituras(antes)

    def test_el_estado_no_cambia_al_registrar_la_fecha(self):
        data = self.assertExito(
            self.publicar(self.coordinador, cuerpo={"fecha": iso(hace(30))})
        )
        self.assertEqual(data["id"], self.practica.pk)
        self.assertEqual(
            Practica.objects.get(pk=self.practica.pk).estado, Practica.Estado.EN_CURSO
        )


class InicioPracticaFalloCerradoTests(InicioPracticaFixturesMixin, TestCase):
    """Una clave de dominio no prevista no se adivina ni se publica."""

    def test_una_clave_no_prevista_falla_cerrado_sin_filtrar_el_mensaje(self):
        antes = self.fotografia_completa()
        with mock.patch(
            "apps.practicas.api.registrar_inicio_practica",
            side_effect=ValidationError({"autor": ["mensaje interno del dominio"]}),
        ):
            respuesta = self.publicar(self.coordinador, cuerpo={"fecha": iso(hace(30))})

        self.assertEqual(respuesta.status_code, 500)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["success"], False)
        self.assertIsNone(cuerpo["data"])
        self.assertEqual(cuerpo["errors"]["code"], "error_interno")
        self.assertNotIn("mensaje interno del dominio", respuesta.content.decode())
        self.assertSinEscrituras(antes)


class InicioPracticaSchemaTests(InicioPracticaFixturesMixin, TestCase):
    """El contrato OpenAPI publica el POST, sus respuestas y el security JWT."""

    @override_settings(DEBUG=True)
    def test_el_post_aparece_en_swagger_con_sus_respuestas_y_jwt(self):
        documento = yaml.safe_load(self.client.get("/api/v1/schema/").content)
        operacion = documento["paths"][RUTA_SCHEMA]["post"]

        self.assertLessEqual(
            {"200", "400", "401", "403", "404", "409"},
            set(operacion["responses"]),
        )
        self.assertEqual(operacion["security"], [{"jwtAuth": []}])
        self.assertIn("practicas", operacion["tags"])
        esquema = operacion["requestBody"]["content"]["application/json"]["schema"]
        self.assertEqual(
            esquema["$ref"], "#/components/schemas/RegistrarInicioPractica"
        )
        componentes = documento["components"]["schemas"]
        self.assertEqual(
            set(componentes["RegistrarInicioPractica"]["properties"]), {"fecha"}
        )
        self.assertEqual(
            set(componentes["InicioPractica"]["properties"]), CAMPOS_RESPUESTA
        )

    @override_settings(DEBUG=True)
    def test_las_rutas_get_de_practicas_conservan_su_metodo(self):
        documento = yaml.safe_load(self.client.get("/api/v1/schema/").content)
        for ruta, metodo in (
            ("/api/v1/practicas/", "get"),
            ("/api/v1/practicas/{practica_id}/", "get"),
            ("/api/v1/practicas/{practica_id}/horas/", "get"),
        ):
            with self.subTest(ruta=ruta):
                self.assertEqual(set(documento["paths"][ruta]), {metodo})
