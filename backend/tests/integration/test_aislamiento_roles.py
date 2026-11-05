"""Aislamiento de roles en la consulta de prácticas (T011/T019, RF-11, S3).

El vínculo con el tutor de entidad es una FK opcional por práctica y el alcance se
aplica en la consulta, nunca después de leer las filas.
"""

from datetime import date
from unittest import mock

from apps.auditoria.models import HistorialEstado
from apps.carreras.models import Carrera, ConfiguracionCarrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import (
    MENSAJE_TUTOR_ENTIDAD_COMUNITARIA,
    MENSAJE_TUTOR_ENTIDAD_ROL,
    AsignacionTutor,
    Periodo,
    Practica,
)
from apps.practicas.services import asignar_practica
from apps.usuarios.models import Usuario
from apps.usuarios.permissions import practicas_visibles_para
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.db.models.deletion import ProtectedError
from django.test import TestCase

HOY = date(2026, 3, 10)
MENSAJE_ROL = MENSAJE_TUTOR_ENTIDAD_ROL
MENSAJE_COMUNITARIA = MENSAJE_TUTOR_ENTIDAD_COMUNITARIA


def crear_usuario(username, rol, carrera=None, **extra):
    return Usuario.objects.create_user(
        username=username, nombre=username.title(), email=f"{username}@example.com",
        rol=rol, carrera=carrera, password=None, **extra,
    )


class AislamientoFixturesMixin:
    """Dos carreras, seis roles y prácticas con y sin vínculo externo."""

    @classmethod
    def setUpTestData(cls):
        cls.carrera = Carrera.objects.create(codigo="ING-SIS", nombre="Ingeniería de Sistemas")
        cls.otra_carrera = Carrera.objects.create(codigo="DER-001", nombre="Derecho")
        cls.entidad = EntidadReceptora.objects.create(nombre="Junta Parroquial de San Lucas")
        cls.periodo = Periodo.objects.create(
            nombre="2026-1", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 7, 31)
        )
        cls.estudiante = crear_usuario("estudiante1", Usuario.Rol.ESTUDIANTE)
        cls.otro_estudiante = crear_usuario("estudiante2", Usuario.Rol.ESTUDIANTE)
        cls.tutor_externo = crear_usuario("externo1", Usuario.Rol.TUTOR_ENTIDAD)
        cls.par_externo = crear_usuario("externo2", Usuario.Rol.TUTOR_ENTIDAD)
        cls.tutor_academico = crear_usuario("academico1", Usuario.Rol.TUTOR_ACADEMICO, cls.carrera)
        cls.coordinador = crear_usuario("coordinador1", Usuario.Rol.COORDINADOR, cls.carrera)
        cls.director = crear_usuario("director1", Usuario.Rol.DIRECTOR, cls.carrera)
        cls.secretaria = crear_usuario("secretaria1", Usuario.Rol.SECRETARIA, cls.carrera)
        cls.practica = cls.crear_practica(cls.estudiante, tutor_entidad=cls.tutor_externo)
        cls.practica_par = cls.crear_practica(cls.otro_estudiante, tutor_entidad=cls.par_externo)
        cls.practica_sin_vinculo = cls.crear_practica(cls.otro_estudiante)
        cls.practica_otra_carrera = cls.crear_practica(cls.otro_estudiante, carrera=cls.otra_carrera)
        cls.practica_comunitaria = cls.crear_practica(cls.estudiante, comunitaria=True)
        cls.asignacion_activa = AsignacionTutor.objects.create(
            practica=cls.practica, tutor_academico=cls.tutor_academico, desde=date(2026, 3, 1)
        )
        cls.asignacion_cerrada = AsignacionTutor.objects.create(
            practica=cls.practica_par, tutor_academico=cls.tutor_academico,
            desde=date(2026, 1, 1), hasta=date(2026, 2, 1),
        )

    @classmethod
    def crear_practica(cls, estudiante, carrera=None, tutor_entidad=None, comunitaria=False):
        practica = Practica(
            estudiante=estudiante, carrera=carrera or cls.carrera,
            entidad=None if comunitaria else cls.entidad, periodo=cls.periodo,
            tipo=Practica.Tipo.COMUNITARIA if comunitaria else Practica.Tipo.LABORAL,
            subtipo="" if comunitaria else Practica.Subtipo.PRACTICA,
            proyecto_vinculacion="Vinculación con la comunidad" if comunitaria else "",
            horas_requeridas=240, tutor_entidad=tutor_entidad,
        )
        practica.full_clean()
        practica.save()
        return practica

    def pks_visibles(self, usuario, practicas=None):
        return set(practicas_visibles_para(usuario, practicas).values_list("pk", flat=True))

    def pks_de_la_carrera(self):
        return {
            self.practica.pk, self.practica_par.pk,
            self.practica_sin_vinculo.pk, self.practica_comunitaria.pk,
        }


