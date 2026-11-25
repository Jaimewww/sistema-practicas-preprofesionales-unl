"""Generación de la alerta de revisión vencida de una práctica (T13, HU-06 #2).

`apps.alertas.services.generar_alerta_revision_vencida` evalúa una práctica a
una fecha inyectada. Solo cuenta la práctica guardada «en curso» y dentro del
período inclusivo; son candidatos sus reportes «en_revision» con
`ingreso_revision_en` conocido, convertido a fecha en la zona configurada del
proyecto. Con candidatos se resuelve la configuración vigente de la misma
carrera y modalidad a la fecha evaluada —sin respaldo— y se aplica el plazo
estricto de días hábiles. Algún reporte vencido produce una única alerta activa
de tipo `revision_pendiente` por práctica.

La fecha de evaluación es un argumento; la `fecha` de la alerta la pone Django
al crear la fila y no se reescribe al reevaluar. La guarda y las candidatas se
deciden antes de leer configuración: sin candidatas no se exige configuración.
"""

# pyright: reportMissingImports=false, reportAttributeAccessIssue=false
from collections.abc import Callable
from datetime import UTC, date, datetime
from typing import Any
from unittest import mock

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.actividades.models import Validacion
from apps.alertas.models import Alerta
from apps.alertas.services import (
    MENSAJE_CONFIGURACION_REVISION,
    generar_alerta_revision_vencida,
)
from apps.auditoria.models import HistorialEstado
from apps.carreras.models import Carrera, ConfiguracionCarrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import Periodo, Practica
from apps.reportes.models import ReporteSemanal
from apps.usuarios.models import Usuario

INICIO = date(2026, 1, 1)
FIN = date(2026, 4, 22)
LUNES = date(2026, 3, 2)
QUINTO_DIA_HABIL = date(2026, 3, 9)
SEXTO_DIA_HABIL = date(2026, 3, 10)
ANTES_DEL_PERIODO = date(2025, 12, 31)
DESPUES_DEL_PERIODO = date(2026, 4, 23)
VIGENTE = date(2025, 9, 1)
INGRESO = datetime(2026, 3, 2, 9, 0, tzinfo=UTC)
Modalidad = ConfiguracionCarrera.Modalidad
Estado = Practica.Estado
EstadoReporte = ReporteSemanal.Estado
MENSAJE_CONFIGURACION_ESPERADO = (
    "No hay una configuración de carrera vigente para esa modalidad: "
    "no se puede evaluar el plazo de revisión de la práctica."
)


class AlertaRevisionFixturesMixin:
    """Carrera, período de 16 semanas y una práctica «en curso»."""

    carrera: Carrera
    otra_carrera: Carrera
    entidad: EntidadReceptora
    periodo: Periodo
    estudiante: Usuario
    practica: Practica

    assertEqual: Callable[..., None]
    assertIs: Callable[..., None]
    assertIsNone: Callable[..., None]
    assertIsNotNone: Callable[..., None]
    assertNotEqual: Callable[..., None]
    assertRaises: Callable[..., Any]
    subTest: Callable[..., Any]

    @classmethod
    def setUpTestData(cls):
        cls.carrera = Carrera.objects.create(
            codigo="ING-SIS", nombre="Ingeniería de Sistemas"
        )
        cls.otra_carrera = Carrera.objects.create(codigo="DER-001", nombre="Derecho")
        cls.entidad = EntidadReceptora.objects.create(
            nombre="Junta Parroquial de San Lucas"
        )
        cls.periodo = Periodo.objects.create(
            nombre="2026-1", fecha_inicio=INICIO, fecha_fin=FIN
        )
        cls.estudiante = Usuario.objects.create_user(
            username="estudiante1",
            nombre="Ana Torres",
            email="ana@example.com",
            rol=Usuario.Rol.ESTUDIANTE,
            password=None,
        )
        cls.practica = cls.crear_practica()

    @classmethod
    def crear_practica(
        cls,
        carrera: Carrera | None = None,
        estado: str = Estado.EN_CURSO,
    ) -> Practica:
        practica = Practica(
            estudiante=cls.estudiante,
            carrera=carrera or cls.carrera,
            entidad=cls.entidad,
            periodo=cls.periodo,
            tipo=Practica.Tipo.LABORAL,
            subtipo=Practica.Subtipo.PRACTICA,
            horas_requeridas=240,
            estado=estado,
        )
        practica.full_clean()
        practica.save()
        return practica

    def configurar(
        self,
        plazo: int = 5,
        desde: date = VIGENTE,
        modalidad: str = Modalidad.LABORAL,
        carrera: Carrera | None = None,
    ) -> ConfiguracionCarrera:
        return ConfiguracionCarrera.objects.create(
            carrera=carrera or self.carrera,
            modalidad=modalidad,
            horas_requeridas=240,
            plazo_revision_dias=plazo,
            vigente_desde=desde,
        )

    def reportar(
        self,
        ingreso: datetime | None = INGRESO,
        estado: str = EstadoReporte.EN_REVISION,
        practica: Practica | None = None,
        horas: int = 10,
    ) -> ReporteSemanal:
        objetivo = practica or self.practica
        return ReporteSemanal.objects.create(
            practica=objetivo,
            semana=ReporteSemanal.objects.filter(practica=objetivo).count() + 1,
            horas_reportadas=horas,
            estado=estado,
            ingreso_revision_en=ingreso,
        )

    def generar(
        self, fecha: date = SEXTO_DIA_HABIL, practica: Practica | None = None
    ) -> tuple[Alerta | None, bool]:
        return generar_alerta_revision_vencida(practica or self.practica, fecha=fecha)

    def alertas(self, practica: Practica | None = None):
        return Alerta.objects.filter(practica=practica or self.practica)


