"""Lectura de un reporte semanal con la observación de su devolución (RF-03, S6).

``GET /api/v1/reportes/{id}/`` cierra el bucle de corrección de HU-03: el
estudiante recupera la observación con la que el tutor académico devolvió su
reporte, y el tutor y los roles con carrera leen el mismo reporte dentro de su
alcance. La lectura es multirrol y no exige un rol concreto, sino que la
práctica del reporte esté en el alcance de filas de T019
(``practicas_visibles_para``): un reporte ajeno responde el mismo 404 que uno
inexistente, sin oráculo de existencia.

La observación se devuelve **solo** cuando el reporte está «devuelto» y es la de
la última ``Validacion`` de devolución: un reenvío posterior deja el reporte en
«en revisión» y la lectura ya no expone la observación anterior. Sin token, el
contrato responde 401 con el envelope universal. La ruta solo lee: ninguna
prueba crea, actualiza ni borra filas por su intermedio.
"""

from collections.abc import Callable
from datetime import date
from typing import cast

from django.test import TestCase
from django.utils.dateparse import parse_datetime
from rest_framework.test import APIClient

from apps.actividades.models import Validacion
from apps.carreras.models import Carrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import AsignacionTutor, Periodo, Practica
from apps.reportes.models import ReporteSemanal
from apps.usuarios.models import Usuario
from tests.integration.test_inicio_practica import RespuestaAPI

DETALLE = "/api/v1/reportes/{}/"
PRIMERA_OBSERVACION = "Detalle las semanas 3 y 4."
SEGUNDA_OBSERVACION = "Falta la evidencia de la semana 4."
CAMPOS_REPORTE = {"id", "semana", "horas_reportadas", "estado", "fecha_registro"}
CAMPOS_DEVOLUCION = {"observacion", "autor_id", "fecha"}


def crear_usuario(username, rol, carrera=None):
    return Usuario.objects.create_user(
        username=username,
        nombre=username.title(),
        email=f"{username}@example.com",
        rol=rol,
        carrera=carrera,
        password=None,
    )


class DetalleReporteFixturesMixin:
    """Una práctica asignada al tutor, una ajena y un reporte devuelto."""

    assertEqual: Callable[..., None]
    assertIn: Callable[..., None]
    assertIs: Callable[..., None]
    assertIsNone: Callable[..., None]
    assertIsNotNone: Callable[..., None]
    assertTrue: Callable[..., None]

    @classmethod
    def setUpTestData(cls):
        cls.carrera = Carrera.objects.create(
            codigo="ING-SIS", nombre="Ingeniería de Sistemas"
        )
        cls.entidad = EntidadReceptora.objects.create(
            nombre="Junta Parroquial de San Lucas"
        )
        cls.periodo = Periodo.objects.create(
            nombre="2026-1", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 7, 31)
        )
        cls.estudiante = crear_usuario("estudiante1", Usuario.Rol.ESTUDIANTE)
        cls.par = crear_usuario("estudiante2", Usuario.Rol.ESTUDIANTE)
        cls.tutor = crear_usuario(
            "academico1", Usuario.Rol.TUTOR_ACADEMICO, cls.carrera
        )
        cls.otro_tutor = crear_usuario(
            "academico2", Usuario.Rol.TUTOR_ACADEMICO, cls.carrera
        )
        cls.coordinador = crear_usuario(
            "coordinador1", Usuario.Rol.COORDINADOR, cls.carrera
        )
        cls.practica = cls.crear_practica(cls.estudiante)
        cls.ajena = cls.crear_practica(cls.par)
        AsignacionTutor.objects.create(
            practica=cls.practica, tutor_academico=cls.tutor, desde=date(2026, 1, 1)
        )

    @classmethod
    def crear_practica(cls, estudiante):
        practica = Practica(
            estudiante=estudiante,
            carrera=cls.carrera,
            entidad=cls.entidad,
            periodo=cls.periodo,
            tipo=Practica.Tipo.LABORAL,
            subtipo=Practica.Subtipo.PRACTICA,
            horas_requeridas=240,
        )
        practica.full_clean()
        practica.save()
        return practica

    def crear_reporte(self, practica=None, semana=1, horas=8, estado=None):
        datos = {"practica": practica or self.practica, "semana": semana}
        datos["horas_reportadas"] = horas
        if estado is not None:
            datos["estado"] = estado
        return ReporteSemanal.objects.create(**datos)

    def devolver(self, reporte, observacion, autor=None):
        """Registra la ``Validacion`` devuelta y deja el reporte «devuelto»."""
        return Validacion.objects.create(
            practica=reporte.practica,
            reporte=reporte,
            decision=Validacion.Decision.DEVUELTO,
            observacion=observacion,
            autor=autor or self.tutor,
        )

    def cliente(self, usuario=None):
        cliente = APIClient()
        if usuario is not None:
            cliente.force_authenticate(user=usuario)
        return cliente

    def obtener(self, usuario, reporte) -> RespuestaAPI:
        return cast(
            RespuestaAPI,
            self.cliente(usuario).get(DETALLE.format(getattr(reporte, "pk", reporte))),
        )

    def assertExito(self, respuesta):
        self.assertEqual(respuesta.status_code, 200)
        cuerpo = respuesta.json()
        self.assertIs(cuerpo["success"], True)
        self.assertEqual(cuerpo["message"], "Operación exitosa.")
        self.assertEqual(cuerpo["errors"], None)
        self.assertEqual(cuerpo["meta"], {})
        return cuerpo["data"]

    def assertSinOráculo(self, respuesta):
        """404 idéntico para un reporte ajeno y uno inexistente."""
        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(
            respuesta.json(),
            {
                "success": False,
                "message": "Recurso no encontrado.",
                "data": None,
                "errors": {"detail": "No encontrado.", "code": "no_encontrado"},
                "meta": {},
            },
        )


