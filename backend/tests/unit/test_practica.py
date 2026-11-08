"""Tests del modelo Practica (RF-14, data-model.md, T015)."""

from datetime import date

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from apps.carreras.models import Carrera, ConfiguracionCarrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import Periodo, Practica
from apps.usuarios.models import Usuario

MENSAJE_ENTIDAD_LABORAL = "La entidad receptora es obligatoria para las prácticas laborales."
MENSAJE_SUBTIPO_LABORAL = "El subtipo es obligatorio para las prácticas laborales."
MENSAJE_SUBTIPO_COMUNITARIA = "El subtipo solo aplica a las prácticas laborales."
MENSAJE_PROYECTO_COMUNITARIA = "El proyecto de vinculación es obligatorio para las prácticas comunitarias."


class PracticaFixturesMixin:
    """Carrera, entidad, período y estudiante compartidos por las pruebas."""

    @classmethod
    def setUpTestData(cls):
        cls.carrera = Carrera.objects.create(codigo="ING-SIS", nombre="Ingeniería de Sistemas")
        cls.entidad = EntidadReceptora.objects.create(nombre="Junta Parroquial de San Lucas")
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

    def datos_laboral(self, **overrides):
        datos = {
            "estudiante": self.estudiante,
            "carrera": self.carrera,
            "entidad": self.entidad,
            "periodo": self.periodo,
            "tipo": Practica.Tipo.LABORAL,
            "subtipo": Practica.Subtipo.PRACTICA,
            "horas_requeridas": 240,
        }
        datos.update(overrides)
        return datos

    def datos_comunitaria(self, **overrides):
        datos = {
            "estudiante": self.estudiante,
            "carrera": self.carrera,
            "periodo": self.periodo,
            "tipo": Practica.Tipo.COMUNITARIA,
            "proyecto_vinculacion": "Alfabetización digital para adultos mayores",
            "horas_requeridas": 96,
        }
        datos.update(overrides)
        return datos

    def guardar(self, **datos):
        practica = Practica(**datos)
        practica.full_clean()
        practica.save()
        return practica


class PracticaCamposObligatoriosTests(PracticaFixturesMixin, TestCase):
    """estudiante, carrera, período, tipo y horas_requeridas son obligatorios."""

    def test_campos_obligatorios_ausentes_se_rechazan_sin_guardar(self):
        casos = {"estudiante": None, "carrera": None, "periodo": None, "tipo": "", "horas_requeridas": None}

        for campo, valor in casos.items():
            with self.subTest(campo=campo):
                incompleta = Practica(**self.datos_laboral(**{campo: valor}))
                with self.assertRaises(ValidationError) as error:
                    incompleta.full_clean()
                self.assertIn(campo, error.exception.message_dict)
                self.assertEqual(Practica.objects.count(), 0)


class PracticaReglasPorTipoTests(PracticaFixturesMixin, TestCase):
    """La entidad y el proyecto dependen del tipo (RF-14)."""

    def test_laboral_sin_entidad_o_sin_subtipo_es_rechazada(self):
        casos = {
            "entidad": (None, MENSAJE_ENTIDAD_LABORAL),
            "subtipo": ("", MENSAJE_SUBTIPO_LABORAL),
        }

        for campo, (valor, mensaje) in casos.items():
            with self.subTest(campo=campo):
                invalida = Practica(**self.datos_laboral(**{campo: valor}))
                with self.assertRaises(ValidationError) as error:
                    invalida.full_clean()
                self.assertEqual(error.exception.message_dict[campo], [mensaje])
                self.assertEqual(Practica.objects.count(), 0)

    def test_comunitaria_sin_proyecto_o_con_subtipo_es_rechazada(self):
        casos = {
            "proyecto_vinculacion": ("", MENSAJE_PROYECTO_COMUNITARIA),
            "subtipo": (Practica.Subtipo.AYUDANTIA_DOCENCIA, MENSAJE_SUBTIPO_COMUNITARIA),
        }

        for campo, (valor, mensaje) in casos.items():
            with self.subTest(campo=campo):
                invalida = Practica(**self.datos_comunitaria(**{campo: valor}))
                with self.assertRaises(ValidationError) as error:
                    invalida.full_clean()
                self.assertEqual(error.exception.message_dict[campo], [mensaje])
                self.assertEqual(Practica.objects.count(), 0)

    def test_comunitaria_se_guarda_sin_entidad_ni_subtipo(self):
        practica = self.guardar(**self.datos_comunitaria())
        practica.refresh_from_db()

        self.assertIsNone(practica.entidad_id)
        self.assertEqual(practica.subtipo, "")
        self.assertEqual(Practica.objects.count(), 1)

    def test_laboral_se_guarda_sin_proyecto_de_vinculacion(self):
        practica = self.guardar(**self.datos_laboral())
        practica.refresh_from_db()

        self.assertEqual(practica.proyecto_vinculacion, "")
        self.assertEqual(Practica.objects.count(), 1)