class PlazoVencidoTests(AlertaRevisionFixturesMixin, TestCase):
    """El sexto día hábil genera la alerta y el quinto no; manda la configuración."""

    def test_el_sexto_dia_habil_crea_una_alerta_de_revision_pendiente(self):
        self.configurar()
        self.reportar()

        alerta, created = self.generar()

        self.assertIs(created, True)
        assert alerta is not None
        alerta.refresh_from_db()
        self.assertEqual(alerta.practica_id, self.practica.pk)
        self.assertEqual(alerta.tipo, Alerta.Tipo.REVISION_PENDIENTE)
        self.assertIs(alerta.atendida, False)
        self.assertEqual(
            list(self.alertas().values_list("tipo", flat=True)),
            [Alerta.Tipo.REVISION_PENDIENTE],
        )
        self.assertEqual(alerta.destinatarios, (Usuario.Rol.TUTOR_ACADEMICO,))

    def test_el_quinto_dia_habil_no_genera_alerta(self):
        self.configurar()
        self.reportar()

        alerta, created = self.generar(fecha=QUINTO_DIA_HABIL)

        self.assertIsNone(alerta)
        self.assertIs(created, False)
        self.assertEqual(self.alertas().count(), 0)

    def test_un_plazo_configurado_mayor_evita_el_vencimiento(self):
        self.configurar(plazo=10)
        self.reportar()

        alerta, created = self.generar()

        self.assertIsNone(alerta)
        self.assertIs(created, False)
        self.assertEqual(self.alertas().count(), 0)

    def test_un_plazo_configurado_menor_adelanta_el_vencimiento(self):
        self.configurar(plazo=2)
        self.reportar()

        # (lun 2, jue 5]: mar 3, mié 4 y jue 5 = 3 días hábiles > 2.
        alerta, created = self.generar(fecha=date(2026, 3, 5))

        self.assertIs(created, True)
        self.assertIsNotNone(alerta)

    def test_la_fecha_de_la_alerta_es_la_de_creacion_no_la_evaluada(self):
        self.configurar()
        self.reportar()
        antes = date.today()

        alerta, _ = self.generar()

        assert alerta is not None
        alerta.refresh_from_db()
        self.assertIn(alerta.fecha, (antes, date.today()))
        self.assertNotEqual(alerta.fecha, SEXTO_DIA_HABIL)

    def test_el_ingreso_se_convierte_a_la_zona_configurada(self):
        self.configurar(plazo=4)
        # La zona activa (UTC) difiere de la configurada: manda settings.TIME_ZONE.
        # Lun 9 mar 02:00 UTC es dom 8 mar 21:00 en UTC-5: la fecha local suma
        # el lunes y da 5 días hábiles en (dom 8, vie 13]; la fecha UTC da 4.
        ingreso = datetime(2026, 3, 9, 2, 0, tzinfo=UTC)
        self.reportar(ingreso=ingreso)
        viernes = date(2026, 3, 13)

        with (
            override_settings(TIME_ZONE="America/Guayaquil"),
            timezone.override("UTC"),
        ):
            alerta, created = self.generar(fecha=viernes)

        self.assertIs(created, True)
        self.assertIsNotNone(alerta)

        otra = self.crear_practica()
        self.reportar(ingreso=ingreso, practica=otra)
        self.assertIs(self.generar(fecha=viernes, practica=otra)[1], False)


