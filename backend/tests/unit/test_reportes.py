"""Modelo del reporte semanal (S4) y el «exactamente uno» de Validacion (S7, #78).

S4: ``semana`` y ``horas_reportadas`` positivas, ``fecha_registro`` automática,
``estado`` nace ``en_revision`` y la base impone una sola versión activa por
semana. S7: ``Validacion`` gana ``reporte_id`` opcional y la ``CheckConstraint``
«exactamente uno» junto a ``plan_id``; la migración 0003 dice lo mismo que el
modelo. T8: ``ingreso_revision_en`` es interno, nullable y sin respaldo: la fila
nativa queda con el ingreso desconocido y ninguna otra transición lo inventa.
"""

import importlib
from datetime import date
from typing import cast

from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from apps.actividades.models import (
    MAX_INFORME_BYTES,
    MENSAJE_EXACTAMENTE_UNO,
    PlanActividades,
    Validacion,
    validar_archivo_informe,
)
from apps.carreras.models import Carrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import AsignacionTutor, Periodo, Practica
from apps.practicas.services import cambiar_estado_practica
from apps.reportes.models import (
    MENSAJE_HORAS,
    MENSAJE_SEMANA,
    MENSAJE_SEMANA_DUPLICADA,
    MENSAJE_TOPE_SEMANAL,
    EvidenciaReporte,
    ReporteSemanal,
    ruta_evidencia_reporte,
)
from apps.reportes.services import devolver_reporte, validar_reporte
from apps.usuarios.models import Usuario

NOMBRE_RESTRICCION = "actividades_validacion_plan_reporte_o_informe"
NOMBRE_RESTRICCION_ANTERIOR = "actividades_validacion_plan_o_reporte"
MODULO_MIGRACION = "apps.actividades.migrations.0003_validacion_reporte"
MODULO_MIGRACION_RESTRICCION = "apps.actividades.migrations.0006_informe_estudiante"
MODULO_MIGRACION_INGRESO = "apps.reportes.migrations.0003_ingreso_revision_en"
MODULO_MIGRACION_EVIDENCIAS = "apps.reportes.migrations.0004_evidencias_y_actividades"


def crear_usuario(username, rol, carrera=None):
    return Usuario.objects.create_user(
        username=username,
        nombre=username.title(),
        email=f"{username}@example.com",
        rol=rol,
        carrera=carrera,
        password=None,
    )


def campo_de(modelo, nombre):
    """Campo del modelo por nombre, declarado como ``Field``.

    ``_meta.get_field`` puede devolver una relación inversa (``ForeignObjectRel``)
    y el checker no estrecha el tipo; el ``cast`` documenta que estas pruebas
    piden campos reales —``deconstruct``, ``null``, ``blank``, ``auto_now_add``—
    y no cambia lo que la prueba comprueba.
    """
    return cast("models.Field", modelo._meta.get_field(nombre))


class ReportesFixturesMixin:
    """Un estudiante con dos prácticas laborales propias y un tutor académico."""

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
        cls.tutor = crear_usuario(
            "academico1", Usuario.Rol.TUTOR_ACADEMICO, cls.carrera
        )
        cls.practica = cls.crear_practica(240)
        cls.otra_practica = cls.crear_practica(120)

    @classmethod
    def crear_practica(cls, horas):
        practica = Practica(
            estudiante=cls.estudiante,
            carrera=cls.carrera,
            entidad=cls.entidad,
            periodo=cls.periodo,
            tipo=Practica.Tipo.LABORAL,
            subtipo=Practica.Subtipo.PRACTICA,
            horas_requeridas=horas,
        )
        practica.full_clean()
        practica.save()
        return practica

    def crear_reporte(self, **extra):
        reporte = ReporteSemanal(
            **{"practica": self.practica, "semana": 1, "horas_reportadas": 8, **extra}
        )
        reporte.full_clean()
        reporte.save()
        return reporte


