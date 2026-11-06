"""Permisos DRF por rol y por objeto (#79, S3-S4) sobre el alcance de T019.

El rol se relee siempre de la fila guardada: el objeto del llamador no decide y
anónimo, sin fila o con fila inactiva quedan fuera. El permiso por objeto reusa
``practicas_visibles_para`` —no reimplementa el alcance de filas— y lo acota al
pk pedido, sin materializar la consulta completa.
"""

from collections.abc import Callable
from datetime import date

from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from rest_framework.permissions import BasePermission
from rest_framework.test import APIRequestFactory

from apps.carreras.models import Carrera, ConfiguracionCarrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import AsignacionTutor, Periodo, Practica
from apps.practicas.services import asignar_practica
from apps.reportes.models import ReporteSemanal
from apps.seguridad.permissions import (
    PermitirObjetoAlDueno,
    rol_guardado,
    rol_requerido,
)
from apps.usuarios.models import Usuario
from apps.usuarios.permissions import practicas_visibles_para

FABRICA = APIRequestFactory()


def peticion(usuario):
    """Petición mínima con el actor ya resuelto, como lo deja la autenticación.

    El permiso solo mira ``request.user``: sirve igual con un ``Usuario`` guardado,
    uno sin guardar (``pk`` nulo) o un ``AnonymousUser``.
    """
    solicitud = FABRICA.get("/api/v1/practicas/")
    solicitud.user = usuario
    return solicitud


class PermisosFixturesMixin:
    """Dos carreras, los seis roles y una práctica propia y otra ajena."""

    assertEqual: Callable[..., None]
    assertFalse: Callable[..., None]
    assertIn: Callable[..., None]
    assertIs: Callable[..., None]
    assertTrue: Callable[..., None]

    @classmethod
    def setUpTestData(cls):
        cls.carrera = Carrera.objects.create(
            codigo="ING-SIS", nombre="Ingeniería de Sistemas"
        )
        cls.otra_carrera = Carrera.objects.create(codigo="DER-001", nombre="Derecho")
        for carrera in (cls.carrera, cls.otra_carrera):
            ConfiguracionCarrera.objects.create(
                carrera=carrera, modalidad="laboral", horas_requeridas=240,
                vigente_desde=date(2020, 1, 1),
            )
        cls.entidad = EntidadReceptora.objects.create(
            nombre="Junta Parroquial de San Lucas"
        )
        cls.periodo = Periodo.objects.create(
            nombre="2026-1", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 7, 31)
        )
        cls.estudiante = cls.usuario("estudiante1", Usuario.Rol.ESTUDIANTE)
        cls.par = cls.usuario("estudiante2", Usuario.Rol.ESTUDIANTE)
        cls.tutor_academico = cls.usuario(
            "academico1", Usuario.Rol.TUTOR_ACADEMICO, cls.carrera
        )
        cls.tutor_entidad = cls.usuario("externo1", Usuario.Rol.TUTOR_ENTIDAD)
        cls.coordinador = cls.usuario("coordinador1", Usuario.Rol.COORDINADOR, cls.carrera)
        cls.coordinador_par = cls.usuario(
            "coordinador2", Usuario.Rol.COORDINADOR, cls.otra_carrera
        )
        cls.director = cls.usuario("director1", Usuario.Rol.DIRECTOR, cls.carrera)
        cls.secretaria = cls.usuario("secretaria1", Usuario.Rol.SECRETARIA, cls.carrera)
        cls.practica = asignar_practica(
            estudiante=cls.estudiante, carrera=cls.carrera, periodo=cls.periodo,
            tipo=Practica.Tipo.LABORAL, subtipo=str(Practica.Subtipo.PRACTICA),
            autor=cls.coordinador, entidad=cls.entidad,
            tutor_entidad=cls.tutor_entidad,
        )
        AsignacionTutor.objects.create(
            practica=cls.practica, tutor_academico=cls.tutor_academico,
            desde=date(2026, 1, 1),
        )
        cls.ajena = asignar_practica(
            estudiante=cls.par, carrera=cls.otra_carrera, periodo=cls.periodo,
            tipo=Practica.Tipo.LABORAL, subtipo=str(Practica.Subtipo.PRACTICA),
            autor=cls.coordinador_par, entidad=cls.entidad,
        )

    @classmethod
    def usuario(cls, username, rol, carrera=None):
        return Usuario.objects.create_user(
            username=username, nombre=username.title(),
            email=f"{username}@example.com", rol=rol, carrera=carrera, password=None,
        )

    def actores(self):
        return {
            Usuario.Rol.ESTUDIANTE: self.estudiante,
            Usuario.Rol.TUTOR_ACADEMICO: self.tutor_academico,
            Usuario.Rol.TUTOR_ENTIDAD: self.tutor_entidad,
            Usuario.Rol.COORDINADOR: self.coordinador,
            Usuario.Rol.DIRECTOR: self.director,
            Usuario.Rol.SECRETARIA: self.secretaria,
        }


