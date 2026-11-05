"""Acciones del plan de actividades: enviar, devolver y aprobar (T021/T024, HU-01).

S5: el plan enviado queda «en revisión» y el tutor lo ve pendiente; la devolución
sin observación se rechaza; la devolución con observación genera una versión nueva;
la aprobación pasa la práctica a «en curso». S12: la ``Validacion`` guarda autor y
fecha, exige observación al devolver y solo admite «aprobado» o «devuelto».
"""

from collections.abc import Callable
from datetime import date
from typing import Any

from apps.actividades.models import (
    MENSAJE_DECISION,
    MENSAJE_OBSERVACION,
    PlanActividades,
    Validacion,
)
from apps.actividades.services import (
    MENSAJE_AUTOR,
    MENSAJE_ESTADO_PLAN,
    MENSAJE_ESTUDIANTE,
    MENSAJE_TUTOR,
    aprobar_plan,
    devolver_plan,
    enviar_plan,
)
from apps.auditoria.models import HistorialEstado
from apps.carreras.models import Carrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import AsignacionTutor, Periodo, Practica
from apps.practicas.services import (
    MENSAJE_MOTIVO,
    MENSAJE_TERMINAL,
    cambiar_estado_practica,
)
from apps.usuarios.models import Usuario
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

Estado = PlanActividades.Estado
EstadoPractica = Practica.Estado
CONTENIDO = "Actividades previstas para la práctica."
OBSERVACION = "Detalle las semanas 3 y 4."


def crear_usuario(username, rol, carrera=None, **extra):
    return Usuario.objects.create_user(
        username=username, nombre=username.title(), email=f"{username}@example.com",
        rol=rol, carrera=carrera, password=None, **extra,
    )


class PlanActividadesFixturesMixin:
    """Dos prácticas con tutor académico activo y los seis roles del MVP."""

    assertEqual: Callable[..., None]
    assertRaises: Callable[..., Any]

    @classmethod
    def setUpTestData(cls):
        cls.carrera = Carrera.objects.create(codigo="ING-SIS", nombre="Ingeniería de Sistemas")
        cls.entidad = EntidadReceptora.objects.create(nombre="Junta Parroquial de San Lucas")
        cls.periodo = Periodo.objects.create(
            nombre="2026-1", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 7, 31)
        )
        cls.estudiante = crear_usuario("estudiante1", Usuario.Rol.ESTUDIANTE)
        cls.otro_estudiante = crear_usuario("estudiante2", Usuario.Rol.ESTUDIANTE)
        cls.tutor = crear_usuario("academico1", Usuario.Rol.TUTOR_ACADEMICO, cls.carrera)
        cls.otro_tutor = crear_usuario("academico2", Usuario.Rol.TUTOR_ACADEMICO, cls.carrera)
        cls.coordinador = crear_usuario("coordinador1", Usuario.Rol.COORDINADOR, cls.carrera)
        cls.tutor_entidad = crear_usuario("externo1", Usuario.Rol.TUTOR_ENTIDAD)
        cls.director = crear_usuario("director1", Usuario.Rol.DIRECTOR, cls.carrera)
        cls.secretaria = crear_usuario("secretaria1", Usuario.Rol.SECRETARIA, cls.carrera)
        cls.practica = cls.crear_practica(cls.estudiante)
        cls.otra_practica = cls.crear_practica(cls.otro_estudiante)
        for practica in (cls.practica, cls.otra_practica):
            AsignacionTutor.objects.create(
                practica=practica, tutor_academico=cls.tutor, desde=date(2026, 3, 1)
            )

    @classmethod
    def crear_practica(cls, estudiante):
        practica = Practica(
            estudiante=estudiante, carrera=cls.carrera, entidad=cls.entidad,
            periodo=cls.periodo, tipo=Practica.Tipo.LABORAL,
            subtipo=Practica.Subtipo.PRACTICA, horas_requeridas=240,
        )
        practica.full_clean()
        practica.save()
        return practica

    def enviar(self, autor=None, practica=None, contenido=CONTENIDO):
        return enviar_plan(
            practica=practica or self.practica, contenido=contenido,
            autor=autor or self.estudiante,
        )

    def guardar_plan(self, estado=Estado.EN_REVISION, version=1, practica=None):
        plan = PlanActividades(
            practica=practica or self.practica, version=version,
            contenido=CONTENIDO, estado=estado,
        )
        plan.full_clean()
        plan.save()
        return plan

    def estado_guardado(self):
        """Foto de las filas y estados; un rechazo no debe cambiar ninguna."""
        return (
            PlanActividades.objects.count(),
            Validacion.objects.count(),
            HistorialEstado.objects.count(),
            list(Practica.objects.order_by("pk").values_list("estado", flat=True)),
            list(PlanActividades.objects.order_by("pk").values_list("version", "estado")),
        )

    def afirmar_rechazo(self, llamada, campo, mensaje, **kwargs):
        """Lanza ``ValidationError`` con ese campo y no escribe ni cambia nada."""
        antes = self.estado_guardado()
        with self.assertRaises(ValidationError) as error:
            llamada(**kwargs)
        self.assertEqual(error.exception.message_dict[campo], [mensaje])
        self.assertEqual(self.estado_guardado(), antes)

    def roles_ajenos(self):
        """Todos los roles menos el tutor activo y el estudiante de la práctica."""
        return (
            self.otro_estudiante, self.otro_tutor, self.coordinador,
            self.tutor_entidad, self.director, self.secretaria,
        )