class ReporteSemanalTests(ReportesFixturesMixin, TestCase):
    """Campos, reglas positivas, estado inicial y unicidad por semana (S4)."""

    def test_nace_en_revision_con_su_semana_y_sus_horas(self):
        reporte = self.crear_reporte(semana=3, horas_reportadas=12)
        guardado = ReporteSemanal.objects.get(pk=reporte.pk)
        self.assertEqual(guardado.estado, ReporteSemanal.Estado.EN_REVISION)
        self.assertEqual((guardado.semana, guardado.horas_reportadas), (3, 12))

    def test_la_semana_debe_ser_positiva(self):
        for semana in (0, -1):
            with self.subTest(semana=semana):
                reporte = ReporteSemanal(
                    practica=self.practica, semana=semana, horas_reportadas=8
                )
                with self.assertRaises(ValidationError) as error:
                    reporte.full_clean()
                self.assertIn(MENSAJE_SEMANA, str(error.exception))
                self.assertEqual(ReporteSemanal.objects.count(), 0)

    def test_las_horas_reportadas_deben_ser_positivas(self):
        for horas in (0, -1):
            with self.subTest(horas=horas):
                reporte = ReporteSemanal(
                    practica=self.practica, semana=1, horas_reportadas=horas
                )
                with self.assertRaises(ValidationError) as error:
                    reporte.full_clean()
                self.assertIn(MENSAJE_HORAS, str(error.exception))
                self.assertEqual(ReporteSemanal.objects.count(), 0)

    def test_el_vocabulario_de_estados_es_el_del_data_model(self):
        self.assertEqual(
            set(ReporteSemanal.Estado.values), {"en_revision", "validado", "devuelto"}
        )
        reporte = ReporteSemanal(
            practica=self.practica, semana=1, horas_reportadas=8, estado="aprobado"
        )
        with self.assertRaises(ValidationError) as error:
            reporte.full_clean()
        self.assertIn("estado", error.exception.message_dict)

    def test_una_sola_version_activa_por_semana_se_impone_en_la_base(self):
        self.crear_reporte()
        with self.assertRaises(ValidationError) as error:
            self.crear_reporte()
        self.assertIn(MENSAJE_SEMANA_DUPLICADA, str(error.exception))
        with transaction.atomic(), self.assertRaises(IntegrityError):
            ReporteSemanal.objects.create(
                practica=self.practica, semana=1, horas_reportadas=4
            )
        self.assertEqual(ReporteSemanal.objects.count(), 1)

    def test_la_misma_semana_en_otra_practica_se_admite(self):
        self.crear_reporte()
        self.crear_reporte(practica=self.otra_practica)
        self.assertEqual(ReporteSemanal.objects.count(), 2)

    def test_la_fecha_de_registro_es_automatica(self):
        campo = cast(
            models.DateTimeField,
            ReporteSemanal._meta.get_field("fecha_registro"),
        )
        self.assertTrue(campo.auto_now_add and not campo.editable)
        reporte = self.crear_reporte()
        self.assertLessEqual(reporte.fecha_registro, timezone.now())
        self.assertIsNotNone(ReporteSemanal.objects.get(pk=reporte.pk).fecha_registro)

    def test_el_reporte_no_inventa_contenido_ni_version(self):
        nombres = {campo.name for campo in ReporteSemanal._meta.get_fields()}
        self.assertNotIn("contenido", nombres)
        self.assertNotIn("version", nombres)
        self.assertLessEqual(
            {"practica", "semana", "horas_reportadas", "fecha_registro", "estado"},
            nombres,
        )

    def test_la_practica_con_reportes_no_se_elimina(self):
        self.crear_reporte()
        with self.assertRaises(ProtectedError):
            self.practica.delete()


class HorasYRevisionTests(ReportesFixturesMixin, TestCase):
    """Tope de 168 h por semana y ``requiere_revision`` (> 40 h, escenario S5)."""

    def test_una_semana_no_pasa_de_168_horas(self):
        self.assertEqual(self.crear_reporte(horas_reportadas=168).horas_reportadas, 168)
        with self.assertRaises(ValidationError) as error:
            self.crear_reporte(semana=2, horas_reportadas=169)
        self.assertIn(MENSAJE_TOPE_SEMANAL, str(error.exception))
        self.assertEqual(ReporteSemanal.objects.count(), 1)

    def test_requiere_revision_solo_con_mas_de_40_horas(self):
        for semana, horas, esperado in ((1, 1, False), (2, 40, False), (3, 41, True)):
            with self.subTest(horas=horas):
                reporte = self.crear_reporte(semana=semana, horas_reportadas=horas)
                self.assertIs(
                    ReporteSemanal.objects.get(pk=reporte.pk).requiere_revision,
                    esperado,
                )

    def test_requiere_revision_no_la_escribe_el_cliente_y_se_recalcula(self):
        campo = ReporteSemanal._meta.get_field("requiere_revision")
        self.assertFalse(campo.editable)
        reporte = self.crear_reporte(horas_reportadas=8)
        reporte.horas_reportadas = 50
        reporte.save(update_fields=["horas_reportadas"])
        self.assertTrue(ReporteSemanal.objects.get(pk=reporte.pk).requiere_revision)

    def test_la_migracion_marca_los_reportes_previos_de_mas_de_40_horas(self):
        from django.apps import apps

        migracion = importlib.import_module(
            "apps.reportes.migrations.0002_requiere_revision_y_tope_semanal"
        )
        alto = self.crear_reporte(semana=1, horas_reportadas=45)
        bajo = self.crear_reporte(semana=2, horas_reportadas=8)
        ReporteSemanal.objects.update(requiere_revision=False)
        migracion.marcar_reportes_existentes(apps, None)
        self.assertTrue(ReporteSemanal.objects.get(pk=alto.pk).requiere_revision)
        self.assertFalse(ReporteSemanal.objects.get(pk=bajo.pk).requiere_revision)


