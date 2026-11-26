"""Generación de la alerta de rezago de una práctica (T043, HU-06, CU-03).

`apps.alertas.services.generar_alerta_rezago` evalúa una práctica a una fecha
inyectada: solo las prácticas guardadas «en curso» y dentro del período
inclusivo se evalúan, la configuración vigente se resuelve por carrera y
modalidad a esa fecha sin respaldo inventado, y la alerta activa de tipo
`rezago` se obtiene con `get_or_create` sobre `(practica, tipo, atendida=False)`.

## Escenario canónico

240 h requeridas en un período de 112 días inclusivos (16 semanas), al cerrar la
semana 8 (día 56): 120 h esperadas y 96 h mínimas al 80 %. Con 95 h entre
validadas y en revisión hay alerta; con 96 h o más no la hay, y un reporte
devuelto no suma en ninguno de los dos saldos.

La fecha de evaluación es un argumento; la `fecha` de la alerta la pone Django al
crear la fila y no se reescribe al reevaluar. Un error de integridad que no sea la
unicidad de la causa activa se propaga tal cual y el servicio no lo confunde con
un duplicado; como el modelo solo tiene esa unicidad como conflicto representable
(la guarda de estado impide llegar a una FK inválida), la prueba lo inyecta con
`mock` sobre `Alerta.save`, que es el camino que recorre `get_or_create`.
"""

# pyright: reportMissingImports=false, reportAttributeAccessIssue=false
from collections.abc import Callable
from datetime import date
from typing import Any
from unittest import mock

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from apps.alertas.models import Alerta
from apps.alertas.services import MENSAJE_CONFIGURACION, generar_alerta_rezago
from apps.carreras.models import Carrera, ConfiguracionCarrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import Periodo, Practica
from apps.reportes.models import ReporteSemanal
from apps.usuarios.models import Usuario

INICIO = date(2026, 1, 1)
FIN = date(2026, 4, 22)  # 112 días inclusivos: las 16 semanas del ejemplo.
SEMANA_8 = date(2026, 2, 25)  # Día 56: 120 h esperadas, 96 h mínimas al 80 %.
ANTES_DEL_PERIODO = date(2025, 12, 31)
DESPUES_DEL_PERIODO = date(2026, 4, 23)
VIGENTE = date(2025, 9, 1)
Modalidad = ConfiguracionCarrera.Modalidad
Estado = Practica.Estado
EstadoReporte = ReporteSemanal.Estado
MENSAJE_CONFIGURACION_ESPERADO = (
    "No hay una configuración de carrera vigente para esa modalidad: "
    "no se puede evaluar el rezago de la práctica."
)


class AlertaRezagoFixturesMixin:
    """Carrera, período de 16 semanas y una práctica «en curso» de 240 h."""

    carrera: Carrera
    otra_carrera: Carrera
    entidad: EntidadReceptora
    periodo: Periodo
    estudiante: Usuario
    practica: Practica

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
        horas: int = 240,
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
            horas_requeridas=horas,
            estado=estado,
        )
        practica.full_clean()
        practica.save()
        return practica

    def configurar(
        self,
        umbral: int = 80,
        desde: date = VIGENTE,
        modalidad: str = Modalidad.LABORAL,
        carrera: Carrera | None = None,
        horas: int = 240,
    ) -> ConfiguracionCarrera:
        return ConfiguracionCarrera.objects.create(
            carrera=carrera or self.carrera,
            modalidad=modalidad,
            horas_requeridas=horas,
            umbral_rezago=umbral,
            vigente_desde=desde,
        )

    def reportar(
        self,
        horas: int,
        estado: str = EstadoReporte.VALIDADO,
        practica: Practica | None = None,
    ) -> ReporteSemanal:
        objetivo = practica or self.practica
        return ReporteSemanal.objects.create(
            practica=objetivo,
            semana=ReporteSemanal.objects.filter(practica=objetivo).count() + 1,
            horas_reportadas=horas,
            estado=estado,
        )

    def generar(
        self, fecha: date = SEMANA_8, practica: Practica | None = None
    ) -> tuple[Alerta | None, bool]:
        return generar_alerta_rezago(practica or self.practica, fecha=fecha)

    def alertas(self, practica=None):
        return Alerta.objects.filter(practica=practica or self.practica)