class SecuenciaTests(PlanActividadesFixturesMixin, TestCase):
    """S5/S10/S11: el ciclo completo de dos devoluciones y la aprobación final."""

    def test_dos_devoluciones_generan_dos_versiones_y_una_sola_aprobacion(self):
        v1 = self.enviar()
        v2 = devolver_plan(plan=v1, autor=self.tutor, observacion=OBSERVACION)
        v3 = devolver_plan(plan=v2, autor=self.tutor, observacion="Segunda devolución.")
        self.assertEqual(
            list(PlanActividades.objects.order_by("version").values_list("version", "estado")),
            [(1, Estado.DEVUELTO), (2, Estado.DEVUELTO), (3, Estado.EN_REVISION)],
        )
        self.assertEqual(
            list(Validacion.objects.order_by("pk").values_list("decision", "plan_id")),
            [(Validacion.Decision.DEVUELTO, v1.pk), (Validacion.Decision.DEVUELTO, v2.pk)],
        )
        aprobado = aprobar_plan(plan=v3, autor=self.tutor)
        self.assertEqual(aprobado.estado, Estado.APROBADO)
        self.assertEqual(
            list(HistorialEstado.objects.values_list("estado_anterior", "estado_nuevo")),
            [(EstadoPractica.ASIGNADA, EstadoPractica.EN_CURSO)],
        )

    def test_aprobar_una_practica_suspendida_no_deja_escritura_parcial(self):
        plan = self.enviar()
        Practica.objects.filter(pk=self.practica.pk).update(
            estado=EstadoPractica.SUSPENDIDA
        )
        self.afirmar_rechazo(
            aprobar_plan, "motivo", MENSAJE_MOTIVO,
            plan=plan, autor=self.tutor,
        )
        self.assertEqual(PlanActividades.objects.get(pk=plan.pk).estado, Estado.EN_REVISION)

    def test_el_reenvio_del_estudiante_crea_la_version_siguiente_sin_devolucion(self):
        """Comportamiento documentado: enviar de nuevo apila la versión siguiente."""
        self.enviar()
        self.assertEqual(self.enviar().version, 2)
        self.assertEqual(
            list(PlanActividades.objects.order_by("version").values_list("version", "estado")),
            [(1, Estado.EN_REVISION), (2, Estado.EN_REVISION)],
        )


class OrdenPermisoEstadoTests(PlanActividadesFixturesMixin, TestCase):
    """S7: el permiso decide antes que el estado; el filtrado nace en la consulta."""

    def test_el_permiso_se_resuelve_antes_del_estado_del_plan(self):
        plan = self.guardar_plan(estado=Estado.APROBADO, version=2)
        self.afirmar_rechazo(
            devolver_plan, "autor", MENSAJE_TUTOR,
            plan=plan, autor=self.estudiante, observacion=OBSERVACION,
        )