class VinculoTutorEntidadTests(AislamientoFixturesMixin, TestCase):
    """La FK es opcional, PROTECT, solo laboral y solo para el rol de entidad."""

    def test_el_vinculo_es_opcional_y_cambiarlo_reemplaza_el_actual(self):
        self.assertIsNone(self.practica_sin_vinculo.tutor_entidad)
        self.assertEqual(self.practica.tutor_entidad, self.tutor_externo)
        self.practica.tutor_entidad = self.par_externo
        self.practica.full_clean()
        self.practica.save()
        self.practica.refresh_from_db()
        self.assertEqual(self.practica.tutor_entidad, self.par_externo)
        self.assertEqual(Practica.objects.count(), 5)
        self.assertEqual(Practica.objects.filter(tutor_entidad_id=self.tutor_externo.pk).count(), 0)

    def test_el_campo_restringe_las_elecciones_al_rol_de_entidad(self):
        campo = Practica._meta.get_field("tutor_entidad")
        self.assertEqual(campo.remote_field.limit_choices_to, {"rol": "tutor_entidad"})
        self.assertTrue(campo.null and campo.blank)
        self.assertIs(campo.remote_field.on_delete, __import__("django.db.models").db.models.PROTECT)

    def test_una_practica_comunitaria_rechaza_el_tutor_de_entidad(self):
        self.practica_comunitaria.tutor_entidad = self.tutor_externo
        with self.assertRaises(ValidationError) as error:
            self.practica_comunitaria.full_clean()
        self.assertEqual(error.exception.message_dict["tutor_entidad"], [MENSAJE_COMUNITARIA])
        self.practica_comunitaria.refresh_from_db()
        self.assertIsNone(self.practica_comunitaria.tutor_entidad)

    def test_el_vinculo_exige_un_usuario_con_rol_tutor_de_entidad(self):
        for usuario in (self.estudiante, self.coordinador, self.tutor_academico):
            with self.subTest(rol=usuario.rol):
                self.practica_sin_vinculo.tutor_entidad = usuario
                with self.assertRaises(ValidationError) as error:
                    self.practica_sin_vinculo.full_clean()
                self.assertEqual(error.exception.message_dict["tutor_entidad"], [MENSAJE_ROL])
        self.practica_sin_vinculo.refresh_from_db()
        self.assertIsNone(self.practica_sin_vinculo.tutor_entidad)

    def test_un_tutor_vinculado_no_se_puede_borrar(self):
        with self.assertRaises(ProtectedError):
            self.tutor_externo.delete()
        self.practica.refresh_from_db()
        self.assertEqual(self.practica.tutor_entidad, self.tutor_externo)


