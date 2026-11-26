"""Comando diario de generación de alertas (T044, RF-07, HU-06, CU-03).

``manage.py generar_alertas --fecha AAAA-MM-DD`` recorre las prácticas
**guardadas «en curso»** cuyo período incluye la fecha y les aplica, una por
una, los tres generadores de ``apps.alertas.services`` (rezago, revisión
vencida y reporte no enviado). La fecha es obligatoria porque los servicios no
leen el reloj: quien lo programa en cron decide el día evaluado.

El comando no reimplementa ninguna regla: cada generador resuelve su guarda, su
configuración vigente y su ``get_or_create``. Por eso dos corridas con la misma
fecha no duplican alertas, y una práctica de una carrera sin configuración
vigente se informa en el resumen sin abortar el resto del lote.
"""

from datetime import UTC, date, datetime
from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase

from apps.alertas.models import Alerta
from apps.auditoria.models import HistorialEstado
from apps.carreras.models import Carrera, ConfiguracionCarrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import Periodo, Practica
from apps.reportes.models import ReporteSemanal
from apps.usuarios.models import Usuario

FECHA = date(2026, 3, 20)
INICIO_PERIODO = date(2026, 1, 1)
FIN_PERIODO = date(2026, 7, 31)
INICIO_REAL = date(2026, 3, 2)  # lunes: la semana 1 cierra el domingo 8
INGRESO_REVISION = datetime(2026, 3, 9, 12, tzinfo=UTC)
VIGENTE = date(2025, 9, 1)
Estado = Practica.Estado
Tipo = Alerta.Tipo


def resumen(*, evaluadas, creadas, existentes, errores):
    """Salida exacta del resumen final del comando."""
    return (
        f"Prácticas en curso evaluadas: {evaluadas}\n"
        f"Alertas creadas: {creadas}\n"
        f"Alertas ya existentes: {existentes}\n"
        f"Prácticas con error de configuración: {errores}\n"
    )