class DetalleReporteDevueltoTests(DetalleReporteFixturesMixin, TestCase):
    """HU-03: el estudiante dueño recupera la observación de la devolución."""

    def test_el_estudiante_dueno_lee_su_reporte_devuelto_con_la_observacion(self):
        reporte = self.crear_reporte(semana=3, horas=12)
        validacion = self.devolver(reporte, PRIMERA_OBSERVACION)
        ReporteSemanal.objects.filter(pk=reporte.pk).update(estado="devuelto")

        data = self.assertExito(self.obtener(self.estudiante, reporte))

        self.assertEqual(set(data), CAMPOS_REPORTE | {"devolucion"})
        self.assertEqual(data["id"], reporte.pk)
        self.assertEqual(data["semana"], 3)
        self.assertEqual(data["horas_reportadas"], 12)
        self.assertEqual(data["estado"], ReporteSemanal.Estado.DEVUELTO)
        self.assertEqual(
            parse_datetime(data["fecha_registro"]), reporte.fecha_registro
        )
        self.assertEqual(set(data["devolucion"]), CAMPOS_DEVOLUCION)
        self.assertEqual(data["devolucion"]["observacion"], PRIMERA_OBSERVACION)
        self.assertEqual(data["devolucion"]["autor_id"], self.tutor.pk)
        self.assertEqual(
            parse_datetime(data["devolucion"]["fecha"]), validacion.fecha
        )

    def test_la_observacion_es_la_de_la_ultima_devolucion(self):
        """Dos devoluciones: la lectura expone la última, no la primera."""
        reporte = self.crear_reporte(semana=2)
        self.devolver(reporte, PRIMERA_OBSERVACION)
        ultima = self.devolver(reporte, SEGUNDA_OBSERVACION)
        ReporteSemanal.objects.filter(pk=reporte.pk).update(estado="devuelto")

        data = self.assertExito(self.obtener(self.estudiante, reporte))

        self.assertEqual(data["devolucion"]["observacion"], SEGUNDA_OBSERVACION)
        self.assertEqual(
            parse_datetime(data["devolucion"]["fecha"]), ultima.fecha
        )

    def test_sin_devolucion_no_hay_observacion(self):
        """«En revisión» y «validado» no publican observación alguna."""
        en_revision = self.crear_reporte(semana=1)
        validado = self.crear_reporte(semana=2, estado=ReporteSemanal.Estado.VALIDADO)
        Validacion.objects.create(
            practica=validado.practica,
            reporte=validado,
            decision=Validacion.Decision.APROBADO,
            autor=self.tutor,
        )

        for reporte in (en_revision, validado):
            with self.subTest(estado=reporte.estado):
                data = self.assertExito(self.obtener(self.estudiante, reporte))
                self.assertEqual(set(data), CAMPOS_REPORTE | {"devolucion"})
                self.assertIsNone(data["devolucion"])

    def test_el_reenvio_deja_de_exponer_la_observacion_anterior(self):
        """Un reporte corregido vuelve a «en revisión» y ya no muestra la devolución."""
        reporte = self.crear_reporte(semana=1)
        self.devolver(reporte, PRIMERA_OBSERVACION)
        ReporteSemanal.objects.filter(pk=reporte.pk).update(estado="en_revision")

        data = self.assertExito(self.obtener(self.estudiante, reporte))

        self.assertIsNone(data["devolucion"])

    def test_el_tutor_academico_lee_el_reporte_de_su_practicante(self):
        reporte = self.crear_reporte(semana=1)
        self.devolver(reporte, PRIMERA_OBSERVACION)
        ReporteSemanal.objects.filter(pk=reporte.pk).update(estado="devuelto")

        data = self.assertExito(self.obtener(self.tutor, reporte))

        self.assertEqual(data["devolucion"]["observacion"], PRIMERA_OBSERVACION)

    def test_la_lectura_no_escribe_nada(self):
        reporte = self.crear_reporte(semana=1)
        self.devolver(reporte, PRIMERA_OBSERVACION)
        ReporteSemanal.objects.filter(pk=reporte.pk).update(estado="devuelto")
        antes = (
            ReporteSemanal.objects.count(),
            Validacion.objects.count(),
            tuple(ReporteSemanal.objects.values_list("pk", "estado")),
        )

        self.assertExito(self.obtener(self.estudiante, reporte))
        self.assertExito(self.obtener(self.tutor, reporte))

        self.assertEqual(
            (
                ReporteSemanal.objects.count(),
                Validacion.objects.count(),
                tuple(ReporteSemanal.objects.values_list("pk", "estado")),
            ),
            antes,
        )