class GuardaDeEstadoYPeriodoTests(AlertaRevisionFixturesMixin, TestCase):
    """Fuera de «en curso» o del período inclusivo no se evalúa ni se escribe."""

    def test_solo_se_evaluan_las_practicas_guardadas_en_curso(self):
        for estado in (
            Estado.ASIGNADA,
            Estado.EN_REVISION_FINAL,
            Estado.CERRADA,
            Estado.SUSPENDIDA,
            Estado.CANCELADA,
        ):
            with self.subTest(estado=estado):
                practica = self.crear_practica(estado=estado)
                self.reportar(practica=practica)

                alerta, created = self.generar(practica=practica)

                self.assertIsNone(alerta)
                self.assertIs(created, False)
                self.assertEqual(self.alertas(practica).count(), 0)
        self.assertEqual(ConfiguracionCarrera.objects.count(), 0)

    def test_el_estado_guardado_manda_sobre_el_objeto_del_llamador(self):
        self.configurar()
        self.reportar()
        # En la base sigue «en curso» aunque el objeto del llamador esté obsoleto.
        self.practica.estado = Estado.CERRADA
        self.assertIs(self.generar()[1], True)

        cerrada = self.crear_practica()
        self.reportar(practica=cerrada)
        Practica.objects.filter(pk=cerrada.pk).update(estado=Estado.CANCELADA)
        self.assertIs(self.generar(practica=cerrada)[1], False)
        self.assertEqual(self.alertas(cerrada).count(), 0)

    def test_fuera_del_periodo_no_evalua_ni_necesita_configuracion(self):
        self.reportar()
        for fecha in (ANTES_DEL_PERIODO, DESPUES_DEL_PERIODO):
            with self.subTest(fecha=fecha):
                alerta, created = self.generar(fecha=fecha)

                self.assertIsNone(alerta)
                self.assertIs(created, False)
        self.assertEqual(self.alertas().count(), 0)
        self.assertEqual(ConfiguracionCarrera.objects.count(), 0)

    def test_los_extremos_del_periodo_cuentan_como_dentro(self):
        self.configurar(plazo=0)
        ingreso = datetime(2025, 12, 30, 9, 0, tzinfo=UTC)
        self.reportar(ingreso=ingreso)
        otra = self.crear_practica()
        self.reportar(ingreso=ingreso, practica=otra)

        primera, created_inicio = self.generar(fecha=INICIO)
        segunda, created_fin = self.generar(fecha=FIN, practica=otra)

        self.assertIs(created_inicio, True)
        self.assertIs(created_fin, True)
        assert primera is not None
        assert segunda is not None
        self.assertEqual(primera.practica_id, self.practica.pk)
        self.assertEqual(segunda.practica_id, otra.pk)

    def test_una_practica_sin_guardar_no_produce_alerta_ni_error(self):
        self.configurar()
        sin_guardar = Practica(
            estudiante=self.estudiante,
            carrera=self.carrera,
            entidad=self.entidad,
            periodo=self.periodo,
            tipo=Practica.Tipo.LABORAL,
            subtipo=Practica.Subtipo.PRACTICA,
            horas_requeridas=240,
            estado=Estado.EN_CURSO,
        )

        alerta, created = self.generar(practica=sin_guardar)

        self.assertIsNone(alerta)
        self.assertIs(created, False)
        self.assertEqual(Alerta.objects.count(), 0)