class EnvioTests(PlanActividadesFixturesMixin, TestCase):
    """S8: registrar y enviar deja el plan en revisión y el tutor lo ve pendiente."""

    def test_enviar_crea_la_version_uno_en_revision_y_el_tutor_la_ve_pendiente(self):
        plan = self.enviar()

        plan.refresh_from_db()
        self.assertEqual(
            (plan.version, plan.estado, plan.contenido),
            (1, Estado.EN_REVISION, CONTENIDO),
        )
        self.practica.refresh_from_db()
        self.assertEqual(self.practica.estado, EstadoPractica.ASIGNADA)
        pendientes = PlanActividades.objects.filter(
            practica__asignaciones_tutor__tutor_academico=self.tutor,
            practica__asignaciones_tutor__hasta__isnull=True,
            estado=Estado.EN_REVISION,
        )
        self.assertEqual(list(pendientes), [plan])
        self.assertEqual(Validacion.objects.count(), 0)
        self.assertEqual(HistorialEstado.objects.count(), 0)

    def test_solo_el_estudiante_de_la_practica_puede_enviar(self):
        for autor in (self.tutor, *self.roles_ajenos()):
            with self.subTest(rol=autor.rol):
                self.afirmar_rechazo(
                    enviar_plan, "autor", MENSAJE_ESTUDIANTE,
                    practica=self.practica, contenido=CONTENIDO, autor=autor,
                )
        for autor in (None, Usuario(username="fantasma", email="fantasma@example.com")):
            with self.subTest(autor="sin guardar"):
                self.afirmar_rechazo(
                    enviar_plan, "autor", MENSAJE_AUTOR,
                    practica=self.practica, contenido=CONTENIDO, autor=autor,
                )

    def test_una_practica_en_estado_final_no_acepta_el_envio(self):
        for final in (EstadoPractica.CERRADA, EstadoPractica.CANCELADA):
            with self.subTest(estado=final):
                Practica.objects.filter(pk=self.otra_practica.pk).update(estado=final)
                self.afirmar_rechazo(
                    enviar_plan, "estado", MENSAJE_TERMINAL.format(estado=final),
                    practica=self.otra_practica, contenido=CONTENIDO,
                    autor=self.otro_estudiante,
                )


class DevolucionTests(PlanActividadesFixturesMixin, TestCase):
    """S5/S9/S12: devolver exige observación y genera la siguiente versión."""

    def test_devolver_sin_observacion_se_rechaza(self):
        plan = self.enviar()
        for observacion in ("", "   ", None):
            with self.subTest(observacion=observacion):
                self.afirmar_rechazo(
                    devolver_plan, "observacion", MENSAJE_OBSERVACION,
                    plan=plan, autor=self.tutor, observacion=observacion,
                )

    def test_devolver_con_observacion_marca_devuelto_y_genera_la_version_siguiente(self):
        plan = self.enviar()

        nueva = devolver_plan(plan=plan, autor=self.tutor, observacion=f"  {OBSERVACION}  ")

        plan.refresh_from_db()
        nueva.refresh_from_db()
        self.assertEqual((plan.estado, plan.version), (Estado.DEVUELTO, 1))
        self.assertEqual(
            (nueva.estado, nueva.version, nueva.contenido),
            (Estado.EN_REVISION, 2, CONTENIDO),
        )
        validacion = Validacion.objects.get()
        self.assertEqual(
            (
                validacion.decision, validacion.observacion, validacion.autor_id,
                validacion.plan_id, validacion.practica_id,
            ),
            (Validacion.Decision.DEVUELTO, OBSERVACION, self.tutor.pk, plan.pk, self.practica.pk),
        )
        self.assertIsNotNone(validacion.fecha)
        # El estudiante ve la observación en la fila devuelta.
        self.assertEqual(list(plan.validaciones.all()), [validacion])
        self.practica.refresh_from_db()
        self.assertEqual(self.practica.estado, EstadoPractica.ASIGNADA)

    def test_solo_el_tutor_academico_de_la_practica_puede_devolver(self):
        plan = self.enviar()
        for autor in self.roles_ajenos():
            with self.subTest(rol=autor.rol):
                self.afirmar_rechazo(
                    devolver_plan, "autor", MENSAJE_TUTOR,
                    plan=plan, autor=autor, observacion=OBSERVACION,
                )
        self.afirmar_rechazo(
            devolver_plan, "autor", MENSAJE_AUTOR,
            plan=plan, autor=None, observacion=OBSERVACION,
        )

    def test_un_tutor_inactivo_o_cerrado_no_puede_devolver(self):
        plan = self.enviar()
        Usuario.objects.filter(pk=self.tutor.pk).update(is_active=False)
        self.afirmar_rechazo(
            devolver_plan, "autor", MENSAJE_TUTOR,
            plan=plan, autor=self.tutor, observacion=OBSERVACION,
        )
        Usuario.objects.filter(pk=self.tutor.pk).update(is_active=True)
        AsignacionTutor.objects.filter(practica=self.practica).update(hasta=date(2026, 3, 5))
        self.afirmar_rechazo(
            devolver_plan, "autor", MENSAJE_TUTOR,
            plan=plan, autor=self.tutor, observacion=OBSERVACION,
        )