class RezagoCanonicoTests(AlertaRezagoFixturesMixin, TestCase):
    """95 h generan la alerta y 96 h no; solo validadas y en revisión suman."""

    def test_95_horas_crean_una_alerta_activa_de_rezago(self):
        self.configurar()
        self.reportar(75, EstadoReporte.VALIDADO)
        self.reportar(20, EstadoReporte.EN_REVISION)

        alerta, created = self.generar()

        self.assertIs(created, True)
        assert alerta is not None
        alerta.refresh_from_db()
        self.assertEqual(alerta.practica_id, self.practica.pk)
        self.assertEqual(alerta.tipo, Alerta.Tipo.REZAGO)
        self.assertIs(alerta.atendida, False)
        self.assertEqual(
            list(self.alertas().values_list("tipo", flat=True)), [Alerta.Tipo.REZAGO]
        )

    def test_96_horas_no_crean_alerta(self):
        self.configurar()
        self.reportar(60, EstadoReporte.VALIDADO)
        self.reportar(36, EstadoReporte.EN_REVISION)

        alerta, created = self.generar()

        self.assertIsNone(alerta)
        self.assertIs(created, False)
        self.assertEqual(self.alertas().count(), 0)

    def test_un_reporte_devuelto_no_suma_al_rezago(self):
        self.configurar()
        self.reportar(90, EstadoReporte.VALIDADO)
        self.reportar(10, EstadoReporte.DEVUELTO)

        alerta, created = self.generar()

        self.assertIs(created, True)
        self.assertIsNotNone(alerta)

    def test_las_horas_requeridas_salen_de_la_practica_no_de_la_configuracion(self):
        self.configurar(horas=100)  # Si se usaran, 95 h no serían rezago.
        self.reportar(75, EstadoReporte.VALIDADO)
        self.reportar(20, EstadoReporte.EN_REVISION)

        _, created = self.generar()

        self.assertIs(created, True)

    def test_la_fecha_de_la_alerta_es_la_de_creacion_no_la_evaluada(self):
        self.configurar()
        self.reportar(75, EstadoReporte.VALIDADO)
        self.reportar(20, EstadoReporte.EN_REVISION)
        antes = date.today()

        alerta, _ = self.generar()

        assert alerta is not None
        alerta.refresh_from_db()
        self.assertIn(alerta.fecha, (antes, date.today()))
        self.assertNotEqual(alerta.fecha, SEMANA_8)


class GuardaDeEstadoYPeriodoTests(AlertaRezagoFixturesMixin, TestCase):
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

                alerta, created = self.generar(practica=practica)

                self.assertIsNone(alerta)
                self.assertIs(created, False)
                self.assertEqual(self.alertas(practica).count(), 0)

    def test_el_estado_guardado_manda_sobre_el_objeto_del_llamador(self):
        self.configurar()
        # En la base sigue «en curso» aunque el objeto del llamador esté obsoleto.
        self.practica.estado = Estado.CERRADA
        self.assertIs(self.generar()[1], True)

        cerrada = self.crear_practica()
        Practica.objects.filter(pk=cerrada.pk).update(estado=Estado.CANCELADA)
        self.assertIs(self.generar(practica=cerrada)[1], False)
        self.assertEqual(self.alertas(cerrada).count(), 0)

    def test_fuera_del_periodo_no_evalua_ni_necesita_configuracion(self):
        for fecha in (ANTES_DEL_PERIODO, DESPUES_DEL_PERIODO):
            with self.subTest(fecha=fecha):
                alerta, created = self.generar(fecha=fecha)

                self.assertIsNone(alerta)
                self.assertIs(created, False)
        self.assertEqual(self.alertas().count(), 0)
        self.assertEqual(ConfiguracionCarrera.objects.count(), 0)

    def test_los_extremos_del_periodo_cuentan_como_dentro(self):
        self.configurar()
        otra = self.crear_practica()

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


