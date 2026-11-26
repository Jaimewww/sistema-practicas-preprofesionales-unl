"""Generación de la alerta de reporte semanal no enviado (RF-07, T16).

``apps.alertas.services.generar_alerta_reporte_no_enviado`` evalúa **una**
práctica a una fecha inyectada. Solo cuenta la práctica guardada «en curso» y
dentro del período inclusivo, con fecha real de inicio conocida y no posterior a
la fecha evaluada, y con un historial de estados que certifique las
suspensiones (``reconstruir_suspensiones``): un historial desconocido no se
interpreta como «no hubo suspensiones».

Las semanas se eligen con ``semanas_sin_reporte_vencidas``: numeración desde el
inicio real, plazo configurado en días naturales, semanas ya enviadas —un
``devuelto`` ya se envió— y suspensión que toca la semana. Cualquier semana
elegida produce una sola alerta activa ``reporte_no_enviado`` por práctica.
"""

from collections.abc import Callable
from datetime import UTC, date, datetime
from typing import Any
from unittest import mock

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.alertas.models import Alerta
from apps.alertas.services import (
    MENSAJE_CONFIGURACION_REPORTE,
    generar_alerta_reporte_no_enviado,
)
from apps.auditoria.models import HistorialEstado
from apps.carreras.models import Carrera, ConfiguracionCarrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import Periodo, Practica
from apps.reportes.models import ReporteSemanal
from apps.usuarios.models import Usuario

INICIO_PERIODO = date(2026, 1, 1)
FIN_PERIODO = date(2026, 7, 31)
INICIO_REAL = date(2026, 3, 2)  # lunes; cierra la semana 1 el domingo 8
OPORTUNO_1 = date(2026, 3, 11)  # cierre + 3 días naturales
VENCIDO_1 = date(2026, 3, 12)
VENCIDO_3 = date(2026, 3, 26)
INICIO_ANTIGUO = date(2025, 12, 15)  # la semana 2 vence antes del período
VIGENTE = date(2025, 9, 1)
ANTES_DEL_PERIODO = date(2025, 12, 31)
DESPUES_DEL_PERIODO = date(2026, 8, 1)
Estado = Practica.Estado
EstadoReporte = ReporteSemanal.Estado
Modalidad = ConfiguracionCarrera.Modalidad
MENSAJE_CONFIGURACION_ESPERADO = (
    "No hay una configuración de carrera vigente para esa modalidad: "
    "no se puede evaluar el plazo de reporte de la práctica."
)


def momento(dia: date, hora: int = 12) -> datetime:
    """Instante UTC de referencia para fijar la fecha del historial."""
    return datetime(dia.year, dia.month, dia.day, hora, tzinfo=UTC)


