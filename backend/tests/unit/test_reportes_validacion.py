"""Servicios de validación del reporte semanal por el tutor académico (S3-S8, #122).

RF-03/S3: el tutor académico valida o devuelve un reporte y la devolución exige
observación. RF-04/S4: cada decisión queda registrada con su autor y su fecha en
``Validacion``. S5/S6: el reporte está «en revisión» y solo desde ahí se valida o
se devuelve; la ``Validacion`` de un reporte lleva ``reporte`` (nunca ``plan``).

La devolución es **solo de estado**: la fila sigue siendo la misma y el reporte no
tiene ``version`` (data-model §ReporteSemanal; decisión O1 de L6). El reenvío del
estudiante hace la vuelta «devuelto» -> «en revisión» sobre esa misma fila, sin
crear versiones ni validaciones.

Todo se falla cerrado con ``ValidationError``: el actor se comprueba contra la
fila guardada (nunca contra el objeto del llamador) y el permiso se resuelve antes
que el estado. Un rechazo no escribe ni cambia nada.
"""

from collections.abc import Callable
from datetime import date
from typing import Any

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.actividades.models import (
    MENSAJE_OBSERVACION,
    PlanActividades,
    Validacion,
)
from apps.carreras.models import Carrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import AsignacionTutor, Periodo, Practica
from apps.reportes.models import ReporteSemanal
from apps.reportes.services import (
    MENSAJE_AUTOR,
    MENSAJE_ESTADO_REPORTE,
    MENSAJE_ESTUDIANTE,
    MENSAJE_PRACTICA_NO_EN_CURSO,
    MENSAJE_REENVIO,
    MENSAJE_REPORTE,
    MENSAJE_TUTOR,
    devolver_reporte,
    reenviar_reporte,
    validar_reporte,
)
from apps.usuarios.models import Usuario

Estado = ReporteSemanal.Estado
Decision = Validacion.Decision
OBSERVACION = "Detalle las semanas 3 y 4."


def crear_usuario(username, rol, carrera=None):
    return Usuario.objects.create_user(
        username=username,
        nombre=username.title(),
        email=f"{username}@example.com",
        rol=rol,
        carrera=carrera,
        password=None,
    )


class ReportesValidacionFixturesMixin:
    """Dos prácticas con tutor académico activo y los seis roles del MVP."""

    assertEqual: Callable[..., None]
    assertRaises: Callable[..., Any]

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
        cls.otro_estudiante = crear_usuario("estudiante2", Usuario.Rol.ESTUDIANTE)
        cls.tutor = crear_usuario(
            "academico1", Usuario.Rol.TUTOR_ACADEMICO, cls.carrera
        )
        cls.otro_tutor = crear_usuario(
            "academico2", Usuario.Rol.TUTOR_ACADEMICO, cls.carrera
        )
        cls.coordinador = crear_usuario(
            "coordinador1", Usuario.Rol.COORDINADOR, cls.carrera
        )
        cls.tutor_entidad = crear_usuario("externo1", Usuario.Rol.TUTOR_ENTIDAD)
        cls.director = crear_usuario("director1", Usuario.Rol.DIRECTOR, cls.carrera)
        cls.secretaria = crear_usuario(
            "secretaria1", Usuario.Rol.SECRETARIA, cls.carrera
        )
        cls.practica = cls.crear_practica(cls.estudiante)
        cls.otra_practica = cls.crear_practica(cls.otro_estudiante)
        for practica in (cls.practica, cls.otra_practica):
            AsignacionTutor.objects.create(
                practica=practica, tutor_academico=cls.tutor, desde=date(2026, 3, 1)
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
            estado=Practica.Estado.EN_CURSO,
        )
        practica.full_clean()
        practica.save()
        return practica

    def crear_reporte(
        self, practica=None, semana=1, horas=8, estado=Estado.EN_REVISION
    ):
        return ReporteSemanal.objects.create(
            practica=practica or self.practica,
            semana=semana,
            horas_reportadas=horas,
            estado=estado,
        )

    def reporte_sin_guardar(self):
        return ReporteSemanal(practica=self.practica, semana=99, horas_reportadas=8)

    def estado_guardado(self):
        """Foto de filas, estados y validaciones; un rechazo no cambia nada."""
        return (
            ReporteSemanal.objects.count(),
            Validacion.objects.count(),
            PlanActividades.objects.count(),
            list(ReporteSemanal.objects.order_by("pk").values_list("estado", "semana")),
            list(Practica.objects.order_by("pk").values_list("estado", flat=True)),
        )

    def afirmar_rechazo(self, llamada, campo, mensaje, **kwargs):
        """Lanza ``ValidationError`` con ese campo y no escribe ni cambia nada."""
        antes = self.estado_guardado()
        with self.assertRaises(ValidationError) as error:
            llamada(**kwargs)
        self.assertEqual(error.exception.message_dict[campo], [mensaje])
        self.assertEqual(self.estado_guardado(), antes)

    def con_practica_en(self, estado):
        """Deja la práctica del reporte en ese estado (CU-01 2b)."""
        Practica.objects.filter(pk=self.practica.pk).update(estado=estado)

    def roles_ajenos(self):
        """Todos los roles menos el tutor académico activo y el estudiante dueño."""
        return (
            self.otro_estudiante,
            self.otro_tutor,
            self.coordinador,
            self.tutor_entidad,
            self.director,
            self.secretaria,
        )


