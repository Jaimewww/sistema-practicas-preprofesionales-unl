"""Reconstrucción conservadora de suspensiones desde el historial (RF-07, T15).

``apps.alertas.suspensiones.reconstruir_suspensiones`` lee el
``HistorialEstado`` canónico de una práctica persistida «en curso», en orden de
``pk``, y devuelve los períodos inclusivos de suspensión reanudados. Distingue un
resultado **conocido y vacío** (historial coherente sin suspensiones) de uno
**desconocido** (historial vacío, incompleto, discontinuo, con aristas
imposibles, pares invertidos o que no coincide con el estado actual). No escribe,
no repara y no interpreta fechas fuera de la zona configurada del proyecto.
"""

from collections.abc import Callable
from datetime import UTC, date, datetime
from unittest import mock

from django.test import TestCase, override_settings
from django.utils import timezone

from apps.alertas.suspensiones import (
    SuspensionesReconstruidas,
    reconstruir_suspensiones,
)
from apps.auditoria.models import HistorialEstado
from apps.carreras.models import Carrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import Periodo, Practica
from apps.usuarios.models import Usuario

Estado = Practica.Estado
DIA_1 = date(2026, 3, 2)
DIA_2 = date(2026, 3, 12)
DIA_3 = date(2026, 4, 1)
DIA_4 = date(2026, 4, 5)


def momento(dia: date, hora: int = 12) -> datetime:
    """Instante UTC de referencia para fijar la fecha del historial en la prueba."""
    return datetime(dia.year, dia.month, dia.day, hora, tzinfo=UTC)


