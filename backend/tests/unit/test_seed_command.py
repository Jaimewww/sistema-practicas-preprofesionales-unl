"""Pruebas de ``manage.py seed``: datos de demo en los modelos reales (S3, #76)."""

from io import StringIO

from apps.actividades.models import PlanActividades, Validacion
from apps.auditoria.models import HistorialEstado
from apps.carreras.models import Carrera, ConfiguracionCarrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import AsignacionTutor, Periodo, Practica
from apps.prototipo import sample_data
from apps.usuarios.models import Usuario
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

CARRERAS_DEMO = (sample_data.CARRERA_COORDINADOR, *sample_data.CARRERAS_OTRAS)
ESTADO_PLAN = {
    "validado": PlanActividades.Estado.APROBADO,
    "en_revision": PlanActividades.Estado.EN_REVISION,
}
MODELOS = (
    Carrera,
    ConfiguracionCarrera,
    Periodo,
    EntidadReceptora,
    Usuario,
    Practica,
    AsignacionTutor,
    PlanActividades,
    Validacion,
    HistorialEstado,
)


def fuente():
    """Prácticas de demo de la carrera del coordinador (C1)."""
    return sample_data.practicas_de_la_carrera()


def sembrar():
    salida = StringIO()
    call_command("seed", stdout=salida)
    return salida.getvalue()


class SeedCommandTests(TestCase):
    """Una sola siembra alimenta todas las comprobaciones de mapeo."""

    @classmethod
    def setUpTestData(cls):
        cls.practicas = fuente()
        cls.resumen = sembrar()

    def buscar(self, origen):
        """La práctica real que corresponde a la de ``sample_data``."""
        return Practica.objects.get(
            estudiante__nombre=origen["estudiante"], tipo=origen["tipo"]
        )

    def test_carga_un_catalogo_por_cada_dato_del_demo(self):
        self.assertEqual(Carrera.objects.count(), len(CARRERAS_DEMO))
        self.assertEqual(
            set(Carrera.objects.values_list("nombre", flat=True)),
            {titulo.partition(" - ")[2] for titulo in CARRERAS_DEMO},
        )
        self.assertEqual(
            Carrera.objects.values_list("codigo", flat=True).distinct().count(),
            len(CARRERAS_DEMO),
        )
        configuraciones = ConfiguracionCarrera.objects.order_by("modalidad")
        self.assertEqual(
            [(fila.modalidad, fila.horas_requeridas) for fila in configuraciones],
            [("comunitaria", 96), ("laboral", 160)],
        )
        self.assertEqual(
            Periodo.objects.values_list("nombre", flat=True).get(),
            sample_data.PERIODO,
        )
        entidades = {origen["entidad"] for origen in self.practicas if origen["entidad"]}
        self.assertEqual(
            set(EntidadReceptora.objects.values_list("nombre", flat=True)), entidades
        )

    def test_crea_un_usuario_por_persona_y_ninguno_puede_entrar(self):
        estudiantes = {origen["estudiante"] for origen in self.practicas}
        tutores = {origen["tutor_academico"] for origen in self.practicas}
        tutores_entidad = {
            origen["tutor_entidad"] for origen in self.practicas if origen["tutor_entidad"]
        }

        self.assertEqual(
            set(Usuario.objects.filter(rol=Usuario.Rol.ESTUDIANTE).values_list("nombre", flat=True)),
            estudiantes,
        )
        self.assertEqual(
            set(
                Usuario.objects.filter(rol=Usuario.Rol.TUTOR_ACADEMICO)
                .values_list("nombre", flat=True)
            ),
            tutores,
        )
        self.assertEqual(
            set(
                Usuario.objects.filter(rol=Usuario.Rol.TUTOR_ENTIDAD)
                .values_list("nombre", flat=True)
            ),
            tutores_entidad,
        )
        for rol, nombre in (
            (Usuario.Rol.COORDINADOR, sample_data.COORDINADOR),
            (Usuario.Rol.DIRECTOR, sample_data.DIRECTOR),
            (Usuario.Rol.SECRETARIA, sample_data.SECRETARIA),
        ):
            self.assertTrue(Usuario.objects.filter(rol=rol, nombre=nombre).exists(), nombre)
        self.assertFalse(Usuario.objects.filter(is_superuser=True).exists())
        self.assertTrue(all(not usuario.has_usable_password() for usuario in Usuario.objects.all()))

    def test_mapea_cada_practica_con_sus_horas_y_su_alcance(self):
        self.assertEqual(Practica.objects.count(), len(self.practicas))
        for origen in self.practicas:
            practica = self.buscar(origen)
            self.assertEqual(practica.estado, origen["estado"])
            self.assertEqual(practica.horas_requeridas, origen["horas_requeridas"])
            self.assertEqual(practica.carrera.nombre, origen["carrera"].partition(" - ")[2])
            self.assertEqual(practica.periodo.nombre, origen["periodo"])
            self.assertEqual(
                practica.entidad.nombre if practica.entidad else "", origen["entidad"]
            )
            self.assertEqual(practica.subtipo or "", origen["subtipo"])
            self.assertEqual(practica.proyecto_vinculacion, origen["proyecto_vinculacion"])

    def test_cada_practica_tiene_un_tutor_academico_activo(self):
        self.assertEqual(AsignacionTutor.objects.count(), len(self.practicas))
        self.assertFalse(AsignacionTutor.objects.filter(hasta__isnull=False).exists())
        for origen in self.practicas:
            asignacion = self.buscar(origen).asignaciones_tutor.get()
            self.assertEqual(
                asignacion.tutor_academico.nombre, origen["tutor_academico"]
            )
            self.assertEqual(asignacion.desde, origen["historial"][0]["fecha"])

    def test_el_historial_recorre_los_estados_del_demo(self):
        self.assertGreaterEqual(HistorialEstado.objects.count(), len(self.practicas))
        for origen in self.practicas:
            registros = list(self.buscar(origen).historial_estados.all())
            self.assertEqual(
                [registro.estado_nuevo for registro in registros],
                [entrada["estado_nuevo"] for entrada in origen["historial"]],
            )
            self.assertEqual(registros[0].estado_anterior, None)
            self.assertEqual(registros[0].estado_nuevo, Practica.Estado.ASIGNADA)
            self.assertEqual(registros[-1].estado_nuevo, origen["estado"])

    def test_conserva_los_motivos_de_suspension_y_cancelacion(self):
        for origen in self.practicas:
            if origen["estado"] not in ("suspendida", "cancelada"):
                continue
            motivos = {
                entrada["estado_nuevo"]: entrada["motivo"]
                for entrada in origen["historial"]
            }
            practica = self.buscar(origen)
            self.assertEqual(practica.motivo_suspension, motivos["suspendida"])
            if origen["estado"] == "cancelada":
                self.assertEqual(practica.motivo_cancelacion, motivos["cancelada"])

    def test_crea_el_plan_de_cada_practica_y_su_validacion(self):
        self.assertEqual(PlanActividades.objects.count(), len(self.practicas))
        decididos = [p for p in self.practicas if p["plan"]["estado"] == "validado"]
        self.assertEqual(Validacion.objects.count(), len(decididos))
        self.assertFalse(
            Validacion.objects.exclude(decision=Validacion.Decision.APROBADO).exists()
        )
        for origen in self.practicas:
            plan = self.buscar(origen).planes_actividades.get()
            self.assertEqual(plan.version, 1)
            self.assertEqual(plan.contenido, "\n".join(origen["plan"]["actividades"]))
            self.assertEqual(plan.estado, ESTADO_PLAN[origen["plan"]["estado"]])
        for origen in decididos:
            validacion = self.buscar(origen).validaciones.get()
            self.assertEqual(validacion.plan, self.buscar(origen).planes_actividades.get())
            self.assertEqual(validacion.autor.nombre, origen["tutor_academico"])

    def test_imprime_un_resumen_de_lo_sembrado(self):
        self.assertIn("Semilla de demostración", self.resumen)
        self.assertIn(f"{len(self.practicas)} prácticas", self.resumen)
        self.assertIn(f"{Carrera.objects.count()} carreras", self.resumen)


