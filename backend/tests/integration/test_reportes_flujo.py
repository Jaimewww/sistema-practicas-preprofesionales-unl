"""Flujo completo del registro de reportes semanales (S2-S7, #78).

Recorre las tres rutas del contrato con ``APIClient``: la lista y el detalle de
prácticas con el alcance de filas de T019 y el POST del reporte con sus reglas
(art. 341 para ayudantías, semana duplicada, práctica en curso, actor dueño).
Un rechazo no escribe: ni filas ni contadores cambian (S3) y el cuerpo es el
envelope de #77 con ``errors.code``.
"""

from collections.abc import Callable
from datetime import date

from unittest import mock

import yaml
from apps.actividades.models import PlanActividades, Validacion
from apps.auditoria.models import HistorialEstado
from apps.carreras.models import Carrera, ConfiguracionCarrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import AsignacionTutor, Periodo, Practica
from apps.practicas.services import asignar_practica
from apps.reportes.api import (
    MENSAJE_ACTOR,
    MENSAJE_NO_EN_CURSO,
)
from apps.reportes.models import (
    MENSAJE_AYUDANTIA,
    MENSAJE_HORAS,
    MENSAJE_SEMANA,
    MENSAJE_SEMANA_DUPLICADA,
    MENSAJE_TOPE_SEMANAL,
    ReporteSemanal,
)
from apps.reportes.serializers import (
    MENSAJE_CAMPO_NO_ADMITIDO,
    MENSAJE_CUERPO_NO_OBJETO,
    ReporteSemanalSerializer,
)
from apps.usuarios.models import Usuario
from apps.usuarios.permissions import practicas_visibles_para
from django.db import IntegrityError, connection
from django.db.models import QuerySet
from django.test import TestCase
from rest_framework.test import APIClient

LISTA = "/api/v1/practicas/"
DETALLE = "/api/v1/practicas/{}/"
REPORTES = "/api/v1/practicas/{}/reportes/"
PAYLOAD = {"semana": 1, "horas_reportadas": 8}
CAMPOS_TARJETA = {
    "id", "estudiante_id", "tipo", "subtipo", "estado", "horas_requeridas"
}
MODELOS = (
    Usuario, Carrera, ConfiguracionCarrera, Periodo, EntidadReceptora, Practica,
    AsignacionTutor, HistorialEstado, ReporteSemanal, PlanActividades, Validacion,
)


def crear_usuario(username, rol, carrera=None):
    return Usuario.objects.create_user(
        username=username, nombre=username.title(), email=f"{username}@example.com",
        rol=rol, carrera=carrera, password=None,
    )