class PracticaSubtiposLaboralesTests(PracticaFixturesMixin, TestCase):
    """Los cuatro subtipos de la práctica laboral son válidos (RF-14)."""

    def test_los_cuatro_subtipos_se_guardan(self):
        for subtipo in ("practica", "pasantia", "ayudantia_docencia", "ayudantia_investigacion"):
            with self.subTest(subtipo=subtipo):
                self.guardar(**self.datos_laboral(subtipo=subtipo))
                self.assertEqual(Practica.objects.filter(subtipo=subtipo).count(), 1)

        self.assertEqual(Practica.objects.count(), 4)


class PracticaEstadoYHorasTests(PracticaFixturesMixin, TestCase):
    """Estado inicial asignada, motivos vacíos y horas aportadas por quien asigna."""

    def test_estado_inicial_es_asignada_y_los_motivos_estan_vacios(self):
        practica = self.guardar(**self.datos_laboral())
        practica.refresh_from_db()

        self.assertEqual(practica.estado, "asignada")
        self.assertEqual(practica.get_estado_display(), "Asignada")
        self.assertEqual(practica.motivo_suspension, "")
        self.assertEqual(practica.motivo_cancelacion, "")

    def test_las_horas_requeridas_se_guardan(self):
        practica = self.guardar(**self.datos_laboral(horas_requeridas=240))
        practica.refresh_from_db()

        self.assertEqual(practica.horas_requeridas, 240)

    def test_actualizar_la_configuracion_no_cambia_las_horas_guardadas(self):
        configuracion = ConfiguracionCarrera.objects.create(
            carrera=self.carrera,
            modalidad=ConfiguracionCarrera.Modalidad.LABORAL,
            horas_requeridas=240,
            vigente_desde=date(2025, 3, 1),
        )
        practica = self.guardar(**self.datos_laboral(horas_requeridas=configuracion.horas_requeridas))

        configuracion.horas_requeridas = 300
        configuracion.full_clean()
        configuracion.save()
        practica.refresh_from_db()

        self.assertEqual(practica.horas_requeridas, 240)


class PracticaRestriccionEnBaseTests(PracticaFixturesMixin, TestCase):
    """Horas requeridas positivas: la base lo impone aunque no se llame full_clean()."""

    def test_cero_horas_es_rechazado_por_la_base(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Practica.objects.create(**self.datos_laboral(horas_requeridas=0))

        self.assertEqual(Practica.objects.count(), 0)

    def test_cero_horas_es_rechazado_por_full_clean(self):
        with self.assertRaises(ValidationError):
            Practica(**self.datos_laboral(horas_requeridas=0)).full_clean()


class PracticaComponentesSeparadosTests(PracticaFixturesMixin, TestCase):
    """Las prácticas laboral y comunitaria de un estudiante son filas separadas."""

    def test_laboral_y_comunitaria_conviven_para_el_mismo_estudiante(self):
        laboral = self.guardar(**self.datos_laboral())
        comunitaria = self.guardar(**self.datos_comunitaria())

        self.assertNotEqual(laboral.pk, comunitaria.pk)
        self.assertEqual(Practica.objects.filter(estudiante=self.estudiante).count(), 2)


class PracticaProteccionTests(PracticaFixturesMixin, TestCase):
    """Las referencias de la práctica no se eliminan en cascada."""

    def test_eliminar_una_referencia_es_rechazado(self):
        self.guardar(**self.datos_laboral())
        referencias = (self.carrera, self.entidad, self.periodo, self.estudiante)

        for referencia in referencias:
            with (
                self.subTest(modelo=type(referencia).__name__),
                self.assertRaises(ProtectedError),
                transaction.atomic(),
            ):
                referencia.delete()

        self.assertEqual(Practica.objects.count(), 1)