class RolRequeridoTests(PermisosFixturesMixin, TestCase):
    """La fábrica de permisos por rol: matriz de los seis roles y fila guardada."""

    def test_cada_rol_entra_solo_donde_la_fabrica_lo_declara(self):
        permiso = rol_requerido(Usuario.Rol.ESTUDIANTE)
        for clave, actor in self.actores().items():
            with self.subTest(rol=clave):
                self.assertIs(
                    permiso().has_permission(peticion(actor), None),
                    clave == Usuario.Rol.ESTUDIANTE,
                )

    def test_la_fabrica_admite_varios_roles_y_es_una_clase_drf(self):
        permiso = rol_requerido(Usuario.Rol.COORDINADOR, Usuario.Rol.DIRECTOR)
        self.assertTrue(issubclass(permiso, BasePermission))
        self.assertEqual(permiso.__name__, "RolRequeridoCoordinadorDirector")
        for usuario in (self.coordinador, self.director):
            with self.subTest(usuario=usuario.username):
                self.assertTrue(permiso().has_permission(peticion(usuario), None))
        for usuario in (self.estudiante, self.secretaria):
            with self.subTest(usuario=usuario.username):
                self.assertFalse(permiso().has_permission(peticion(usuario), None))

    def test_anonimo_sin_fila_e_inactivo_quedan_fuera(self):
        permiso = rol_requerido(Usuario.Rol.ESTUDIANTE)
        self.assertFalse(permiso().has_permission(peticion(AnonymousUser()), None))
        self.assertFalse(
            permiso().has_permission(peticion(Usuario(username="fantasma")), None)
        )
        # Copia de la fila: la fixture de la clase no se muta entre pruebas.
        inactivo = Usuario.objects.get(pk=self.estudiante.pk)
        inactivo.is_active = False
        inactivo.save(update_fields=["is_active"])
        self.assertFalse(permiso().has_permission(peticion(inactivo), None))

    def test_un_rol_desconocido_o_vacio_en_la_fabrica_falla_cerrado(self):
        for roles in (("superusuario",), (Usuario.Rol.ESTUDIANTE, "otro"), ()):
            with self.subTest(roles=roles), self.assertRaises(ValueError):
                rol_requerido(*roles)

    def test_el_rol_se_lee_de_la_fila_guardada_y_no_del_objeto(self):
        impostor = Usuario.objects.get(pk=self.estudiante.pk)
        impostor.rol = Usuario.Rol.COORDINADOR
        permiso = rol_requerido(Usuario.Rol.COORDINADOR)
        self.assertFalse(permiso().has_permission(peticion(impostor), None))
        self.assertEqual(rol_guardado(impostor), Usuario.Rol.ESTUDIANTE)
        self.assertIsNone(rol_guardado(AnonymousUser()))
        self.assertIsNone(rol_guardado(Usuario(username="fantasma")))


class PermitirObjetoAlDuenoTests(PermisosFixturesMixin, TestCase):
    """Alcance por objeto: reusa el row-scope de T019, no lo reimplementa."""

    def test_el_alcance_por_objeto_sigue_las_filas_visibles_de_t019(self):
        permiso = PermitirObjetoAlDueno()
        casos = (
            (self.estudiante, self.practica, True),
            (self.estudiante, self.ajena, False),
            (self.tutor_academico, self.practica, True),
            (self.tutor_academico, self.ajena, False),
            (self.tutor_entidad, self.practica, True),
            (self.tutor_entidad, self.ajena, False),
            (self.coordinador, self.practica, True),
            (self.coordinador, self.ajena, False),
            (self.coordinador_par, self.practica, False),
            (self.director, self.practica, True),
            (self.secretaria, self.practica, True),
        )
        for actor, practica, esperado in casos:
            with self.subTest(actor=actor.username, practica=practica.pk):
                self.assertIs(
                    permiso.has_object_permission(peticion(actor), None, practica),
                    esperado,
                )
                self.assertIs(
                    practicas_visibles_para(actor).filter(pk=practica.pk).exists(),
                    esperado,
                )

    def test_anonimo_sin_fila_e_inactivo_no_pasan_ni_la_entrada(self):
        permiso = PermitirObjetoAlDueno()
        self.assertFalse(
            permiso.has_permission(peticion(AnonymousUser()), None)
        )
        self.assertFalse(
            permiso.has_permission(peticion(Usuario(username="fantasma")), None)
        )
        self.assertTrue(permiso.has_permission(peticion(self.estudiante), None))
        inactivo = Usuario.objects.get(pk=self.estudiante.pk)
        inactivo.is_active = False
        inactivo.save(update_fields=["is_active"])
        self.assertFalse(permiso.has_permission(peticion(inactivo), None))

    def test_anonimo_no_consulta_la_base(self):
        with self.assertNumQueries(0):
            self.assertFalse(
                PermitirObjetoAlDueno.has_object_permission(
                    PermitirObjetoAlDueno(), peticion(AnonymousUser()), None,
                    self.practica,
                )
            )

    def test_un_objeto_que_no_es_practica_queda_fuera(self):
        reporte = ReporteSemanal(practica=self.practica, semana=1, horas_reportadas=8)
        for objeto in (reporte, object(), None):
            with self.subTest(objeto=type(objeto).__name__):
                self.assertFalse(
                    PermitirObjetoAlDueno().has_object_permission(
                        peticion(self.estudiante), None, objeto
                    )
                )

    def test_el_alcance_por_objeto_no_materializa_la_consulta(self):
        with CaptureQueriesContext(connection) as consultas:
            veredicto = PermitirObjetoAlDueno().has_object_permission(
                peticion(self.coordinador), None, self.practica
            )

        self.assertTrue(veredicto)
        # Dos consultas: la fila del actor (T019) y la existencia del objeto.
        self.assertEqual(len(consultas.captured_queries), 2)
        sql_practicas = [
            consulta["sql"] for consulta in consultas.captured_queries
            if '"practicas_practica"' in consulta["sql"]
        ]
        self.assertEqual(len(sql_practicas), 1)
        self.assertIn(f'"practicas_practica"."id" = {self.practica.pk}', sql_practicas[0])
        self.assertIn("LIMIT 1", sql_practicas[0])