class ValidarReporteTests(ReportesValidacionFixturesMixin, TestCase):
    """S3/S4/S6: validar registra autor y fecha y deja el reporte «validado»."""

    def test_validar_marca_validado_y_registra_la_validacion(self):
        reporte = self.crear_reporte()

        validado = validar_reporte(reporte=reporte, autor=self.tutor)

        self.assertEqual(validado.pk, reporte.pk)
        reporte.refresh_from_db()
        self.assertEqual(
            (validado.estado, reporte.estado), (Estado.VALIDADO, Estado.VALIDADO)
        )
        self.assertEqual(ReporteSemanal.objects.count(), 1)
        self.assertEqual(PlanActividades.objects.count(), 0)
        validacion = Validacion.objects.get()
        self.assertEqual(
            (
                validacion.decision,
                validacion.observacion,
                validacion.autor_id,
                validacion.reporte_id,
                validacion.plan_id,
                validacion.practica_id,
            ),
            (
                Decision.APROBADO,
                "",
                self.tutor.pk,
                reporte.pk,
                None,
                reporte.practica_id,
            ),
        )
        self.assertIsNotNone(validacion.fecha)
        self.assertEqual(list(reporte.validaciones.all()), [validacion])

    def test_validar_no_toca_la_practica_ni_otro_reporte(self):
        reporte = self.crear_reporte(semana=1)
        otro = self.crear_reporte(semana=2, horas=45)

        validar_reporte(reporte=reporte, autor=self.tutor)

        otro.refresh_from_db()
        self.assertEqual(
            (otro.estado, otro.requiere_revision), (Estado.EN_REVISION, True)
        )
        # Se lee la fila guardada, no el objeto en memoria del fixture.
        self.assertEqual(
            Practica.objects.get(pk=self.practica.pk).estado, Practica.Estado.EN_CURSO
        )
        self.assertEqual(Validacion.objects.count(), 1)

    def test_solo_el_tutor_academico_activo_de_la_practica_puede_validar(self):
        reporte = self.crear_reporte()
        for autor in self.roles_ajenos():
            with self.subTest(rol=autor.rol):
                self.afirmar_rechazo(
                    validar_reporte,
                    "autor",
                    MENSAJE_TUTOR,
                    reporte=reporte,
                    autor=autor,
                )
        for autor in (None, Usuario(username="fantasma", email="fantasma@example.com")):
            with self.subTest(autor="sin guardar"):
                self.afirmar_rechazo(
                    validar_reporte,
                    "autor",
                    MENSAJE_AUTOR,
                    reporte=reporte,
                    autor=autor,
                )

    def test_un_tutor_inactivo_o_con_la_asignacion_cerrada_no_valida(self):
        reporte = self.crear_reporte()
        inactivo = crear_usuario(
            "academico3", Usuario.Rol.TUTOR_ACADEMICO, self.carrera
        )
        AsignacionTutor.objects.create(
            practica=self.practica, tutor_academico=inactivo,
            desde=date(2026, 1, 1), hasta=date(2026, 2, 1),
        )
        Usuario.objects.filter(pk=inactivo.pk).update(is_active=False)
        self.afirmar_rechazo(
            validar_reporte, "autor", MENSAJE_TUTOR, reporte=reporte, autor=inactivo
        )
        # El tutor activo sigue pudiendo validar el mismo reporte.
        self.assertEqual(
            validar_reporte(reporte=reporte, autor=self.tutor).estado, Estado.VALIDADO
        )

    def test_solo_se_valida_un_reporte_en_revision(self):
        for i, estado in enumerate((Estado.VALIDADO, Estado.DEVUELTO)):
            with self.subTest(estado=estado):
                reporte = self.crear_reporte(semana=6 + i, estado=estado)
                self.afirmar_rechazo(
                    validar_reporte,
                    "estado",
                    MENSAJE_ESTADO_REPORTE.format(estado=estado),
                    reporte=reporte,
                    autor=self.tutor,
                )

    def test_un_reporte_sin_guardar_se_rechaza_sin_escribir(self):
        self.afirmar_rechazo(
            validar_reporte,
            "reporte",
            MENSAJE_REPORTE,
            reporte=self.reporte_sin_guardar(),
            autor=self.tutor,
        )

    def test_el_permiso_se_resuelve_antes_que_el_estado(self):
        reporte = self.crear_reporte(estado=Estado.VALIDADO)
        self.afirmar_rechazo(
            validar_reporte,
            "autor",
            MENSAJE_TUTOR,
            reporte=reporte,
            autor=self.estudiante,
        )