class IngresoRevisionEnTests(ReportesFixturesMixin, TestCase):
    """T8: el ingreso a revisión es interno, nullable y no se rellena solo."""

    def test_el_campo_es_interno_nullable_y_sin_valor_por_defecto(self):
        campo = cast(
            models.DateTimeField,
            ReporteSemanal._meta.get_field("ingreso_revision_en"),
        )
        self.assertTrue(campo.null)
        self.assertFalse(campo.editable)
        self.assertFalse(campo.has_default())

    def test_una_fila_nativa_queda_con_el_ingreso_desconocido(self):
        reporte = self.crear_reporte()
        self.assertIsNone(
            ReporteSemanal.objects.values_list("ingreso_revision_en", flat=True).get(
                pk=reporte.pk
            )
        )

    def test_las_otras_transiciones_no_inventan_el_ingreso_desconocido(self):
        """Devolver y validar no son ingresos: la fila heredada sigue en NULL."""
        AsignacionTutor.objects.create(
            practica=self.practica, tutor_academico=self.tutor, desde=date(2026, 1, 1)
        )
        # CU-01 2b (integrated in develop while this stack was open): validar,
        # devolver y reenviar exigen la práctica «en curso»; se mueve por la
        # transición de dominio antes de las dos decisiones de la prueba.
        cambiar_estado_practica(
            practica=self.practica,
            nuevo_estado=Practica.Estado.EN_CURSO,
            autor=self.tutor,
        )
        devuelto = self.crear_reporte(semana=1)
        validado = self.crear_reporte(semana=2)

        devolver_reporte(
            reporte=devuelto, autor=self.tutor, observacion="Corregir la semana 1."
        )
        validar_reporte(reporte=validado, autor=self.tutor)

        self.assertEqual(
            list(
                ReporteSemanal.objects.order_by("pk").values_list(
                    "estado", "ingreso_revision_en"
                )
            ),
            [("devuelto", None), ("validado", None)],
        )


class MigracionIngresoRevisionTests(TestCase):
    """La migración 0003 solo agrega la columna: nada de backfill ni default."""

    def migracion(self):
        return importlib.import_module(MODULO_MIGRACION_INGRESO).Migration

    def test_solo_agrega_el_campo_nullable_sin_backfill(self):
        operaciones = self.migracion().operations
        self.assertEqual(
            [type(operacion).__name__ for operacion in operaciones], ["AddField"]
        )
        agregado = operaciones[0]
        self.assertEqual(agregado.model_name, "reportesemanal")
        self.assertEqual(agregado.name, "ingreso_revision_en")
        self.assertTrue(agregado.field.null)
        self.assertFalse(agregado.field.has_default())
        campo = cast(
            models.DateTimeField,
            ReporteSemanal._meta.get_field("ingreso_revision_en"),
        )
        self.assertEqual(agregado.field.deconstruct()[1:], campo.deconstruct()[1:])

    def test_depende_de_la_migracion_anterior(self):
        self.assertEqual(
            self.migracion().dependencies,
            [("reportes", "0002_requiere_revision_y_tope_semanal")],
        )