class ComandoAlertasFixturesMixin:
    """Una carrera configurada, otra sin configuración y los insumos del lote."""

    carrera: Carrera
    otra_carrera: Carrera
    entidad: EntidadReceptora
    periodo: Periodo
    periodo_anterior: Periodo
    estudiante: Usuario
    otro_estudiante: Usuario
    autor: Usuario

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
        cls.periodo_anterior = Periodo.objects.create(
            nombre="2025-2",
            fecha_inicio=date(2025, 8, 1),
            fecha_fin=date(2025, 12, 31),
        )
        cls.estudiante = Usuario.objects.create_user(
            username="estudiante1",
            nombre="Ana Torres",
            email="ana@example.com",
            rol=Usuario.Rol.ESTUDIANTE,
            password=None,
        )
        cls.otro_estudiante = Usuario.objects.create_user(
            username="estudiante2",
            nombre="Beto Ruiz",
            email="beto@example.com",
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

    def configurar(self, *, carrera: Carrera | None = None) -> ConfiguracionCarrera:
        return ConfiguracionCarrera.objects.create(
            carrera=carrera or self.carrera,
            modalidad=ConfiguracionCarrera.Modalidad.LABORAL,
            horas_requeridas=240,
            plazo_reporte_dias=3,
            plazo_revision_dias=5,
            vigente_desde=VIGENTE,
        )

    def crear_practica(
        self,
        *,
        estudiante: Usuario | None = None,
        carrera: Carrera | None = None,
        periodo: Periodo | None = None,
        estado: str = Estado.EN_CURSO,
        inicio_real: date | None = None,
    ) -> Practica:
        practica = Practica(
            estudiante=estudiante or self.estudiante,
            carrera=carrera or self.carrera,
            entidad=self.entidad,
            periodo=periodo or self.periodo,
            tipo=Practica.Tipo.LABORAL,
            subtipo=Practica.Subtipo.PRACTICA,
            horas_requeridas=240,
            estado=estado,
            fecha_inicio_real=inicio_real,
        )
        practica.full_clean()
        practica.save()
        return practica

    def con_historial(self, practica: Practica) -> Practica:
        """Alta canónica del diario: sin estado anterior → asignada → en curso."""
        for anterior, nuevo in (
            (None, Estado.ASIGNADA),
            (Estado.ASIGNADA, Estado.EN_CURSO),
        ):
            registro = HistorialEstado(
                practica=practica,
                estado_anterior=anterior,
                estado_nuevo=nuevo,
                autor=self.autor,
            )
            registro.full_clean()
            registro.save()
        return practica

    def reportar_en_revision(
        self, practica: Practica, semana: int = 1
    ) -> ReporteSemanal:
        return ReporteSemanal.objects.create(
            practica=practica,
            semana=semana,
            horas_reportadas=10,
            estado=ReporteSemanal.Estado.EN_REVISION,
            ingreso_revision_en=INGRESO_REVISION,
        )

    def ejecutar(self, fecha: date | None = FECHA) -> str:
        """Corre el comando como en cron (fecha ISO en la línea de comandos)."""
        salida = StringIO()
        argumentos = [] if fecha is None else ["--fecha", fecha.isoformat()]
        call_command("generar_alertas", *argumentos, stdout=salida)
        return salida.getvalue()

    def tipos(self, practica: Practica) -> set[str]:
        return set(
            Alerta.objects.filter(practica=practica).values_list("tipo", flat=True)
        )


class GeneracionDiariaTests(ComandoAlertasFixturesMixin, TestCase):
    """Las alertas salen de los servicios; el comando solo recorre el lote."""

    def test_crea_las_alertas_esperadas_sin_tocar_las_practicas_fuera_de_alcance(
        self,
    ):
        self.configurar()
        sin_reportes = self.con_historial(
            self.crear_practica(inicio_real=INICIO_REAL, estudiante=self.estudiante)
        )
        con_revision = self.crear_practica(estudiante=self.otro_estudiante)
        self.reportar_en_revision(con_revision)
        # Fuera de alcance: una «asignada» en el período y una «en curso» fuera
        # de él. Ninguna se evalúa ni recibe alertas.
        asignada = self.crear_practica(estado=Estado.ASIGNADA)
        fuera_de_periodo = self.crear_practica(
            periodo=self.periodo_anterior, inicio_real=date(2025, 10, 1)
        )

        salida = self.ejecutar()

        self.assertEqual(
            salida, resumen(evaluadas=2, creadas=4, existentes=0, errores=0)
        )
        self.assertEqual(
            self.tipos(sin_reportes), {Tipo.REZAGO, Tipo.REPORTE_NO_ENVIADO}
        )
        self.assertEqual(
            self.tipos(con_revision), {Tipo.REZAGO, Tipo.REVISION_PENDIENTE}
        )
        self.assertEqual(self.tipos(asignada), set())
        self.assertEqual(self.tipos(fuera_de_periodo), set())
        self.assertEqual(Alerta.objects.count(), 4)

    def test_una_segunda_corrida_con_la_misma_fecha_no_duplica_alertas(self):
        self.configurar()
        practica = self.con_historial(self.crear_practica(inicio_real=INICIO_REAL))
        self.ejecutar()
        estado = list(Alerta.objects.order_by("pk").values())

        salida = self.ejecutar()

        self.assertEqual(
            salida, resumen(evaluadas=1, creadas=0, existentes=2, errores=0)
        )
        self.assertEqual(self.tipos(practica), {Tipo.REZAGO, Tipo.REPORTE_NO_ENVIADO})
        self.assertEqual(list(Alerta.objects.order_by("pk").values()), estado)

    def test_la_falta_de_configuracion_se_informa_en_el_resumen_sin_abortar(self):
        self.configurar()
        con_configuracion = self.crear_practica(estudiante=self.otro_estudiante)
        sin_configuracion = self.crear_practica(
            carrera=self.otra_carrera, inicio_real=INICIO_REAL
        )
        mensaje = (
            "No hay una configuración de carrera vigente para esa modalidad: "
            "no se puede evaluar el rezago de la práctica."
        )

        salida = self.ejecutar()

        self.assertEqual(
            salida,
            f"Práctica {sin_configuracion.pk}: {mensaje}\n"
            + resumen(evaluadas=2, creadas=1, existentes=0, errores=1),
        )
        self.assertEqual(self.tipos(con_configuracion), {Tipo.REZAGO})
        self.assertEqual(self.tipos(sin_configuracion), set())

    def test_exige_la_fecha_de_evaluacion(self):
        with self.assertRaises(CommandError):
            self.ejecutar(fecha=None)
        self.assertEqual(Alerta.objects.count(), 0)

    def test_rechaza_una_fecha_que_no_es_iso(self):
        with self.assertRaises(CommandError):
            call_command("generar_alertas", "--fecha", "20/03/2026", stdout=StringIO())
        self.assertEqual(Alerta.objects.count(), 0)