class SeedGuardTests(TestCase):
    """La segunda ejecución se rechaza explícitamente y no escribe nada."""

    def conteos(self):
        return {modelo.__name__: modelo.objects.count() for modelo in MODELOS}

    def test_una_segunda_ejecucion_se_rechaza_sin_cambiar_los_datos(self):
        sembrar()
        antes = self.conteos()

        with self.assertRaisesMessage(CommandError, "ya están cargados"):
            call_command("seed", stdout=StringIO())

        self.assertEqual(self.conteos(), antes)


class SeedAtomicidadTests(TestCase):
    """Un fallo a media siembra no deja ninguna fila escrita (S3 todo o nada)."""

    def test_fallo_a_media_siembra_no_escribe_nada(self):
        from unittest import mock

        import apps.prototipo.management.commands.seed as seedmod

        original = seedmod.Command._plan
        llamadas = {"n": 0}

        def fallar(self, *args, **kwargs):
            llamadas["n"] += 1
            if llamadas["n"] == 100:
                raise RuntimeError("fallo simulado")
            return original(self, *args, **kwargs)

        with mock.patch.object(seedmod.Command, "_plan", fallar), \
                self.assertRaises(RuntimeError):
            call_command("seed", stdout=StringIO())

        self.assertTrue(all(modelo.objects.count() == 0 for modelo in MODELOS))