class AprobacionTests(PlanActividadesFixturesMixin, TestCase):
    """S5/S11: aprobar marca el plan y pasa la práctica a «en curso» vía T017."""

    def test_aprobar_marca_el_plan_y_pasa_la_practica_a_en_curso(self):
        plan = self.enviar()

        aprobado = aprobar_plan(plan=plan, autor=self.tutor)

        aprobado.refresh_from_db()
        self.practica.refresh_from_db()
        self.assertEqual(aprobado.estado, Estado.APROBADO)
        self.assertEqual(self.practica.estado, EstadoPractica.EN_CURSO)
        registro = HistorialEstado.objects.get(practica=self.practica)
        self.assertEqual(
            (registro.estado_anterior, registro.estado_nuevo, registro.autor_id),
            (EstadoPractica.ASIGNADA, EstadoPractica.EN_CURSO, self.tutor.pk),
        )
        validacion = Validacion.objects.get()
        self.assertEqual(
            (validacion.decision, validacion.observacion, validacion.plan_id),
            (Validacion.Decision.APROBADO, "", plan.pk),
        )

    def test_aprobar_una_practica_ya_en_curso_no_duplica_el_historial(self):
        historial = cambiar_estado_practica(
            practica=self.practica, nuevo_estado=EstadoPractica.EN_CURSO, autor=self.coordinador
        )
        plan = self.enviar()

        aprobar_plan(plan=plan, autor=self.tutor)

        plan.refresh_from_db()
        self.assertEqual(plan.estado, Estado.APROBADO)
        self.assertEqual(list(HistorialEstado.objects.values_list("estado_nuevo", flat=True)), ["en_curso"])
        self.assertEqual(historial.estado, EstadoPractica.EN_CURSO)

    def test_aprobar_no_envuelve_el_rechazo_de_la_transicion_de_t017(self):
        plan = self.enviar()
        Practica.objects.filter(pk=self.practica.pk).update(estado=EstadoPractica.CERRADA)
        self.afirmar_rechazo(
            aprobar_plan, "estado", MENSAJE_TERMINAL.format(estado=EstadoPractica.CERRADA),
            plan=plan, autor=self.tutor,
        )
        self.assertEqual(PlanActividades.objects.get(pk=plan.pk).estado, Estado.EN_REVISION)

    def test_solo_el_tutor_academico_activo_puede_aprobar(self):
        plan = self.enviar()
        for autor in self.roles_ajenos():
            with self.subTest(rol=autor.rol):
                self.afirmar_rechazo(aprobar_plan, "autor", MENSAJE_TUTOR, plan=plan, autor=autor)
        Usuario.objects.filter(pk=self.tutor.pk).update(is_active=False)
        self.afirmar_rechazo(aprobar_plan, "autor", MENSAJE_TUTOR, plan=plan, autor=self.tutor)


class ValidacionEstadoTests(PlanActividadesFixturesMixin, TestCase):
    """Ningún transición se aplica a un plan fuera de «en revisión»."""

    def test_un_plan_fuera_de_en_revision_no_se_valida(self):
        for estado in (Estado.DEVUELTO, Estado.APROBADO):
            plan = self.guardar_plan(estado=estado, version=2)
            for servicio, extra in (
                (devolver_plan, {"observacion": OBSERVACION}),
                (aprobar_plan, {}),
            ):
                with self.subTest(estado=estado, servicio=servicio.__name__):
                    self.afirmar_rechazo(
                        servicio, "estado", MENSAJE_ESTADO_PLAN.format(estado=estado),
                        plan=plan, autor=self.tutor, **extra,
                    )