class AlcancePorRolTests(AislamientoFixturesMixin, TestCase):
    """Cada rol ve solo sus filas; el alcance se aplica en la consulta."""

    def test_estudiante_solo_ve_sus_practicas(self):
        self.assertEqual(
            self.pks_visibles(self.estudiante),
            {self.practica.pk, self.practica_comunitaria.pk},
        )
        self.assertEqual(
            self.pks_visibles(self.otro_estudiante),
            {self.practica_par.pk, self.practica_sin_vinculo.pk, self.practica_otra_carrera.pk},
        )

    def test_coordinador_director_y_secretaria_solo_ven_su_carrera(self):
        for usuario in (self.coordinador, self.director, self.secretaria):
            with self.subTest(rol=usuario.rol):
                self.assertEqual(self.pks_visibles(usuario), self.pks_de_la_carrera())
        sin_carrera = Usuario(
            username="sin-carrera", nombre="Sin Carrera", email="sin@example.com",
            rol=Usuario.Rol.COORDINADOR,
        )
        sin_carrera.save()
        self.assertEqual(self.pks_visibles(sin_carrera), set())

    def test_tutor_academico_solo_ve_la_asignacion_activa(self):
        self.assertEqual(self.pks_visibles(self.tutor_academico), {self.practica.pk})
        self.asignacion_activa.hasta = date(2026, 3, 5)
        self.asignacion_activa.save()
        self.assertEqual(self.pks_visibles(self.tutor_academico), set())
        otra = crear_usuario("academico2", Usuario.Rol.TUTOR_ACADEMICO, self.carrera)
        self.assertEqual(self.pks_visibles(otra), set())

    def test_dos_tutores_de_entidad_de_la_misma_entidad_no_comparten_practicas(self):
        self.assertEqual(self.pks_visibles(self.tutor_externo), {self.practica.pk})
        self.assertEqual(self.pks_visibles(self.par_externo), {self.practica_par.pk})
        self.practica.tutor_entidad = self.par_externo
        self.practica.full_clean()
        self.practica.save()
        self.assertEqual(self.pks_visibles(self.tutor_externo), set())
        self.assertEqual(self.pks_visibles(self.par_externo), {self.practica.pk, self.practica_par.pk})

    def test_un_vinculo_ausente_o_comunitario_no_filtra_nada(self):
        visibles = self.pks_visibles(self.tutor_externo)
        self.assertNotIn(self.practica_sin_vinculo.pk, visibles)
        self.assertNotIn(self.practica_comunitaria.pk, visibles)
        self.assertNotIn(self.practica_otra_carrera.pk, visibles)

    def test_anonimo_sin_guardar_borrado_inactivo_y_rol_desconocido_no_ven_nada(self):
        sin_guardar = Usuario(
            username="fantasma", nombre="Fantasma", email="fantasma@example.com",
            rol=Usuario.Rol.COORDINADOR, carrera=self.carrera,
        )
        for usuario in (None, AnonymousUser(), sin_guardar,
                        Usuario(username="inventado", email="x@example.com")):
            with self.subTest(usuario=usuario):
                self.assertEqual(self.pks_visibles(usuario), set())
        borrado = crear_usuario("coordinador2", Usuario.Rol.COORDINADOR, self.otra_carrera)
        self.assertEqual(self.pks_visibles(borrado), {self.practica_otra_carrera.pk})
        Usuario.objects.filter(pk=borrado.pk).delete()
        self.assertEqual(self.pks_visibles(borrado), set())
        Usuario.objects.filter(pk=self.estudiante.pk).update(is_active=False)
        self.assertEqual(self.pks_visibles(self.estudiante), set())
        Usuario.objects.filter(pk=self.par_externo.pk).update(rol="visitante")
        self.assertEqual(self.pks_visibles(self.par_externo), set())

    def test_el_staff_o_superusuario_no_evita_el_filtro(self):
        Usuario.objects.filter(pk=self.tutor_externo.pk).update(is_staff=True, is_superuser=True)
        self.tutor_externo.refresh_from_db()
        self.assertEqual(self.pks_visibles(self.tutor_externo), {self.practica.pk})

    def test_prevalecen_el_rol_y_la_carrera_guardados_sobre_el_objeto_del_llamador(self):
        self.coordinador.rol = Usuario.Rol.COORDINADOR
        Usuario.objects.filter(pk=self.coordinador.pk).update(rol=Usuario.Rol.ESTUDIANTE)
        self.assertEqual(self.visibles_tras_cambio(self.coordinador), set())
        Usuario.objects.filter(pk=self.coordinador.pk).update(
            rol=Usuario.Rol.COORDINADOR, carrera=self.otra_carrera
        )
        self.coordinador.rol = Usuario.Rol.TUTOR_ENTIDAD
        self.coordinador.carrera = self.carrera
        self.assertEqual(
            self.visibles_tras_cambio(self.coordinador), {self.practica_otra_carrera.pk}
        )

    def visibles_tras_cambio(self, usuario):
        """El objeto del llamador conserva valores viejos; gana la fila guardada."""
        return self.pks_visibles(usuario)

    def test_la_restriccion_y_el_orden_del_conjunto_entregado_se_conservan(self):
        self.assertIsInstance(practicas_visibles_para(self.coordinador), QuerySet)
        seleccion = Practica.objects.exclude(pk=self.practica_sin_vinculo.pk).order_by("-pk")
        esperado = [
            pk for pk in seleccion.values_list("pk", flat=True)
            if pk in (self.pks_de_la_carrera() - {self.practica_sin_vinculo.pk})
        ]
        self.assertEqual(self.pks_visibles(self.coordinador, seleccion), set(esperado))
        consulta = practicas_visibles_para(self.coordinador, seleccion)
        self.assertEqual(list(consulta.values_list("pk", flat=True)), esperado)
        ajeno = Practica.objects.filter(pk=self.practica_otra_carrera.pk)
        self.assertEqual(list(practicas_visibles_para(self.coordinador, ajeno)), [])
        self.assertEqual(list(practicas_visibles_para(self.coordinador, Practica.objects.none())), [])