class ReporteNoEnviadoFixturesMixin:
    """Carrera, período, práctica «en curso» con inicio real y un autor real."""

    carrera: Carrera
    otra_carrera: Carrera
    entidad: EntidadReceptora
    periodo: Periodo
    estudiante: Usuario
    autor: Usuario

    assertEqual: Callable[..., None]
    assertIn: Callable[..., None]
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
            nombre="2026-1", fecha_inicio=INICIO_PERIODO, fecha_fin=FIN_PERIODO
        )
        cls.estudiante = Usuario.objects.create_user(
            username="estudiante1",
            nombre="Ana Torres",
            email="ana@example.com",
            rol=Usuario.Rol.ESTUDIANTE,
            password=None,
        )
        cls.autor = Usuario.objects.create_user(
            username="coordinador1",
            nombre="Luis Paredes",
            email="coordinador@example.com",
            rol=Usuario.Rol.COORDINADOR,
            carrera=cls.carrera,
            password=None,
        )

    def crear_practica(
        self,
        *,
        inicio_real: date | None = INICIO_REAL,
        estado: str = Estado.EN_CURSO,
        carrera: Carrera | None = None,
    ) -> Practica:
        practica = Practica(
            estudiante=self.estudiante,
            carrera=carrera or self.carrera,
            entidad=self.entidad,
            periodo=self.periodo,
            tipo=Practica.Tipo.LABORAL,
            subtipo=Practica.Subtipo.PRACTICA,
            horas_requeridas=240,
            estado=estado,
            fecha_inicio_real=inicio_real,
        )
        practica.full_clean()
        practica.save()
        return practica

    def registrar(
        self,
        anterior,
        nuevo,
        *,
        cuando: datetime,
        motivo: str = "",
        practica: Practica,
    ) -> HistorialEstado:
        with mock.patch("django.utils.timezone.now", return_value=cuando):
            registro = HistorialEstado(
                practica=practica,
                estado_anterior=anterior,
                estado_nuevo=nuevo,
                motivo=motivo,
                autor=self.autor,
            )
            registro.full_clean()
            registro.save()
        return registro

    def con_historial(self, practica: Practica) -> Practica:
        """Alta canónica: sin estado anterior → asignada → en curso."""
        self.registrar(
            None, Estado.ASIGNADA, cuando=momento(INICIO_PERIODO), practica=practica
        )
        self.registrar(
            Estado.ASIGNADA,
            Estado.EN_CURSO,
            cuando=momento(INICIO_PERIODO),
            practica=practica,
        )
        return practica

    def suspender(
        self, cuando: date | datetime, *, practica: Practica, motivo="Convenio vencido."
    ) -> None:
        self.registrar(
            Estado.EN_CURSO,
            Estado.SUSPENDIDA,
            cuando=cuando if isinstance(cuando, datetime) else momento(cuando),
            motivo=motivo,
            practica=practica,
        )

    def reanudar(self, cuando: date | datetime, *, practica: Practica) -> None:
        self.registrar(
            Estado.SUSPENDIDA,
            Estado.EN_CURSO,
            cuando=cuando if isinstance(cuando, datetime) else momento(cuando),
            practica=practica,
        )

    def configurar(
        self,
        *,
        plazo: int = 3,
        desde: date = VIGENTE,
        modalidad: str = Modalidad.LABORAL,
        carrera: Carrera | None = None,
    ) -> ConfiguracionCarrera:
        return ConfiguracionCarrera.objects.create(
            carrera=carrera or self.carrera,
            modalidad=modalidad,
            horas_requeridas=240,
            plazo_reporte_dias=plazo,
            vigente_desde=desde,
        )

    def reportar(
        self,
        semana: int,
        *,
        estado: str = EstadoReporte.EN_REVISION,
        practica: Practica,
    ) -> ReporteSemanal:
        return ReporteSemanal.objects.create(
            practica=practica,
            semana=semana,
            horas_reportadas=10,
            estado=estado,
        )

    def generar(
        self, *, fecha: date = VENCIDO_1, practica: Practica
    ) -> tuple[Alerta | None, bool]:
        return generar_alerta_reporte_no_enviado(practica, fecha=fecha)

    def alertas(self, practica: Practica):
        return Alerta.objects.filter(practica=practica)