class DevolverReporteTests(ReportesValidacionFixturesMixin, TestCase):
    """S3/S8: devolver exige observación y deja el reporte «devuelto» al estudiante."""

    def test_devolver_sin_observacion_se_rechaza(self):
        reporte = self.crear_reporte()
        for observacion in ("", "   ", None):
            with self.subTest(observacion=observacion):
                self.afirmar_rechazo(
                    devolver_reporte,
                    "observacion",
                    MENSAJE_OBSERVACION,
                    reporte=reporte,
                    autor=self.tutor,
                    observacion=observacion,
                )

    def test_devolver_con_observacion_marca_devuelto_sin_crear_version(self):
        reporte = self.crear_reporte(semana=3, horas=12)

        devuelto = devolver_reporte(
            reporte=reporte, autor=self.tutor, observacion=f"  {OBSERVACION}  "
        )

        self.assertEqual(devuelto.pk, reporte.pk)
        reporte.refresh_from_db()
        self.assertEqual(
            (devuelto.estado, devuelto.semana, devuelto.horas_reportadas),
            (Estado.DEVUELTO, 3, 12),
        )
        self.assertEqual(reporte.estado, Estado.DEVUELTO)
        self.assertEqual(ReporteSemanal.objects.count(), 1)
        # El reporte no tiene versión: la devolución no renumeró nada (O1).
        self.assertFalse(hasattr(reporte, "version"))
        validacion = Validacion.objects.get()
        self.assertEqual(
            (
                validacion.decision,
                validacion.observacion,
                validacion.autor_id,
                validacion.reporte_id,
                validacion.plan_id,
            ),
            (Decision.DEVUELTO, OBSERVACION, self.tutor.pk, reporte.pk, None),
        )
        self.assertIsNotNone(validacion.fecha)
        self.assertEqual(list(reporte.validaciones.all()), [validacion])

    def test_solo_se_devuelve_un_reporte_en_revision(self):
        for i, estado in enumerate((Estado.VALIDADO, Estado.DEVUELTO)):
            with self.subTest(estado=estado):
                reporte = self.crear_reporte(semana=10 + i, estado=estado)
                self.afirmar_rechazo(
                    devolver_reporte,
                    "estado",
                    MENSAJE_ESTADO_REPORTE.format(estado=estado),
                    reporte=reporte,
                    autor=self.tutor,
                    observacion=OBSERVACION,
                )

    def test_solo_el_tutor_academico_activo_de_la_practica_puede_devolver(self):
        reporte = self.crear_reporte()
        for autor in self.roles_ajenos():
            with self.subTest(rol=autor.rol):
                self.afirmar_rechazo(
                    devolver_reporte,
                    "autor",
                    MENSAJE_TUTOR,
                    reporte=reporte,
                    autor=autor,
                    observacion=OBSERVACION,
                )
        self.afirmar_rechazo(
            devolver_reporte,
            "autor",
            MENSAJE_AUTOR,
            reporte=reporte,
            autor=None,
            observacion=OBSERVACION,
        )

    def test_un_reporte_sin_guardar_se_rechaza_sin_escribir(self):
        self.afirmar_rechazo(
            devolver_reporte,
            "reporte",
            MENSAJE_REPORTE,
            reporte=self.reporte_sin_guardar(),
            autor=self.tutor,
            observacion=OBSERVACION,
        )

    def test_el_permiso_se_resuelve_antes_que_el_estado(self):
        reporte = self.crear_reporte(estado=Estado.VALIDADO)
        self.afirmar_rechazo(
            devolver_reporte,
            "autor",
            MENSAJE_TUTOR,
            reporte=reporte,
            autor=self.estudiante,
            observacion=OBSERVACION,
        )