class ActividadesTests(ReportesFixturesMixin, TestCase):
    """C-03 (D1'): ``actividades`` del reporte, texto opcional en el modelo."""

    def test_actividades_es_texto_opcional_vacio_por_defecto(self):
        campo = campo_de(ReporteSemanal, "actividades")
        self.assertIsInstance(campo, models.TextField)
        self.assertTrue(campo.blank)
        self.assertEqual(campo.default, "")
        reporte = self.crear_reporte()
        self.assertEqual(ReporteSemanal.objects.get(pk=reporte.pk).actividades, "")
        con_texto = self.crear_reporte(semana=2, actividades="Levanté requisitos.")
        self.assertEqual(
            ReporteSemanal.objects.get(pk=con_texto.pk).actividades,
            "Levanté requisitos.",
        )


class EvidenciaReporteTests(ReportesFixturesMixin, TestCase):
    """C-03 (D2, D3): el PDF privado de una versión del reporte."""

    def evidencia(self, reporte, **extra):
        datos = {
            "reporte": reporte,
            "version": 1,
            "archivo": "reportes_evidencias/practica-1/x.pdf",
            "nombre": "semana-1.pdf",
            "tamano_bytes": 12,
            **extra,
        }
        return EvidenciaReporte.objects.create(**datos)

    def test_declara_sus_campos(self):
        nombres = {
            campo.name
            for campo in EvidenciaReporte._meta.get_fields()
            if campo.concrete
        }
        self.assertEqual(
            nombres,
            {"id", "reporte", "version", "archivo", "nombre", "tamano_bytes", "subida_en"},
        )
        self.assertIsInstance(campo_de(EvidenciaReporte, "archivo"), models.FileField)
        self.assertTrue(campo_de(EvidenciaReporte, "subida_en").auto_now_add)

    def test_el_reporte_con_evidencias_no_se_elimina(self):
        reporte = self.crear_reporte()
        self.evidencia(reporte)
        self.assertEqual(list(reporte.evidencias.all().values_list("version", flat=True)), [1])
        with self.assertRaises(ProtectedError):
            reporte.delete()

    def test_la_ruta_es_unica_por_archivo_y_no_usa_el_nombre_del_cliente(self):
        reporte = self.crear_reporte()
        fila = EvidenciaReporte(reporte=reporte, version=1)
        primera = ruta_evidencia_reporte(fila, "Mi Informe.PDF")
        segunda = ruta_evidencia_reporte(fila, "Mi Informe.PDF")
        prefijo = f"reportes_evidencias/practica-{self.practica.pk}/"
        for ruta in (primera, segunda):
            self.assertTrue(ruta.startswith(prefijo))
            self.assertTrue(ruta.endswith(".pdf"))
            self.assertNotIn("Mi Informe", ruta)
        self.assertNotEqual(primera, segunda)

    def test_el_archivo_exige_pdf_de_hasta_5_mb(self):
        campo = campo_de(EvidenciaReporte, "archivo")
        self.assertIn(validar_archivo_informe, campo.validators)
        self.assertEqual(MAX_INFORME_BYTES, 5 * 1024 * 1024)


class MigracionEvidenciasTests(TestCase):
    """La migración 0004 agrega ``actividades`` y crea la evidencia (D1')."""

    def migracion(self):
        return importlib.import_module(MODULO_MIGRACION_EVIDENCIAS).Migration

    def test_declara_los_dos_campos_y_el_modelo(self):
        operaciones = self.migracion().operations
        resumen = [
            (type(operacion).__name__, getattr(operacion, "name", None))
            for operacion in operaciones
        ]
        self.assertEqual(
            sorted(resumen),
            [
                ("AddField", "actividades"),
                ("CreateModel", "EvidenciaReporte"),
            ],
        )

    def test_depende_de_la_migracion_anterior(self):
        self.assertIn(
            ("reportes", "0003_ingreso_revision_en"), self.migracion().dependencies
        )