class GeneracionTests(ReporteNoEnviadoFixturesMixin, TestCase):
    """Una semana vencida sin reporte produce una sola alerta activa."""

    def test_una_semana_vencida_sin_reporte_crea_una_alerta_activa(self):
        practica = self.con_historial(self.crear_practica())
        self.configurar()

        alerta, created = self.generar(practica=practica)

        self.assertIs(created, True)
        assert alerta is not None
        alerta.refresh_from_db()
        self.assertEqual(alerta.practica_id, practica.pk)
        self.assertEqual(alerta.tipo, Alerta.Tipo.REPORTE_NO_ENVIADO)
        self.assertIs(alerta.atendida, False)
        self.assertEqual(
            list(self.alertas(practica).values_list("tipo", flat=True)),
            [Alerta.Tipo.REPORTE_NO_ENVIADO],
        )
        self.assertEqual(
            alerta.destinatarios,
            (
                Usuario.Rol.ESTUDIANTE,
                Usuario.Rol.TUTOR_ACADEMICO,
                Usuario.Rol.COORDINADOR,
            ),
        )

    def test_el_ultimo_dia_oportuno_no_alerta_y_el_dia_siguiente_si(self):
        practica = self.con_historial(self.crear_practica())
        self.configurar()

        alerta, created = self.generar(fecha=OPORTUNO_1, practica=practica)

        self.assertIsNone(alerta)
        self.assertIs(created, False)
        self.assertEqual(self.alertas(practica).count(), 0)
        self.assertIs(self.generar(practica=practica)[1], True)

    def test_varias_semanas_faltantes_producen_una_sola_alerta(self):
        practica = self.con_historial(self.crear_practica())
        self.configurar()
        original, created = self.generar(fecha=VENCIDO_3, practica=practica)
        assert original is not None
        Alerta.objects.filter(pk=original.pk).update(fecha=date(2020, 1, 2))

        repetida, created_repetida = self.generar(fecha=VENCIDO_3, practica=practica)

        self.assertIs(created, True)
        self.assertIs(created_repetida, False)
        assert repetida is not None
        self.assertEqual(repetida.pk, original.pk)
        repetida.refresh_from_db()
        self.assertEqual(repetida.fecha, date(2020, 1, 2))
        self.assertEqual(self.alertas(practica).count(), 1)

    def test_una_alerta_atendida_no_bloquea_y_no_se_reactiva(self):
        practica = self.con_historial(self.crear_practica())
        self.configurar()
        atendida, _ = self.generar(practica=practica)
        assert atendida is not None
        Alerta.objects.filter(pk=atendida.pk).update(
            atendida=True, fecha=date(2020, 1, 2)
        )

        nueva, created = self.generar(fecha=VENCIDO_3, practica=practica)

        self.assertIs(created, True)
        assert nueva is not None
        self.assertNotEqual(nueva.pk, atendida.pk)
        self.assertIs(nueva.atendida, False)
        atendida.refresh_from_db()
        self.assertIs(atendida.atendida, True)
        self.assertEqual(atendida.fecha, date(2020, 1, 2))
        self.assertEqual(self.alertas(practica).count(), 2)

    def test_no_cierra_la_alerta_cuando_ya_no_falta_ninguna_semana(self):
        practica = self.con_historial(self.crear_practica())
        self.configurar()
        vigente, _ = self.generar(practica=practica)
        self.reportar(1, practica=practica)

        alerta, created = self.generar(practica=practica)

        self.assertIsNone(alerta)
        self.assertIs(created, False)
        assert vigente is not None
        vigente.refresh_from_db()
        self.assertIs(vigente.atendida, False)
        self.assertEqual(self.alertas(practica).count(), 1)

    def test_un_reporte_devuelto_ya_fue_enviado(self):
        for estado in (
            EstadoReporte.EN_REVISION,
            EstadoReporte.VALIDADO,
            EstadoReporte.DEVUELTO,
        ):
            with self.subTest(estado=estado):
                practica = self.con_historial(self.crear_practica())
                self.configurar()
                self.reportar(1, estado=estado, practica=practica)

                alerta, created = self.generar(practica=practica)

                self.assertIsNone(alerta)
                self.assertIs(created, False)
                self.assertEqual(self.alertas(practica).count(), 0)

    def test_otra_semana_reportada_no_oculta_la_faltante(self):
        practica = self.con_historial(self.crear_practica())
        self.configurar()
        self.reportar(2, estado=EstadoReporte.DEVUELTO, practica=practica)

        alerta, created = self.generar(practica=practica)

        self.assertIs(created, True)
        self.assertIsNotNone(alerta)
        self.assertEqual(self.alertas(practica).count(), 1)

    def test_generar_no_cambia_estados_ni_escribe_historial(self):
        practica = self.con_historial(self.crear_practica())
        self.configurar()
        antes_practica = Practica.objects.filter(pk=practica.pk).values(
            "estado", "fecha_inicio_real"
        )
        antes = (list(antes_practica), HistorialEstado.objects.count())

        self.generar(practica=practica)

        self.assertEqual((list(antes_practica), HistorialEstado.objects.count()), antes)

    def test_un_integrity_error_ajeno_no_se_trata_como_duplicado(self):
        practica = self.con_historial(self.crear_practica())
        self.configurar()

        with (
            mock.patch.object(
                Alerta,
                "save",
                side_effect=IntegrityError("constraint failed: otra regla"),
            ),
            self.assertRaises(IntegrityError) as error,
        ):
            self.generar(practica=practica)

        self.assertIn("otra regla", str(error.exception))
        self.assertEqual(self.alertas(practica).count(), 0)