class ConfiguracionVigenteTests(AlertaRezagoFixturesMixin, TestCase):
    """La configuración se resuelve por carrera/modalidad a la fecha evaluada."""

    def test_usa_la_configuracion_vigente_a_la_fecha_y_ignora_la_futura(self):
        self.configurar(umbral=50, desde=date(2026, 2, 1))
        self.configurar(umbral=100, desde=date(2026, 3, 1))
        self.reportar(75, EstadoReporte.VALIDADO)
        self.reportar(20, EstadoReporte.EN_REVISION)

        alerta, created = self.generar(fecha=SEMANA_8)

        # Con el umbral del 100 % habría alerta; con la vigente (50 %), no.
        self.assertIsNone(alerta)
        self.assertIs(created, False)

    def test_antes_de_la_vigencia_usa_la_configuracion_anterior(self):
        self.configurar(umbral=80, desde=VIGENTE)
        self.configurar(umbral=50, desde=date(2026, 2, 1))
        self.reportar(20, EstadoReporte.VALIDADO)

        fecha = date(2026, 1, 15)  # 15 días: 32,14 h esperadas; 25,71 u 16,07 mínimas.
        alerta, created = self.generar(fecha=fecha)

        self.assertIs(created, True)
        self.assertIsNotNone(alerta)

    def test_del_mismo_dia_gana_la_configuracion_de_mayor_pk(self):
        self.configurar(umbral=100, desde=date(2026, 1, 1))
        self.configurar(umbral=20, desde=date(2026, 1, 1))
        self.reportar(20, EstadoReporte.VALIDADO)

        alerta, created = self.generar(fecha=date(2026, 1, 15))

        self.assertIsNone(alerta)
        self.assertIs(created, False)

    def test_otra_modalidad_u_otra_carrera_no_sirven_de_configuracion(self):
        self.configurar(modalidad=Modalidad.COMUNITARIA)
        self.configurar(carrera=self.otra_carrera)

        with self.assertRaises(ValidationError) as error:
            self.generar()

        self.assertEqual(
            error.exception.message_dict, {"carrera": [MENSAJE_CONFIGURACION]}
        )
        self.assertEqual(self.alertas().count(), 0)

    def test_sin_configuracion_vigente_rechaza_sin_escribir(self):
        self.reportar(75, EstadoReporte.VALIDADO)
        self.reportar(20, EstadoReporte.EN_REVISION)
        antes = (Alerta.objects.count(), ConfiguracionCarrera.objects.count())

        with self.assertRaises(ValidationError) as error:
            self.generar()

        self.assertEqual(MENSAJE_CONFIGURACION, MENSAJE_CONFIGURACION_ESPERADO)
        self.assertEqual(
            error.exception.message_dict, {"carrera": [MENSAJE_CONFIGURACION_ESPERADO]}
        )
        self.assertEqual(
            (Alerta.objects.count(), ConfiguracionCarrera.objects.count()), antes
        )


class IdempotenciaYHistorialTests(AlertaRezagoFixturesMixin, TestCase):
    """Reevaluar conserva la alerta activa y el historial atendido."""

    def setUp(self):
        self.configurar()

    def test_reejecutar_conserva_pk_y_fecha_de_la_alerta_existente(self):
        self.reportar(75, EstadoReporte.VALIDADO)
        self.reportar(20, EstadoReporte.EN_REVISION)
        original, _ = self.generar()
        assert original is not None
        Alerta.objects.filter(pk=original.pk).update(fecha=date(2020, 1, 2))

        repetida, created = self.generar(fecha=SEMANA_8)
        posterior, created_tarde = self.generar(fecha=FIN)

        self.assertIs(created, False)
        self.assertIs(created_tarde, False)
        assert repetida is not None
        assert posterior is not None
        self.assertEqual(repetida.pk, original.pk)
        self.assertEqual(posterior.pk, original.pk)
        self.assertEqual(self.alertas().count(), 1)
        posterior.refresh_from_db()
        self.assertEqual(posterior.fecha, date(2020, 1, 2))
        self.assertIs(posterior.atendida, False)

    def test_una_alerta_atendida_no_bloquea_y_conserva_su_historial(self):
        self.reportar(75, EstadoReporte.VALIDADO)
        self.reportar(20, EstadoReporte.EN_REVISION)
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

    def test_no_resuelve_la_alerta_cuando_ya_no_hay_rezago(self):
        self.reportar(75, EstadoReporte.VALIDADO)
        self.reportar(20, EstadoReporte.EN_REVISION)
        vigente, _ = self.generar()
        assert vigente is not None
        self.reportar(150, EstadoReporte.VALIDADO)  # 245 h: sobre las 192 mínimas.

        alerta, created = self.generar(fecha=FIN)

        self.assertIsNone(alerta)
        self.assertIs(created, False)
        vigente.refresh_from_db()
        self.assertIs(vigente.atendida, False)
        self.assertEqual(self.alertas().count(), 1)


class IntegridadTests(AlertaRezagoFixturesMixin, TestCase):
    """Un error de integridad ajeno a la causa activa se propaga sin escribirse."""

    def test_un_integrity_error_ajeno_no_se_trata_como_duplicado(self):
        self.configurar()
        self.reportar(75, EstadoReporte.VALIDADO)
        self.reportar(20, EstadoReporte.EN_REVISION)

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