class CandidatasTests(AlertaRevisionFixturesMixin, TestCase):
    """Solo los reportes «en_revision» con ingreso conocido de esa práctica."""

    def test_un_ingreso_desconocido_no_es_candidato_ni_infiere_fecha(self):
        reporte = self.reportar(ingreso=None)

        alerta, created = self.generar()

        self.assertIsNone(alerta)
        self.assertIs(created, False)
        self.assertEqual(self.alertas().count(), 0)
        self.assertEqual(ConfiguracionCarrera.objects.count(), 0)
        reporte.refresh_from_db()
        self.assertIsNone(reporte.ingreso_revision_en)

    def test_otros_estados_no_son_candidatos(self):
        ingreso_viejo = datetime(2025, 12, 29, 9, 0, tzinfo=UTC)
        for estado in (EstadoReporte.VALIDADO, EstadoReporte.DEVUELTO):
            with self.subTest(estado=estado):
                self.reportar(ingreso=ingreso_viejo, estado=estado)

        alerta, created = self.generar()

        self.assertIsNone(alerta)
        self.assertIs(created, False)
        self.assertEqual(self.alertas().count(), 0)
        self.assertEqual(ConfiguracionCarrera.objects.count(), 0)

    def test_solo_los_reportes_de_la_practica_evaluada_son_candidatos(self):
        self.configurar()
        otra = self.crear_practica()
        self.reportar(practica=otra)

        alerta, created = self.generar()

        self.assertIsNone(alerta)
        self.assertIs(created, False)
        self.assertEqual(self.alertas().count(), 0)
        self.assertIs(self.generar(practica=otra)[1], True)


class ConfiguracionVigenteTests(AlertaRevisionFixturesMixin, TestCase):
    """La configuración se resuelve por carrera/modalidad a la fecha evaluada."""

    def setUp(self):
        self.reportar()

    def test_ignora_una_configuracion_posterior_a_la_fecha(self):
        self.configurar(plazo=10)
        self.configurar(plazo=0, desde=date(2026, 3, 5))

        # Con la vigente (10) no vence; la futura (0) sí lo haría.
        alerta, created = self.generar(fecha=date(2026, 3, 4))

        self.assertIsNone(alerta)
        self.assertIs(created, False)

    def test_gana_la_configuracion_mas_reciente(self):
        self.configurar(plazo=10)
        self.configurar(plazo=0, desde=date(2026, 3, 1))

        # Con la más reciente (0), 2 días hábiles vencen; con la anterior no.
        alerta, created = self.generar(fecha=date(2026, 3, 4))

        self.assertIs(created, True)
        self.assertIsNotNone(alerta)

    def test_del_mismo_dia_gana_la_configuracion_de_mayor_pk(self):
        self.configurar(plazo=10, desde=date(2026, 3, 2))
        self.configurar(plazo=0, desde=date(2026, 3, 2))

        # La de mayor pk (0) hace vencer el quinto día hábil.
        alerta, created = self.generar(fecha=QUINTO_DIA_HABIL)

        self.assertIs(created, True)
        self.assertIsNotNone(alerta)

    def test_otra_modalidad_u_otra_carrera_no_sirven_de_configuracion(self):
        self.configurar(modalidad=Modalidad.COMUNITARIA)
        self.configurar(carrera=self.otra_carrera)

        with self.assertRaises(ValidationError) as error:
            self.generar()

        self.assertEqual(
            error.exception.message_dict,
            {"carrera": [MENSAJE_CONFIGURACION_REVISION]},
        )
        self.assertEqual(self.alertas().count(), 0)

    def test_sin_configuracion_vigente_rechaza_sin_escribir(self):
        antes = (Alerta.objects.count(), ConfiguracionCarrera.objects.count())

        with self.assertRaises(ValidationError) as error:
            self.generar()

        self.assertEqual(MENSAJE_CONFIGURACION_REVISION, MENSAJE_CONFIGURACION_ESPERADO)
        self.assertEqual(
            error.exception.message_dict,
            {"carrera": [MENSAJE_CONFIGURACION_ESPERADO]},
        )
        self.assertEqual(
            (Alerta.objects.count(), ConfiguracionCarrera.objects.count()), antes
        )