class DetalleReporteAlcanceTests(DetalleReporteFixturesMixin, TestCase):
    """RF-11: el alcance de filas de T019 decide quién lee el reporte."""

    def test_un_reporte_ajeno_y_uno_inexistente_responden_el_mismo_404(self):
        ajeno = self.crear_reporte(practica=self.ajena, semana=1)

        self.assertSinOráculo(self.obtener(self.estudiante, ajeno))
        self.assertSinOráculo(self.obtener(self.estudiante, 999_999))

    def test_otro_tutor_no_alcanza_el_reporte_de_una_practica_ajena(self):
        ajeno = self.crear_reporte(practica=self.ajena, semana=1)

        self.assertSinOráculo(self.obtener(self.otro_tutor, ajeno))

    def test_el_coordinador_lee_los_reportes_de_su_carrera(self):
        ajeno = self.crear_reporte(practica=self.ajena, semana=1)

        self.assertEqual(self.obtener(self.coordinador, ajeno).status_code, 200)

    def test_el_rol_de_entidad_no_alcanza_los_reportes_de_la_practica(self):
        reporte = self.crear_reporte(semana=1)
        externo = crear_usuario("externo1", Usuario.Rol.TUTOR_ENTIDAD)

        self.assertSinOráculo(self.obtener(externo, reporte))

    def test_sin_token_responde_401_con_el_envelope(self):
        reporte = self.crear_reporte(semana=1)

        for actor in (None, Usuario(username="fantasma")):
            with self.subTest(actor=getattr(actor, "username", "anonimo")):
                respuesta = self.obtener(actor, reporte)
                self.assertEqual(respuesta.status_code, 401)
                self.assertEqual(
                    respuesta.json(),
                    {
                        "success": False,
                        "message": "Autenticación requerida.",
                        "data": None,
                        "errors": {
                            "detail": "Se requiere autenticación.",
                            "code": "no_autenticado",
                        },
                        "meta": {},
                    },
                )