class ReenviarReporteTests(ReportesValidacionFixturesMixin, TestCase):
    """S8 (HU-03): el estudiante reenvía su reporte devuelto sobre la misma fila."""

    def test_reenviar_devuelto_lo_deja_en_revision_sobre_la_misma_fila(self):
        reporte = self.crear_reporte(semana=4, horas=10)
        devolver_reporte(reporte=reporte, autor=self.tutor, observacion=OBSERVACION)

        reenviado = reenviar_reporte(reporte=reporte, autor=self.estudiante)

        self.assertEqual(reenviado.pk, reporte.pk)
        reporte.refresh_from_db()
        self.assertEqual(
            (reenviado.estado, reporte.estado), (Estado.EN_REVISION, Estado.EN_REVISION)
        )
        self.assertEqual((reporte.semana, reporte.horas_reportadas), (4, 10))
        self.assertEqual(ReporteSemanal.objects.count(), 1)
        self.assertFalse(hasattr(reporte, "version"))
        # El reenvío no es una validación: la decisión del tutor queda como estaba.
        self.assertEqual(
            list(Validacion.objects.values_list("decision", "reporte_id")),
            [(Decision.DEVUELTO, reporte.pk)],
        )

    def test_solo_se_reenvia_despues_de_una_devolucion(self):
        for estado in (Estado.EN_REVISION, Estado.VALIDADO):
            with self.subTest(estado=estado):
                reporte = self.crear_reporte(semana=len(estado) + 1, estado=estado)
                self.afirmar_rechazo(
                    reenviar_reporte,
                    "estado",
                    MENSAJE_REENVIO.format(estado=estado),
                    reporte=reporte,
                    autor=self.estudiante,
                )

    def test_solo_el_estudiante_de_la_practica_reenvia(self):
        reporte = self.crear_reporte(estado=Estado.DEVUELTO)
        for autor in (self.tutor, *self.roles_ajenos()):
            with self.subTest(rol=autor.rol):
                self.afirmar_rechazo(
                    reenviar_reporte,
                    "autor",
                    MENSAJE_ESTUDIANTE,
                    reporte=reporte,
                    autor=autor,
                )
        self.afirmar_rechazo(
            reenviar_reporte,
            "autor",
            MENSAJE_AUTOR,
            reporte=reporte,
            autor=None,
        )

    def test_un_reporte_sin_guardar_se_rechaza_sin_escribir(self):
        self.afirmar_rechazo(
            reenviar_reporte,
            "reporte",
            MENSAJE_REPORTE,
            reporte=self.reporte_sin_guardar(),
            autor=self.estudiante,
        )