class PermisosQueNoSeSaltanTests(PlanActividadesFixturesMixin, TestCase):
    """El rol guardado manda: ni staff ni superusuario evitan el permiso."""

    def test_el_staff_o_superusuario_no_evita_los_permisos(self):
        Usuario.objects.filter(pk=self.otro_estudiante.pk).update(is_staff=True, is_superuser=True)
        Usuario.objects.filter(pk=self.coordinador.pk).update(is_staff=True, is_superuser=True)
        self.afirmar_rechazo(
            enviar_plan, "autor", MENSAJE_ESTUDIANTE,
            practica=self.practica, contenido=CONTENIDO, autor=self.otro_estudiante,
        )
        plan = self.enviar()
        self.afirmar_rechazo(
            devolver_plan, "autor", MENSAJE_TUTOR,
            plan=plan, autor=self.coordinador, observacion=OBSERVACION,
        )
        self.afirmar_rechazo(aprobar_plan, "autor", MENSAJE_TUTOR, plan=plan, autor=self.coordinador)


class ReglasDelLlamadorTests(PlanActividadesFixturesMixin, TestCase):
    """S10: la versión, el estado y la entidad los decide el servicio, no el llamador."""

    def test_el_llamador_no_impone_version_estado_ni_entidad(self):
        plan = self.enviar()
        casos = (
            (
                enviar_plan,
                {"practica": self.otra_practica, "contenido": CONTENIDO, "autor": self.otro_estudiante},
                {"version": 7, "estado": Estado.APROBADO, "entidad": self.entidad},
            ),
            (
                devolver_plan,
                {"plan": plan, "autor": self.tutor},
                {"observacion": OBSERVACION, "estado": Estado.APROBADO, "version": 9},
            ),
            (
                aprobar_plan,
                {"plan": plan, "autor": self.tutor},
                {"version": 9, "estado": Estado.DEVUELTO, "entidad": self.entidad},
            ),
        )
        for servicio, base, impuestos in casos:
            with self.subTest(servicio=servicio.__name__):
                antes = self.estado_guardado()
                with self.assertRaises(TypeError):
                    servicio(**base, **impuestos)
                self.assertEqual(self.estado_guardado(), antes)


class ValidacionModeloTests(PlanActividadesFixturesMixin, TestCase):
    """S12: la validación apunta a un plan, tiene decision y observación al devolver."""

    def crear(self, **overrides):
        plan = overrides.pop("plan", self.guardar_plan())
        datos = {
            "practica": self.practica, "plan": plan,
            "decision": Validacion.Decision.APROBADO, "autor": self.tutor,
        }
        datos.update(overrides)
        validacion = Validacion(**datos)
        validacion.full_clean()
        validacion.save()
        return validacion

    def test_guarda_autor_y_fecha_y_aprueba_sin_observacion(self):
        validacion = self.crear()
        self.assertEqual((validacion.decision, validacion.observacion), ("aprobado", ""))
        self.assertEqual(
            (validacion.plan.practica_id, validacion.practica_id, validacion.autor_id),
            (self.practica.pk, self.practica.pk, self.tutor.pk),
        )
        self.assertIsNotNone(validacion.fecha)

    def test_devuelto_exige_una_observacion_no_vacia(self):
        for observacion in ("", "  ", None):
            with self.subTest(observacion=observacion):
                with self.assertRaises(ValidationError) as error:
                    self.crear(decision=Validacion.Decision.DEVUELTO, observacion=observacion)
                self.assertEqual(error.exception.message_dict["observacion"], [MENSAJE_OBSERVACION])
        self.assertEqual(Validacion.objects.count(), 0)

    def test_rechaza_una_decision_fuera_del_vocabulario(self):
        with self.assertRaises(ValidationError) as error:
            self.crear(decision="validado")
        self.assertEqual(error.exception.message_dict["decision"], [MENSAJE_DECISION])
        self.assertEqual(Validacion.objects.count(), 0)

    def test_la_practica_y_el_plan_son_obligatorios(self):
        for campo in ("practica", "plan", "autor"):
            with self.subTest(campo=campo):
                with self.assertRaises(ValidationError) as error:
                    self.crear(**{campo: None})
                self.assertEqual(list(error.exception.message_dict), [campo])
        with self.assertRaises(IntegrityError), transaction.atomic():
            Validacion.objects.create(
                practica=self.practica, plan=None,
                decision=Validacion.Decision.APROBADO, autor=self.tutor,
            )