class GuardaDeEstadoPeriodoEInicioRealTests(ReporteNoEnviadoFixturesMixin, TestCase):
    """Fuera de la guarda no se evalúa ni se escribe, y sin inicio real no hay alerta."""

    def test_sin_fecha_inicio_real_no_alerta_ni_exige_configuracion(self):
        practica = self.con_historial(self.crear_practica(inicio_real=None))

        alerta, created = self.generar(fecha=VENCIDO_3, practica=practica)

        self.assertIsNone(alerta)
        self.assertIs(created, False)
        self.assertEqual(self.alertas(practica).count(), 0)
        self.assertEqual(ConfiguracionCarrera.objects.count(), 0)

    def test_una_fecha_anterior_al_inicio_real_no_alerta(self):
        practica = self.con_historial(self.crear_practica())

        alerta, created = self.generar(fecha=date(2026, 3, 1), practica=practica)

        self.assertIsNone(alerta)
        self.assertIs(created, False)
        self.assertEqual(self.alertas(practica).count(), 0)
        self.assertEqual(ConfiguracionCarrera.objects.count(), 0)

    def test_fuera_del_periodo_no_alerta_ni_exige_configuracion(self):
        practica = self.con_historial(self.crear_practica())
        for fecha in (ANTES_DEL_PERIODO, DESPUES_DEL_PERIODO):
            with self.subTest(fecha=fecha):
                alerta, created = self.generar(fecha=fecha, practica=practica)

                self.assertIsNone(alerta)
                self.assertIs(created, False)
        self.assertEqual(self.alertas(practica).count(), 0)
        self.assertEqual(ConfiguracionCarrera.objects.count(), 0)

    def test_los_extremos_del_periodo_cuentan_como_dentro(self):
        self.configurar()
        primera = self.con_historial(self.crear_practica(inicio_real=INICIO_ANTIGUO))
        segunda = self.con_historial(self.crear_practica(inicio_real=INICIO_ANTIGUO))

        en_inicio, created_inicio = self.generar(fecha=INICIO_PERIODO, practica=primera)
        en_fin, created_fin = self.generar(fecha=FIN_PERIODO, practica=segunda)

        self.assertIs(created_inicio, True)
        self.assertIs(created_fin, True)
        assert en_inicio is not None
        assert en_fin is not None
        self.assertEqual(en_inicio.practica_id, primera.pk)
        self.assertEqual(en_fin.practica_id, segunda.pk)

    def test_solo_se_evaluan_las_practicas_guardadas_en_curso(self):
        for estado in (
            Estado.ASIGNADA,
            Estado.EN_REVISION_FINAL,
            Estado.SUSPENDIDA,
            Estado.CANCELADA,
        ):
            with self.subTest(estado=estado):
                practica = self.con_historial(self.crear_practica())
                Practica.objects.filter(pk=practica.pk).update(estado=estado)

                alerta, created = self.generar(fecha=VENCIDO_3, practica=practica)

                self.assertIsNone(alerta)
                self.assertIs(created, False)
                self.assertEqual(self.alertas(practica).count(), 0)
        self.assertEqual(ConfiguracionCarrera.objects.count(), 0)

    def test_el_estado_guardado_manda_sobre_el_objeto_del_llamador(self):
        practica = self.con_historial(self.crear_practica())
        self.configurar()
        practica.estado = Estado.CERRADA  # solo en memoria

        self.assertIs(self.generar(practica=practica)[1], True)

        otra = self.con_historial(self.crear_practica())
        Practica.objects.filter(pk=otra.pk).update(estado=Estado.CANCELADA)
        self.assertIs(self.generar(practica=otra)[1], False)
        self.assertEqual(self.alertas(otra).count(), 0)

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
            fecha_inicio_real=INICIO_REAL,
        )

        alerta, created = self.generar(practica=sin_guardar)

        self.assertIsNone(alerta)
        self.assertIs(created, False)
        self.assertEqual(Alerta.objects.count(), 0)

    def test_sin_ninguna_semana_completa_no_exige_configuracion(self):
        practica = self.con_historial(self.crear_practica())

        alerta, created = self.generar(fecha=date(2026, 3, 7), practica=practica)

        self.assertIsNone(alerta)
        self.assertIs(created, False)
        self.assertEqual(ConfiguracionCarrera.objects.count(), 0)