class FlujoFixturesMixin:
    """Dos carreras con configuración, seis roles y prácticas en varios estados."""

    assertEqual: Callable[..., None]
    assertFalse: Callable[..., None]
    assertTrue: Callable[..., None]

    @classmethod
    def setUpTestData(cls):
        cls.carrera = Carrera.objects.create(
            codigo="ING-SIS", nombre="Ingeniería de Sistemas"
        )
        cls.otra_carrera = Carrera.objects.create(codigo="DER-001", nombre="Derecho")
        for carrera in (cls.carrera, cls.otra_carrera):
            for modalidad in ("laboral", "comunitaria"):
                ConfiguracionCarrera.objects.create(
                    carrera=carrera, modalidad=modalidad, horas_requeridas=240,
                    vigente_desde=date(2020, 1, 1),
                )
        cls.entidad = EntidadReceptora.objects.create(
            nombre="Junta Parroquial de San Lucas"
        )
        cls.periodo = Periodo.objects.create(
            nombre="2026-1", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 7, 31)
        )
        cls.estudiante = crear_usuario("estudiante1", Usuario.Rol.ESTUDIANTE)
        cls.par = crear_usuario("estudiante2", Usuario.Rol.ESTUDIANTE)
        cls.tutor = crear_usuario("academico1", Usuario.Rol.TUTOR_ACADEMICO, cls.carrera)
        cls.coordinador = crear_usuario("coordinador1", Usuario.Rol.COORDINADOR, cls.carrera)
        cls.coordinador_par = crear_usuario(
            "coordinador2", Usuario.Rol.COORDINADOR, cls.otra_carrera
        )
        cls.externo = crear_usuario("externo1", Usuario.Rol.TUTOR_ENTIDAD)
        cls.practica = cls.crear(
            cls.estudiante, tutor_entidad=cls.externo, estado=Practica.Estado.EN_CURSO
        )
        cls.ayudantia = cls.crear(
            cls.estudiante, subtipo=Practica.Subtipo.AYUDANTIA_DOCENCIA,
            estado=Practica.Estado.EN_CURSO,
        )
        cls.ajena = cls.crear(cls.par, carrera=cls.otra_carrera)
        cls.cerrada = cls.crear(cls.par, estado=Practica.Estado.CERRADA)
        cls.cancelada = cls.crear(cls.par, estado=Practica.Estado.CANCELADA)
        AsignacionTutor.objects.create(
            practica=cls.practica, tutor_academico=cls.tutor, desde=date(2026, 1, 1)
        )

    @classmethod
    def crear(cls, estudiante, carrera=None, estado=None,
              subtipo=Practica.Subtipo.PRACTICA, tutor_entidad=None):
        """Asigna la práctica con el servicio de T018 y fija el estado pedido."""
        practica = asignar_practica(
            estudiante=estudiante, carrera=carrera or cls.carrera, periodo=cls.periodo,
            tipo=Practica.Tipo.LABORAL, autor=cls.coordinador, entidad=cls.entidad,
            subtipo=subtipo, tutor_entidad=tutor_entidad,
        )
        if estado is not None:
            practica.estado = estado
            practica.save(update_fields=["estado"])
        return practica

    def cliente(self, usuario=None):
        cliente = APIClient()
        if usuario is not None:
            cliente.force_authenticate(user=usuario)
        return cliente

    def ids_de_la_lista(self, usuario=None):
        respuesta = self.cliente(usuario).get(LISTA)
        self.assertEqual(respuesta.status_code, 200)
        cuerpo = respuesta.json()
        self.assertTrue(cuerpo["success"])
        return {fila["id"] for fila in cuerpo["data"]}

    def pks_carrera(self):
        return {
            self.practica.pk, self.ayudantia.pk, self.cerrada.pk, self.cancelada.pk
        }

    def crear_reporte(self, practica=None, semana=1, horas=8):
        return ReporteSemanal.objects.create(
            practica=practica or self.practica, semana=semana, horas_reportadas=horas
        )

    def fotografia(self):
        return {modelo.__name__: modelo.objects.count() for modelo in MODELOS}


class AlcanceDeFilasTests(FlujoFixturesMixin, TestCase):
    """La lista y el detalle entregan solo las prácticas visibles del actor (RF-11)."""

    def test_el_estudiante_solo_ve_sus_practicas(self):
        self.assertEqual(
            self.ids_de_la_lista(self.estudiante), {self.practica.pk, self.ayudantia.pk}
        )

    def test_el_coordinador_ve_su_carrera_y_no_la_ajena(self):
        self.assertEqual(self.ids_de_la_lista(self.coordinador), self.pks_carrera())
        self.assertEqual(self.ids_de_la_lista(self.coordinador_par), {self.ajena.pk})

    def test_el_tutor_externo_solo_ve_la_practica_vinculada_laboral(self):
        self.assertEqual(self.ids_de_la_lista(self.externo), {self.practica.pk})

    def test_anonimo_y_no_guardado_no_ven_nada(self):
        self.assertEqual(self.ids_de_la_lista(), set())
        self.assertEqual(self.ids_de_la_lista(Usuario(username="fantasma")), set())

    def test_el_alcance_respeta_una_consulta_vacia_explicita(self):
        self.assertEqual(
            practicas_visibles_para(self.coordinador, Practica.objects.none()).count(), 0
        )
        self.assertEqual(
            set(practicas_visibles_para(self.coordinador).values_list("pk", flat=True)),
            self.pks_carrera(),
        )

    def test_el_detalle_del_dueno_trae_la_tarjeta(self):
        respuesta = self.cliente(self.estudiante).get(DETALLE.format(self.practica.pk))
        self.assertEqual(respuesta.status_code, 200)
        tarjeta = respuesta.json()["data"]
        self.assertEqual(set(tarjeta), CAMPOS_TARJETA)
        self.assertEqual(tarjeta["estudiante_id"], self.estudiante.pk)
        self.assertEqual(tarjeta["tipo"], Practica.Tipo.LABORAL)

    def test_el_detalle_fuera_de_alcance_o_inexistente_es_404(self):
        for actor, practica in (
            (self.coordinador_par, self.practica.pk), (self.estudiante, 999_999),
        ):
            with self.subTest(actor=getattr(actor, "username", "anon")):
                respuesta = self.cliente(actor).get(DETALLE.format(practica))
                self.assertEqual(respuesta.status_code, 404)
                self.assertFalse(respuesta.json()["success"])