class PracticaNoEnCursoTests(ReportesValidacionFixturesMixin, TestCase):
    """CU-01 2b (spec.md:497): solo una práctica en curso admite validar,
    devolver o reenviar; el permiso se resuelve antes y un rechazo no escribe."""

    ESTADOS = (
        Practica.Estado.SUSPENDIDA,
        Practica.Estado.CANCELADA,
        Practica.Estado.CERRADA,
    )

    # S9a: ni antes de empezar ni ya en revisión final la práctica está en curso.
    ESTADOS_FUERA_DE_CURSO = (
        Practica.Estado.ASIGNADA,
        Practica.Estado.EN_REVISION_FINAL,
    )

    def afirmar_practica_no_en_curso(
        self, llamada, estado_reporte, estados=None, **kwargs
    ):
        for estado in estados or self.ESTADOS:
            with self.subTest(estado=estado):
                reporte = self.crear_reporte(
                    semana=len(estado), estado=estado_reporte
                )
                self.con_practica_en(estado)
                self.afirmar_rechazo(
                    llamada,
                    "practica",
                    MENSAJE_PRACTICA_NO_EN_CURSO.format(estado=estado),
                    reporte=reporte,
                    **kwargs,
                )
                reporte.refresh_from_db()
                self.assertEqual(reporte.estado, estado_reporte)
                self.assertEqual(
                    Practica.objects.get(pk=self.practica.pk).estado, estado
                )

    def test_validar_rechaza_practica_asignada_o_en_revision_final(self):
        self.afirmar_practica_no_en_curso(
            validar_reporte,
            Estado.EN_REVISION,
            estados=self.ESTADOS_FUERA_DE_CURSO,
            autor=self.tutor,
        )

    def test_devolver_rechaza_practica_asignada_o_en_revision_final(self):
        self.afirmar_practica_no_en_curso(
            devolver_reporte,
            Estado.EN_REVISION,
            estados=self.ESTADOS_FUERA_DE_CURSO,
            autor=self.tutor,
            observacion=OBSERVACION,
        )

    def test_reenviar_rechaza_practica_asignada_o_en_revision_final(self):
        self.afirmar_practica_no_en_curso(
            reenviar_reporte,
            Estado.DEVUELTO,
            estados=self.ESTADOS_FUERA_DE_CURSO,
            autor=self.estudiante,
        )

    def test_validar_exige_practica_en_curso(self):
        self.afirmar_practica_no_en_curso(
            validar_reporte, Estado.EN_REVISION, autor=self.tutor
        )

    def test_devolver_exige_practica_en_curso(self):
        self.afirmar_practica_no_en_curso(
            devolver_reporte,
            Estado.EN_REVISION,
            autor=self.tutor,
            observacion=OBSERVACION,
        )

    def test_reenviar_exige_practica_en_curso(self):
        self.afirmar_practica_no_en_curso(
            reenviar_reporte, Estado.DEVUELTO, autor=self.estudiante
        )

    def test_el_permiso_se_resuelve_antes_que_el_estado_de_la_practica(self):
        self.con_practica_en(Practica.Estado.SUSPENDIDA)
        reporte = self.crear_reporte(estado=Estado.DEVUELTO)
        for llamada, mensaje, extra in (
            (validar_reporte, MENSAJE_TUTOR, {}),
            (devolver_reporte, MENSAJE_TUTOR, {"observacion": OBSERVACION}),
            (reenviar_reporte, MENSAJE_ESTUDIANTE, {}),
        ):
            with self.subTest(llamada=llamada.__name__):
                self.afirmar_rechazo(
                    llamada,
                    "autor",
                    mensaje,
                    reporte=reporte,
                    autor=self.otro_tutor,
                    **extra,
                )

    def test_la_practica_se_comprueba_antes_que_el_estado_del_reporte(self):
        self.con_practica_en(Practica.Estado.CANCELADA)
        reporte = self.crear_reporte(estado=Estado.VALIDADO)
        self.afirmar_rechazo(
            validar_reporte,
            "practica",
            MENSAJE_PRACTICA_NO_EN_CURSO.format(estado=Practica.Estado.CANCELADA),
            reporte=reporte,
            autor=self.tutor,
        )