class SuspensionesFixturesMixin:
    """Carrera, período, práctica «en curso» y un autor real para el historial."""

    carrera: Carrera
    entidad: EntidadReceptora
    periodo: Periodo
    estudiante: Usuario
    autor: Usuario
    practica: Practica

    assertEqual: Callable[..., None]
    assertFalse: Callable[..., None]
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
        cls.practica = cls.crear_practica()

    @classmethod
    def crear_practica(cls, estado: str = Estado.EN_CURSO) -> Practica:
        practica = Practica(
            estudiante=cls.estudiante,
            carrera=cls.carrera,
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

    def registrar(
        self,
        anterior,
        nuevo,
        *,
        cuando: datetime,
        motivo: str = "",
        practica: Practica | None = None,
    ) -> HistorialEstado:
        """Inserta una fila del diario con la fecha elegida (se patchea el reloj)."""
        objetivo = practica or self.practica
        with mock.patch("django.utils.timezone.now", return_value=cuando):
            registro = HistorialEstado(
                practica=objetivo,
                estado_anterior=anterior,
                estado_nuevo=nuevo,
                motivo=motivo,
                autor=self.autor,
            )
            registro.full_clean()
            registro.save()
        return registro

    def historial_inicial(self, practica: Practica | None = None) -> None:
        """Alta canónica: sin estado anterior → asignada → en curso."""
        self.registrar(
            None, Estado.ASIGNADA, cuando=momento(date(2026, 1, 1)), practica=practica
        )
        self.registrar(
            Estado.ASIGNADA,
            Estado.EN_CURSO,
            cuando=momento(date(2026, 1, 2)),
            practica=practica,
        )

    def suspender(self, cuando: date | datetime, motivo: str = "Convenio vencido."):
        self.registrar(
            Estado.EN_CURSO,
            Estado.SUSPENDIDA,
            cuando=cuando if isinstance(cuando, datetime) else momento(cuando),
            motivo=motivo,
        )

    def reanudar(self, cuando: date | datetime):
        self.registrar(
            Estado.SUSPENDIDA,
            Estado.EN_CURSO,
            cuando=cuando if isinstance(cuando, datetime) else momento(cuando),
        )

    def situar(self, estado: str) -> None:
        """Fija el estado persistido sin pasar por el servicio (preparación)."""
        Practica.objects.filter(pk=self.practica.pk).update(estado=estado)
        self.practica.refresh_from_db()


class HistorialCoherenteTests(SuspensionesFixturesMixin, TestCase):
    """Un historial canónico produce pares inclusivos o un vacío conocido."""

    def test_sin_suspensiones_es_conocido_y_vacio(self):
        self.historial_inicial()
        self.registrar(
            Estado.EN_CURSO, Estado.EN_REVISION_FINAL, cuando=momento(date(2026, 2, 1))
        )
        self.registrar(
            Estado.EN_REVISION_FINAL,
            Estado.EN_CURSO,
            cuando=momento(date(2026, 2, 3)),
        )

        resultado = reconstruir_suspensiones(self.practica)

        self.assertEqual(
            resultado, SuspensionesReconstruidas(conocida=True, periodos=())
        )

    def test_un_par_reanudado_es_un_periodo_inclusivo(self):
        self.historial_inicial()
        self.suspender(DIA_1)
        self.reanudar(DIA_2)

        resultado = reconstruir_suspensiones(self.practica)

        self.assertTrue(resultado.conocida)
        self.assertEqual(resultado.periodos, ((DIA_1, DIA_2),))

    def test_varios_periodos_conservan_orden_y_extremos(self):
        self.historial_inicial()
        self.suspender(DIA_1, "Primera suspensión.")
        self.reanudar(DIA_2)
        self.suspender(DIA_3, "Segunda suspensión.")
        self.reanudar(DIA_4)

        resultado = reconstruir_suspensiones(self.practica)

        self.assertEqual(resultado.periodos, ((DIA_1, DIA_2), (DIA_3, DIA_4)))

    def test_suspension_y_reanudacion_el_mismo_dia_es_un_par_de_un_dia(self):
        self.historial_inicial()
        self.suspender(momento(DIA_1, hora=9), "Trámite puntual.")
        self.reanudar(momento(DIA_1, hora=15))

        resultado = reconstruir_suspensiones(self.practica)

        self.assertEqual(resultado.periodos, ((DIA_1, DIA_1),))

    def test_el_orden_es_por_pk_aunque_las_fechas_no_sean_monotonas(self):
        # El alta se insertó después que la transición a en curso: ordenar por
        # fecha rompería la cadena; el historial canónico manda por pk.
        self.registrar(None, Estado.ASIGNADA, cuando=momento(date(2026, 1, 5)))
        self.registrar(
            Estado.ASIGNADA, Estado.EN_CURSO, cuando=momento(date(2026, 1, 1))
        )
        self.suspender(DIA_1)
        self.reanudar(DIA_2)

        resultado = reconstruir_suspensiones(self.practica)

        self.assertTrue(resultado.conocida)
        self.assertEqual(resultado.periodos, ((DIA_1, DIA_2),))


class ZonaConfiguradaTests(SuspensionesFixturesMixin, TestCase):
    """Las fechas se convierten en la zona por defecto del proyecto, no en la activa."""

    def test_una_zona_activa_distinta_no_cambia_la_fecha_recuperada(self):
        self.historial_inicial()
        # Lun 9 mar 02:00 UTC = dom 8 mar 21:00 en UTC-5; la reanudación cae el
        # lunes 9. Si mandara la zona activa (UTC), el par sería 9 → 10.
        self.suspender(datetime(2026, 3, 9, 2, 0, tzinfo=UTC))
        self.reanudar(datetime(2026, 3, 10, 2, 0, tzinfo=UTC))

        with (
            override_settings(TIME_ZONE="America/Guayaquil"),
            timezone.override("UTC"),
        ):
            resultado = reconstruir_suspensiones(self.practica)

        self.assertEqual(resultado.periodos, ((date(2026, 3, 8), date(2026, 3, 9)),))


class HistorialNoConfiableTests(SuspensionesFixturesMixin, TestCase):
    """Todo historial que no certifica el resultado devuelve «desconocido»."""

    def test_practica_sin_guardar_es_desconocida(self):
        sin_pk = Practica(
            estudiante=self.estudiante,
            carrera=self.carrera,
            entidad=self.entidad,
            periodo=self.periodo,
            tipo=Practica.Tipo.LABORAL,
            subtipo=Practica.Subtipo.PRACTICA,
            horas_requeridas=240,
            estado=Estado.EN_CURSO,
        )

        self.assertFalse(reconstruir_suspensiones(sin_pk).conocida)

    def test_practica_inexistente_es_desconocida(self):
        fantasma = Practica(pk=999_999, estado=Estado.EN_CURSO)

        self.assertFalse(reconstruir_suspensiones(fantasma).conocida)

    def test_historial_vacio_es_desconocido(self):
        self.assertFalse(reconstruir_suspensiones(self.practica).conocida)

    def test_una_practica_que_no_esta_en_curso_es_desconocida(self):
        self.registrar(None, Estado.ASIGNADA, cuando=momento(date(2026, 1, 1)))
        self.situar(Estado.ASIGNADA)

        self.assertFalse(reconstruir_suspensiones(self.practica).conocida)

    def test_historial_sin_registro_inicial_es_incompleto(self):
        self.registrar(
            Estado.ASIGNADA, Estado.EN_CURSO, cuando=momento(date(2026, 1, 2))
        )

        self.assertFalse(reconstruir_suspensiones(self.practica).conocida)

    def test_cadena_discontinua_es_desconocida(self):
        self.historial_inicial()
        # El estado anterior no es el nuevo de la fila previa (en_curso).
        self.registrar(Estado.SUSPENDIDA, Estado.EN_CURSO, cuando=momento(DIA_1))

        self.assertFalse(reconstruir_suspensiones(self.practica).conocida)

    def test_arista_imposible_es_desconocida(self):
        self.registrar(None, Estado.ASIGNADA, cuando=momento(date(2026, 1, 1)))
        # asignada → suspendida no existe en la tabla canónica de transiciones.
        self.registrar(
            Estado.ASIGNADA,
            Estado.SUSPENDIDA,
            cuando=momento(DIA_1),
            motivo="No permitida.",
        )

        self.assertFalse(reconstruir_suspensiones(self.practica).conocida)

    def test_el_estado_actual_debe_coincidir_con_el_ultimo_del_historial(self):
        self.historial_inicial()
        self.registrar(Estado.EN_CURSO, Estado.EN_REVISION_FINAL, cuando=momento(DIA_1))
        # La fila persistida sigue en curso, pero el historial terminó en revisión.

        self.assertFalse(reconstruir_suspensiones(self.practica).conocida)

    def test_una_suspension_sin_reanudar_es_incompleta(self):
        self.historial_inicial()
        self.suspender(DIA_1)
        # La fila se fuerza a en curso para que el rechazo no dependa solo del
        # primer guardia: falta el cierre del par.
        self.situar(Estado.EN_CURSO)

        self.assertFalse(reconstruir_suspensiones(self.practica).conocida)

    def test_un_par_con_fechas_invertidas_es_malformado(self):
        self.historial_inicial()
        self.suspender(DIA_2)
        self.reanudar(DIA_1)

        self.assertFalse(reconstruir_suspensiones(self.practica).conocida)

    def test_no_escribe_ni_repara_el_historial(self):
        self.historial_inicial()
        self.suspender(DIA_2)
        self.reanudar(DIA_1)
        antes = list(
            HistorialEstado.objects.order_by("pk").values_list(
                "pk", "estado_anterior", "estado_nuevo", "fecha"
            )
        )

        resultado = reconstruir_suspensiones(self.practica)

        self.assertFalse(resultado.conocida)
        self.assertEqual(
            list(
                HistorialEstado.objects.order_by("pk").values_list(
                    "pk", "estado_anterior", "estado_nuevo", "fecha"
                )
            ),
            antes,
        )
        self.practica.refresh_from_db()
        self.assertEqual(self.practica.estado, Estado.EN_CURSO)