class HistorialDesconocidoTests(ReporteNoEnviadoFixturesMixin, TestCase):
    """Un historial no certificado no se lee como «no hubo suspensiones»."""

    def test_un_historial_vacio_no_alerta_ni_lee_configuracion(self):
        practica = self.crear_practica()

        alerta, created = self.generar(fecha=VENCIDO_3, practica=practica)

        self.assertIsNone(alerta)
        self.assertIs(created, False)
        self.assertEqual(self.alertas(practica).count(), 0)
        self.assertEqual(ConfiguracionCarrera.objects.count(), 0)

    def test_un_historial_incoherente_no_alerta_aunque_haya_semanas_faltantes(self):
        self.configurar()
        incompleto = self.crear_practica()
        self.registrar(
            Estado.ASIGNADA,
            Estado.EN_CURSO,
            cuando=momento(INICIO_PERIODO),
            practica=incompleto,
        )
        discontinuo = self.crear_practica()
        self.con_historial(discontinuo)
        self.registrar(
            Estado.SUSPENDIDA,
            Estado.EN_CURSO,
            cuando=momento(date(2026, 3, 5)),
            practica=discontinuo,
        )

        for practica in (incompleto, discontinuo):
            with self.subTest(practica=practica.pk):
                alerta, created = self.generar(fecha=VENCIDO_3, practica=practica)

                self.assertIsNone(alerta)
                self.assertIs(created, False)
                self.assertEqual(self.alertas(practica).count(), 0)
        self.assertEqual(ConfiguracionCarrera.objects.count(), 1)


class SuspensionesTests(ReporteNoEnviadoFixturesMixin, TestCase):
    """La semana que toca una suspensión se omite; la zona configurada manda."""

    def test_una_semana_que_toca_una_suspension_no_alerta(self):
        self.configurar()
        suspendida = self.con_historial(self.crear_practica())
        self.suspender(date(2026, 3, 5), practica=suspendida)
        self.reanudar(date(2026, 3, 8), practica=suspendida)
        intacta = self.con_historial(self.crear_practica())

        alerta, created = self.generar(practica=suspendida)

        self.assertIsNone(alerta)
        self.assertIs(created, False)
        self.assertEqual(self.alertas(suspendida).count(), 0)
        self.assertIs(self.generar(practica=intacta)[1], True)

    def test_una_suspension_que_cubre_todas_las_semanas_no_alerta(self):
        practica = self.con_historial(self.crear_practica())
        self.configurar()
        self.suspender(INICIO_REAL, practica=practica)
        self.reanudar(date(2026, 3, 22), practica=practica)

        alerta, created = self.generar(fecha=VENCIDO_3, practica=practica)

        self.assertIsNone(alerta)
        self.assertIs(created, False)
        self.assertEqual(self.alertas(practica).count(), 0)

    def test_la_zona_configurada_decide_la_suspension(self):
        self.configurar()
        en_utc = self.con_historial(self.crear_practica(inicio_real=INICIO_REAL))
        con_zona = self.con_historial(self.crear_practica(inicio_real=INICIO_REAL))
        for practica in (en_utc, con_zona):
            self.suspender(datetime(2026, 3, 9, 2, 0, tzinfo=UTC), practica=practica)
            self.reanudar(datetime(2026, 3, 9, 12, 0, tzinfo=UTC), practica=practica)

        # En UTC el par es (lun 9, lun 9) y no toca la semana 1 (lun 2–dom 8).
        self.assertIs(self.generar(practica=en_utc)[1], True)
        # En UTC-5 el par es (dom 8, lun 9) y toca la semana 1: no hay alerta.
        with (
            override_settings(TIME_ZONE="America/Guayaquil"),
            timezone.override("UTC"),
        ):
            self.assertIs(self.generar(practica=con_zona)[1], False)

        self.assertEqual(self.alertas(con_zona).count(), 0)