class DeduplicacionYEscriturasTests(AlertaRevisionFixturesMixin, TestCase):
    """Una sola alerta activa por práctica, sin resolver ni reescribir nada."""

    def setUp(self):
        self.configurar()

    def test_varios_reportes_vencidos_producen_una_sola_alerta_activa(self):
        self.reportar()
        self.reportar()

        primera, created = self.generar()
        repetida, created_repetida = self.generar(fecha=FIN)

        self.assertIs(created, True)
        self.assertIs(created_repetida, False)
        assert primera is not None
        assert repetida is not None
        self.assertEqual(primera.pk, repetida.pk)
        self.assertEqual(self.alertas().count(), 1)

    def test_reejecutar_conserva_pk_y_fecha_de_la_alerta_existente(self):
        self.reportar()
        original, _ = self.generar()
        assert original is not None
        Alerta.objects.filter(pk=original.pk).update(fecha=date(2020, 1, 2))

        repetida, created = self.generar(fecha=FIN)

        self.assertIs(created, False)
        assert repetida is not None
        self.assertEqual(repetida.pk, original.pk)
        repetida.refresh_from_db()
        self.assertEqual(repetida.fecha, date(2020, 1, 2))
        self.assertIs(repetida.atendida, False)

    def test_una_alerta_atendida_no_bloquea_y_no_se_reactiva(self):
        self.reportar()
        atendida, _ = self.generar()
        assert atendida is not None
        Alerta.objects.filter(pk=atendida.pk).update(
            atendida=True, fecha=date(2020, 1, 2)
        )

        nueva, created = self.generar(fecha=FIN)

        self.assertIs(created, True)
        assert nueva is not None
        self.assertNotEqual(nueva.pk, atendida.pk)
        self.assertIs(nueva.atendida, False)
        atendida.refresh_from_db()
        self.assertIs(atendida.atendida, True)
        self.assertEqual(atendida.fecha, date(2020, 1, 2))
        self.assertEqual(self.alertas().count(), 2)

    def test_no_cierra_la_alerta_cuando_ya_no_hay_candidatas(self):
        reporte = self.reportar()
        vigente, _ = self.generar()
        assert vigente is not None
        ReporteSemanal.objects.filter(pk=reporte.pk).update(
            estado=EstadoReporte.VALIDADO
        )

        alerta, created = self.generar(fecha=FIN)

        self.assertIsNone(alerta)
        self.assertIs(created, False)
        vigente.refresh_from_db()
        self.assertIs(vigente.atendida, False)
        self.assertEqual(self.alertas().count(), 1)

    def test_generar_no_cambia_estados_ni_escribe_historial(self):
        reporte = self.reportar()
        antes_practica = (
            Practica.objects.filter(pk=self.practica.pk)
            .values("estado", "fecha_inicio_real")
            .get()
        )
        antes_reporte = (
            ReporteSemanal.objects.filter(pk=reporte.pk)
            .values(
                "estado", "ingreso_revision_en", "fecha_registro", "requiere_revision"
            )
            .get()
        )

        self.generar()

        self.assertEqual(
            Practica.objects.filter(pk=self.practica.pk)
            .values("estado", "fecha_inicio_real")
            .get(),
            antes_practica,
        )
        self.assertEqual(
            ReporteSemanal.objects.filter(pk=reporte.pk)
            .values(
                "estado", "ingreso_revision_en", "fecha_registro", "requiere_revision"
            )
            .get(),
            antes_reporte,
        )
        self.assertEqual(HistorialEstado.objects.count(), 0)
        self.assertEqual(Validacion.objects.count(), 0)

    def test_un_integrity_error_ajeno_no_se_trata_como_duplicado(self):
        self.reportar()

        with (
            mock.patch.object(
                Alerta,
                "save",
                side_effect=IntegrityError("constraint failed: otra regla"),
            ),
            self.assertRaises(IntegrityError) as error,
        ):
            self.generar()

        self.assertIn("otra regla", str(error.exception))
        self.assertEqual(Alerta.objects.count(), 0)