class AsignacionConTutorEntidadTests(AislamientoFixturesMixin, TestCase):
    """T018 acepta el vínculo externo opcional sin cambiar sus otros contratos."""

    def setUp(self):
        ConfiguracionCarrera.objects.create(
            carrera=self.carrera, modalidad=ConfiguracionCarrera.Modalidad.LABORAL,
            horas_requeridas=240, vigente_desde=HOY,
        )

    def asignar(self, **overrides):
        datos = {
            "estudiante": self.estudiante, "carrera": self.carrera, "periodo": self.periodo,
            "tipo": Practica.Tipo.LABORAL, "entidad": self.entidad,
            "subtipo": Practica.Subtipo.PRACTICA, "autor": self.coordinador,
        }
        datos.update(overrides)
        with mock.patch("django.utils.timezone.localdate", return_value=HOY):
            return asignar_practica(**datos)

    def test_la_asignacion_guarda_el_tutor_externo_opcional(self):
        con_tutor = self.asignar(tutor_entidad=self.tutor_externo)
        self.assertEqual((con_tutor.tutor_entidad, con_tutor.horas_requeridas), (self.tutor_externo, 240))
        self.assertEqual(con_tutor.estado, Practica.Estado.ASIGNADA)
        sin_tutor = self.asignar()
        self.assertIsNone(sin_tutor.tutor_entidad)
        self.assertEqual(HistorialEstado.objects.filter(practica=sin_tutor).count(), 1)

    def test_rechaza_un_tutor_de_entidad_invalido_sin_escribir(self):
        casos = {
            "rol ajeno": ({"tutor_entidad": self.estudiante}, [MENSAJE_ROL]),
            "comunitaria": (
                {
                    "tipo": Practica.Tipo.COMUNITARIA, "entidad": None, "subtipo": "",
                    "proyecto_vinculacion": "Vinculación", "tutor_entidad": self.tutor_externo,
                },
                [MENSAJE_COMUNITARIA],
            ),
        }
        for nombre, (overrides, mensajes) in casos.items():
            with self.subTest(caso=nombre):
                antes = (Practica.objects.count(), HistorialEstado.objects.count())
                with self.assertRaises(ValidationError) as error:
                    self.asignar(**overrides)
                self.assertEqual(error.exception.message_dict["tutor_entidad"], mensajes)
                self.assertEqual(
                    (Practica.objects.count(), HistorialEstado.objects.count()), antes
                )
    def test_un_vinculo_comunitario_forzado_por_orm_no_filtra_al_tutor(self):
        """Solo el ORM puede romper la regla comunitaria; el alcance no revela la práctica."""
        Practica.objects.filter(pk=self.practica_comunitaria.pk).update(
            tutor_entidad=self.tutor_externo
        )
        self.assertNotIn(
            self.practica_comunitaria.pk, self.pks_visibles(self.tutor_externo)
        )

    def test_el_alcance_se_aplica_en_la_consulta_no_despues(self):
        consulta = practicas_visibles_para(self.coordinador)
        self.assertIsNone(consulta._result_cache)
        self.assertIn('"carrera_id"', str(consulta.query))
        externa = practicas_visibles_para(self.tutor_externo)
        self.assertIn('"tutor_entidad_id"', str(externa.query))
        self.assertIn('"tipo"', str(externa.query))