class ConfiguracionVigenteTests(ReporteNoEnviadoFixturesMixin, TestCase):
    """El plazo sale de la configuración vigente, sin respaldo ni escritura."""

    def test_un_plazo_mayor_evita_el_vencimiento(self):
        practica = self.con_historial(self.crear_practica())
        self.configurar(plazo=10, desde=date(2025, 12, 1))

        alerta, created = self.generar(practica=practica)

        self.assertIsNone(alerta)
        self.assertIs(created, False)
        self.assertEqual(self.alertas(practica).count(), 0)

    def test_un_plazo_cero_vence_al_dia_siguiente_del_cierre(self):
        practica = self.con_historial(self.crear_practica())
        self.configurar(plazo=0, desde=date(2026, 1, 1))

        self.assertIs(self.generar(fecha=date(2026, 3, 8), practica=practica)[1], False)
        self.assertIs(self.generar(fecha=date(2026, 3, 9), practica=practica)[1], True)

    def test_ignora_una_configuracion_posterior_a_la_fecha(self):
        practica = self.con_historial(self.crear_practica())
        self.configurar(plazo=10)
        self.configurar(plazo=0, desde=date(2026, 3, 13))

        alerta, created = self.generar(practica=practica)

        self.assertIsNone(alerta)
        self.assertIs(created, False)

    def test_gana_la_configuracion_mas_reciente_y_el_mayor_pk(self):
        practica = self.con_historial(self.crear_practica())
        self.configurar(plazo=10, desde=date(2026, 1, 1))
        self.configurar(plazo=0, desde=date(2026, 1, 1))

        self.assertIs(self.generar(fecha=date(2026, 3, 9), practica=practica)[1], True)

    def test_otra_modalidad_u_otra_carrera_no_sirven_de_configuracion(self):
        practica = self.con_historial(self.crear_practica())
        self.configurar(modalidad=Modalidad.COMUNITARIA)
        self.configurar(carrera=self.otra_carrera)

        with self.assertRaises(ValidationError) as error:
            self.generar(practica=practica)

        self.assertEqual(
            error.exception.message_dict, {"carrera": [MENSAJE_CONFIGURACION_REPORTE]}
        )
        self.assertEqual(self.alertas(practica).count(), 0)

    def test_sin_configuracion_vigente_rechaza_sin_escribir(self):
        practica = self.con_historial(self.crear_practica())
        antes = (Alerta.objects.count(), ConfiguracionCarrera.objects.count())

        with self.assertRaises(ValidationError) as error:
            self.generar(practica=practica)

        self.assertEqual(MENSAJE_CONFIGURACION_REPORTE, MENSAJE_CONFIGURACION_ESPERADO)
        self.assertEqual(
            error.exception.message_dict,
            {"carrera": [MENSAJE_CONFIGURACION_ESPERADO]},
        )
        self.assertEqual(
            (Alerta.objects.count(), ConfiguracionCarrera.objects.count()), antes
        )