class ValidacionExactamenteUnoTests(ReportesFixturesMixin, TestCase):
    """``plan_id`` o ``reporte_id``, exactamente uno (S7)."""

    def setUp(self):
        self.reporte = self.crear_reporte()
        self.plan = PlanActividades.objects.create(
            practica=self.practica, contenido="Actividades previstas."
        )

    def crear_validacion(self, **extra):
        return Validacion(
            practica=self.practica,
            autor=self.tutor,
            decision=Validacion.Decision.APROBADO,
            **extra,
        )

    def test_un_plan_sin_reporte_sigue_siendo_valido(self):
        validacion = self.crear_validacion(plan=self.plan)
        validacion.full_clean()
        validacion.save()
        self.assertIsNone(Validacion.objects.get().reporte_id)

    def test_un_reporte_sin_plan_es_valido(self):
        validacion = self.crear_validacion(reporte=self.reporte)
        validacion.full_clean()
        validacion.save()
        self.assertEqual(Validacion.objects.get().reporte_id, self.reporte.pk)

    def test_ni_plan_ni_reporte_se_rechaza_sin_escribir(self):
        with self.assertRaises(ValidationError) as error:
            self.crear_validacion().full_clean()
        self.assertIn(MENSAJE_EXACTAMENTE_UNO, str(error.exception))
        with transaction.atomic(), self.assertRaises(IntegrityError):
            Validacion.objects.create(
                practica=self.practica,
                autor=self.tutor,
                decision=Validacion.Decision.APROBADO,
            )
        self.assertEqual(Validacion.objects.count(), 0)

    def test_plan_y_reporte_juntos_se_rechazan_sin_escribir(self):
        with self.assertRaises(ValidationError) as error:
            self.crear_validacion(plan=self.plan, reporte=self.reporte).full_clean()
        self.assertIn(MENSAJE_EXACTAMENTE_UNO, str(error.exception))
        with transaction.atomic(), self.assertRaises(IntegrityError):
            Validacion.objects.create(
                practica=self.practica,
                autor=self.tutor,
                plan=self.plan,
                reporte=self.reporte,
                decision=Validacion.Decision.APROBADO,
            )
        self.assertEqual(Validacion.objects.count(), 0)


class MigracionValidacionReporteTests(ReportesFixturesMixin, TestCase):
    """La migración 0003 declara lo mismo que el modelo (S7)."""

    def operaciones(self):
        migracion = importlib.import_module(MODULO_MIGRACION).Migration
        return {
            type(operacion).__name__: operacion for operacion in migracion.operations
        }

    def test_agrega_el_reporte_y_deja_el_plan_opcional(self):
        operaciones = self.operaciones()
        # ``AddField``/``AlterField`` llevan el nombre en la operación, no en el campo.
        self.assertEqual(
            operaciones["AddField"].field.deconstruct()[1:],
            campo_de(Validacion, "reporte").deconstruct()[1:],
        )
        plan = campo_de(Validacion, "plan")
        self.assertTrue(plan.null and plan.blank)
        self.assertEqual(
            operaciones["AlterField"].field.deconstruct()[1:], plan.deconstruct()[1:]
        )

    def test_declara_la_restriccion_exactamente_uno(self):
        """La restricción vigente («uno de tres») la declara la migración 0006.

        0003 queda histórica: su ``actividades_validacion_plan_o_reporte`` se
        retira en 0006, así que la paridad se comprueba contra la migración que
        recrea la restricción y contra la que retira la anterior.
        """
        del_modelo = next(
            restriccion
            for restriccion in Validacion._meta.constraints
            if restriccion.name == NOMBRE_RESTRICCION
        )
        migracion = importlib.import_module(MODULO_MIGRACION_RESTRICCION).Migration
        nueva = next(
            restriccion
            for restriccion in (
                getattr(operacion, "constraint", None)
                for operacion in migracion.operations
            )
            if restriccion is not None and restriccion.name == NOMBRE_RESTRICCION
        )
        retiradas = {
            operacion.name
            for operacion in migracion.operations
            if type(operacion).__name__ == "RemoveConstraint"
        }
        self.assertEqual(nueva.deconstruct(), del_modelo.deconstruct())
        self.assertEqual(retiradas, {NOMBRE_RESTRICCION_ANTERIOR})


class ParidadDeMigracionTests(TestCase):
    """S7: la migración 0003 y el modelo Validacion no divergeen."""

    def test_deconstruccion_igual_al_estado_de_la_migración(self):
        from django.db.migrations.loader import MigrationLoader

        estado = MigrationLoader(None, ignore_no_migrations=True).project_state(
            ("actividades", "0003_validacion_reporte")
        )
        entidad = estado.models[("actividades", "validacion")]
        for nombre in ("plan", "reporte"):
            campo = entidad.get_field(nombre)
            modelo = campo_de(Validacion, nombre)
            self.assertEqual(
                (modelo.null, modelo.blank), (campo.null, campo.blank), nombre
            )
        nombres = [c.name for c in Validacion._meta.constraints]
        self.assertIn(NOMBRE_RESTRICCION, nombres)
        self.assertNotIn(NOMBRE_RESTRICCION_ANTERIOR, nombres)