class RegistroDeReportesTests(FlujoFixturesMixin, TestCase):
    """POST del reporte semanal: 201 al crear y rechazos con envelope sin escribir."""

    def publicar(self, actor, practica, datos=PAYLOAD):
        return self.cliente(actor).post(
            REPORTES.format(practica), datos, format="json"
        )

    def assertRechazo(self, respuesta, estado, mensaje, errores):
        """Estado, envelope exacto (mensaje y ``errors`` con ``code``) y sin datos."""
        self.assertEqual(respuesta.status_code, estado)
        self.assertEqual(
            respuesta.json(),
            {
                "success": False, "message": mensaje, "data": None,
                "errors": errores, "meta": {},
            },
        )

    def assertSinEscrituras(self, antes):
        self.assertEqual(self.fotografia(), antes)

    def test_el_post_registra_el_reporte_y_responde_201(self):
        respuesta = self.publicar(self.estudiante, self.practica.pk)
        self.assertEqual(respuesta.status_code, 201)
        cuerpo = respuesta.json()
        self.assertTrue(cuerpo["success"])
        self.assertEqual(cuerpo["data"]["semana"], 1)
        self.assertEqual(cuerpo["data"]["horas_reportadas"], 8)
        self.assertEqual(cuerpo["data"]["estado"], ReporteSemanal.Estado.EN_REVISION)
        self.assertEqual(cuerpo["data"]["practica_id"], self.practica.pk)
        self.assertIs(cuerpo["data"]["requiere_revision"], False)
        self.assertTrue(cuerpo["data"]["fecha_registro"])
        reporte = ReporteSemanal.objects.get(practica=self.practica)
        self.assertEqual((reporte.semana, reporte.horas_reportadas), (1, 8))

    def test_un_campo_fuera_del_data_model_se_rechaza(self):
        antes = self.fotografia()
        for campo in ("contenido", "requiere_revision", "estado"):
            with self.subTest(campo=campo):
                respuesta = self.publicar(
                    self.estudiante, self.practica.pk, {**PAYLOAD, campo: "x"}
                )
                self.assertRechazo(
                    respuesta, 400, "Datos inválidos.",
                    {campo: [MENSAJE_CAMPO_NO_ADMITIDO]},
                )
        self.assertSinEscrituras(antes)

    def test_semana_y_horas_deben_ser_positivas(self):
        antes = self.fotografia()
        casos = (
            ("semana", 0, MENSAJE_SEMANA), ("horas_reportadas", 0, MENSAJE_HORAS),
        )
        for campo, valor, mensaje in casos:
            with self.subTest(campo=campo, valor=valor):
                respuesta = self.publicar(
                    self.estudiante, self.practica.pk, {**PAYLOAD, campo: valor}
                )
                self.assertRechazo(respuesta, 400, "Datos inválidos.", {campo: [mensaje]})
        respuesta = self.publicar(
            self.estudiante, self.practica.pk, {**PAYLOAD, "horas_reportadas": -3}
        )
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(list(respuesta.json()["errors"]), ["horas_reportadas"])
        self.assertSinEscrituras(antes)

    def test_un_cuerpo_que_no_es_objeto_responde_400_y_no_500(self):
        antes = self.fotografia()
        for cuerpo in ([{"semana": 1}], ["semana"], "semana", 7):
            with self.subTest(cuerpo=cuerpo):
                respuesta = self.publicar(self.estudiante, self.practica.pk, cuerpo)
                self.assertRechazo(
                    respuesta, 400, "Datos inválidos.",
                    {"non_field_errors": [MENSAJE_CUERPO_NO_OBJETO]},
                )
        self.assertSinEscrituras(antes)

    def test_la_semana_duplicada_responde_409_con_su_code_sin_escribir(self):
        self.crear_reporte()
        antes = self.fotografia()
        respuesta = self.publicar(self.estudiante, self.practica.pk)
        self.assertRechazo(
            respuesta, 409, "Solicitud inválida.",
            {"detail": MENSAJE_SEMANA_DUPLICADA, "code": "semana_duplicada"},
        )
        self.assertSinEscrituras(antes)

    def test_la_restriccion_de_semana_unica_de_la_base_responde_409(self):
        """La carrera entre dos envíos llega al INSERT: la base es la última red."""
        self.crear_reporte()
        antes = self.fotografia()
        with mock.patch("apps.reportes.api.semana_ya_reportada", return_value=False):
            respuesta = self.publicar(self.estudiante, self.practica.pk)
        self.assertRechazo(
            respuesta, 409, "Solicitud inválida.",
            {"detail": MENSAJE_SEMANA_DUPLICADA, "code": "semana_duplicada"},
        )
        self.assertSinEscrituras(antes)

    def test_la_semana_unica_se_reconoce_en_los_mensajes_de_sqlite_y_postgresql(self):
        antes = self.fotografia()
        mensajes = (
            "UNIQUE constraint failed: reportes_reportesemanal.practica_id, "
            "reportes_reportesemanal.semana",
            'duplicate key value violates unique constraint '
            '"reportes_reporte_semana_unica"',
        )
        for mensaje in mensajes:
            with self.subTest(mensaje=mensaje), mock.patch.object(
                ReporteSemanalSerializer, "create", side_effect=IntegrityError(mensaje)
            ):
                respuesta = self.publicar(self.estudiante, self.practica.pk)
                self.assertRechazo(
                    respuesta, 409, "Solicitud inválida.",
                    {"detail": MENSAJE_SEMANA_DUPLICADA, "code": "semana_duplicada"},
                )
        self.assertSinEscrituras(antes)

    def test_otro_integrity_error_no_se_disfraza_de_semana_duplicada(self):
        antes = self.fotografia()
        with mock.patch.object(
            ReporteSemanalSerializer, "create",
            side_effect=IntegrityError("FOREIGN KEY constraint failed"),
        ), self.assertLogs("apps.contrato.exceptions", "ERROR"):
            respuesta = self.publicar(self.estudiante, self.practica.pk)
        self.assertRechazo(
            respuesta, 500, "Error interno del servidor.",
            {"detail": "Ocurrió un error inesperado.", "code": "error_interno"},
        )
        self.assertSinEscrituras(antes)

    def test_la_ayudantia_rechaza_mas_de_10_horas_con_el_art_341(self):
        antes = self.fotografia()
        respuesta = self.publicar(
            self.estudiante, self.ayudantia.pk, {"semana": 1, "horas_reportadas": 11}
        )
        self.assertRechazo(
            respuesta, 400, "Datos inválidos.",
            {"horas_reportadas": [MENSAJE_AYUDANTIA]},
        )
        self.assertSinEscrituras(antes)

    def test_la_ayudantia_admite_exactamente_10_horas(self):
        respuesta = self.publicar(
            self.estudiante, self.ayudantia.pk, {"semana": 1, "horas_reportadas": 10}
        )
        self.assertEqual(respuesta.status_code, 201)
        self.assertIs(respuesta.json()["data"]["requiere_revision"], False)
        self.assertEqual(ReporteSemanal.objects.count(), 1)

    def test_mas_de_40_horas_se_acepta_y_queda_marcado_para_revision(self):
        """S5: la práctica laboral o comunitaria con > 40 h se identifica para el tutor."""
        for semana, horas, marcado in ((1, 40, False), (2, 41, True), (3, 168, True)):
            with self.subTest(horas=horas):
                respuesta = self.publicar(
                    self.estudiante, self.practica.pk,
                    {"semana": semana, "horas_reportadas": horas},
                )
                self.assertEqual(respuesta.status_code, 201)
                self.assertIs(respuesta.json()["data"]["requiere_revision"], marcado)
                reporte = ReporteSemanal.objects.get(practica=self.practica, semana=semana)
                self.assertIs(reporte.requiere_revision, marcado)

    def test_mas_de_168_horas_por_semana_es_imposible_y_se_rechaza(self):
        antes = self.fotografia()
        respuesta = self.publicar(
            self.estudiante, self.practica.pk, {"semana": 1, "horas_reportadas": 169}
        )
        self.assertRechazo(
            respuesta, 400, "Datos inválidos.", {"horas_reportadas": [MENSAJE_TOPE_SEMANAL]}
        )
        self.assertSinEscrituras(antes)

    def test_sin_actor_responde_401_con_su_code(self):
        antes = self.fotografia()
        respuesta = self.publicar(None, self.practica.pk)
        self.assertRechazo(
            respuesta, 401, "Autenticación requerida.",
            {"detail": "Se requiere autenticación.", "code": "no_autenticado"},
        )
        self.assertSinEscrituras(antes)

    def test_un_actor_guardado_pero_inactivo_o_no_guardado_responde_401(self):
        inactivo = crear_usuario("inactivo1", Usuario.Rol.ESTUDIANTE)
        Usuario.objects.filter(pk=inactivo.pk).update(is_active=False)
        antes = self.fotografia()
        for actor in (inactivo, Usuario(username="fantasma", rol=Usuario.Rol.ESTUDIANTE)):
            with self.subTest(actor=actor.username):
                respuesta = self.publicar(actor, self.practica.pk)
                self.assertRechazo(
                    respuesta, 401, "Autenticación requerida.",
                    {"detail": "Se requiere autenticación.", "code": "no_autenticado"},
                )
        self.assertSinEscrituras(antes)

    def test_un_actor_que_no_es_estudiante_responde_403_aunque_la_practica_exista(self):
        antes = self.fotografia()
        for actor in (self.tutor, self.coordinador, self.externo):
            with self.subTest(actor=actor.username):
                respuesta = self.publicar(actor, self.practica.pk)
                self.assertRechazo(
                    respuesta, 403, "Permiso denegado.",
                    {"detail": MENSAJE_ACTOR, "code": "permiso_denegado"},
                )
        self.assertSinEscrituras(antes)

    def test_practica_inexistente_y_ajena_dan_el_mismo_404_sin_fuga(self):
        antes = self.fotografia()
        ajena = self.publicar(self.estudiante, self.ajena.pk)
        ajena_cerrada = self.publicar(self.estudiante, self.cerrada.pk)
        inexistente = self.publicar(self.estudiante, 999_999)
        self.assertRechazo(
            inexistente, 404, "Recurso no encontrado.",
            {"detail": "No encontrado.", "code": "no_encontrado"},
        )
        self.assertEqual(ajena.status_code, 404)
        self.assertEqual(ajena.json(), inexistente.json())
        self.assertEqual(ajena_cerrada.status_code, 404)
        self.assertEqual(ajena_cerrada.json(), inexistente.json())
        self.assertSinEscrituras(antes)

    def test_solo_una_practica_en_curso_acepta_reportes(self):
        estados = (
            Practica.Estado.ASIGNADA, Practica.Estado.SUSPENDIDA,
            Practica.Estado.EN_REVISION_FINAL, Practica.Estado.CERRADA,
            Practica.Estado.CANCELADA,
        )
        for estado in estados:
            with self.subTest(estado=estado):
                practica = self.crear(self.estudiante, estado=estado)
                antes = self.fotografia()
                respuesta = self.publicar(self.estudiante, practica.pk)
                self.assertRechazo(
                    respuesta, 409, "Solicitud inválida.",
                    {
                        "detail": MENSAJE_NO_EN_CURSO.format(estado=estado),
                        "code": "practica_no_en_curso",
                    },
                )
                self.assertSinEscrituras(antes)

    def test_la_practica_se_busca_dentro_de_una_transaccion_con_select_for_update(self):
        observado = []
        original = QuerySet.select_for_update

        def espia(consulta, *args, **kwargs):
            observado.append(len(connection.savepoint_ids))
            return original(consulta, *args, **kwargs)

        base = len(connection.savepoint_ids)
        with mock.patch.object(QuerySet, "select_for_update", espia):
            respuesta = self.publicar(self.estudiante, self.practica.pk)
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(len(observado), 1)
        self.assertGreater(observado[0], base)

    def test_un_rechazo_no_cambia_datos_ni_contadores(self):
        self.crear_reporte()
        antes = self.fotografia()
        rechazos = (
            (self.estudiante, self.practica.pk, {**PAYLOAD, "semana": 2, "extra": 1}, 400),
            (self.estudiante, self.practica.pk, {"semana": 0, "horas_reportadas": 8}, 400),
            (self.estudiante, self.practica.pk, {"semana": 2, "horas_reportadas": 200}, 400),
            (self.estudiante, self.practica.pk, PAYLOAD, 409),
            (self.estudiante, self.ayudantia.pk, {"semana": 1, "horas_reportadas": 12}, 400),
            (self.par, self.practica.pk, PAYLOAD, 404),
            (self.par, self.cerrada.pk, PAYLOAD, 409),
            (self.tutor, self.practica.pk, PAYLOAD, 403),
            (None, self.practica.pk, PAYLOAD, 401),
        )
        for actor, practica, datos, estado in rechazos:
            with self.subTest(practica=practica, datos=datos, actor=actor):
                respuesta = self.publicar(actor, practica, datos)
                self.assertEqual(respuesta.status_code, estado)
                self.assertFalse(respuesta.json()["success"])
                if estado != 400:
                    self.assertIn("code", respuesta.json()["errors"])
                self.assertSinEscrituras(antes)

    def documento(self):
        respuesta = self.client.get("/api/v1/schema/")
        self.assertEqual(respuesta.status_code, 200)
        return yaml.safe_load(respuesta.content)

    def test_el_endpoint_aparece_en_swagger_con_sus_errores(self):
        documento = self.documento()
        self.assertIn("get", documento["paths"][LISTA])
        operacion = documento["paths"]["/api/v1/practicas/{practica_id}/reportes/"]["post"]
        self.assertLessEqual(
            {"201", "400", "401", "403", "404", "409"}, set(operacion["responses"])
        )
        esquema = operacion["requestBody"]["content"]["application/json"]["schema"]
        self.assertEqual(esquema, {"$ref": "#/components/schemas/ReporteSemanal"})
        componente = documento["components"]["schemas"]["ReporteSemanal"]
        escribibles = {
            nombre for nombre, campo in componente["properties"].items()
            if not campo.get("readOnly")
        }
        self.assertEqual(escribibles, {"semana", "horas_reportadas"})
        self.assertIn("requiere_revision", componente["properties"])

    def test_el_path_de_detalle_aparece_en_swagger_con_su_404(self):
        documento = self.documento()
        operacion = documento["paths"]["/api/v1/practicas/{practica_id}/"]["get"]
        self.assertLessEqual({"200", "404"}, set(operacion["responses"]))


class PreservacionDemoTests(TestCase):
    """Retirado del demo (opción A): lo preservado conserva su payload."""

    def test_alertas_conserva_la_url_de_la_practica(self):
        from apps.prototipo.dto import to_alerta_dto

        salida = to_alerta_dto(
            {
                "tipo": "rezago", "tipo_display": "Rezago", "estado_badge": "warn",
                "detalle": "Detalle", "fecha": "2026-03-10",
                "practica": {
                    "id": 77, "estudiante": "Estudiante Um", "tipo": "laboral",
                    "tipo_display": "Laboral", "carrera": "ING",
                },
            },
            rol="estudiante",
        )
        self.assertEqual(salida["practica"]["url"], "/api/v1/practicas/77/")
        self.assertEqual(salida["practica"]["detalle_url"], "/prototipo/mi-practica/?practica=laboral")

    def test_el_dto_de_practica_payload_igual_con_url_real(self):
        from apps.prototipo.dto import PRACTICE_FIELDS, to_practica_dto

        salida = to_practica_dto(
            {
                **{campo: f"valor-{campo}" for campo in PRACTICE_FIELDS},
                "id": 77,
            },
            resumido=True,
        )
        self.assertEqual(salida["url"], "/api/v1/practicas/77/")

    def test_el_dto_de_practica_conserva_la_posicion_de_la_url(self):
        """``url`` sigue a los campos de la práctica, como antes de #78."""
        from apps.prototipo.dto import PRACTICE_FIELDS, to_practica_dto

        practica = {
            **{campo: f"valor-{campo}" for campo in PRACTICE_FIELDS},
            "id": 77, "reportes": [],
        }
        for resumido in (True, False):
            with self.subTest(resumido=resumido):
                claves = list(to_practica_dto(practica, resumido=resumido))
                self.assertEqual(claves[: len(PRACTICE_FIELDS)], list(PRACTICE_FIELDS))
                self.assertEqual(claves[len(PRACTICE_FIELDS)], "url")

    def test_las_tres_rutas_reales_responden_antes_que_el_demo(self):
        from django.urls import resolve

        salida = resolve("/api/v1/practicas/")
        self.assertIn("PracticasListaView", salida.func.view_class.__name__)
