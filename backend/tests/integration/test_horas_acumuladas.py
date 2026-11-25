# pyright: reportMissingImports=false, reportAttributeAccessIssue=false
"""Horas acumuladas de una práctica (HU-04, #126).

``GET /api/v1/practicas/{id}/horas/`` proyecta lo que ya está guardado: las horas
``validadas`` suman solo los reportes en «validado», las ``en_revision`` solo los
que están «en revisión», y los «devueltos» no cuentan en ninguna de las dos. Las
``requeridas`` salen de la práctica, las ``faltantes`` nunca son negativas y
``semana_en_revision`` señala que algún reporte no devuelto superó las 40 h.

La lectura conserva el alcance de filas de T019 completo: el estudiante solo su
práctica, el coordinador/director/secretaría las de su carrera, el tutor
académico las asignadas activas y el tutor de entidad las laborales con su FK.
Una práctica ajena responde el mismo 404 que una inexistente (sin oráculo) y un
GET no escribe nada.
"""

from collections.abc import Callable
from datetime import date

import yaml
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.actividades.models import PlanActividades, Validacion
from apps.auditoria.models import HistorialEstado
from apps.carreras.models import Carrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import AsignacionTutor, Periodo, Practica
from apps.reportes.models import UMBRAL_REVISION_HORAS, ReporteSemanal
from apps.reportes.services import horas_practica
from apps.usuarios.models import Usuario

HORAS = "/api/v1/practicas/{}/horas/"
CAMPOS = {
    "horas_validadas",
    "horas_en_revision",
    "horas_requeridas",
    "horas_faltantes",
    "semana_en_revision",
}
MODELOS = (
    Usuario,
    Carrera,
    Periodo,
    EntidadReceptora,
    Practica,
    AsignacionTutor,
    HistorialEstado,
    ReporteSemanal,
    PlanActividades,
    Validacion,
)


def crear_usuario(username, rol, carrera=None):
    return Usuario.objects.create_user(
        username=username,
        nombre=username.title(),
        email=f"{username}@example.com",
        rol=rol,
        carrera=carrera,
        password=None,
    )


class HorasAcumuladasFixturesMixin:
    """Dos prácticas asignadas al tutor, una ajena y los seis roles del MVP."""

    assertEqual: Callable[..., None]
    assertIs: Callable[..., None]

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
            nombre="2026-1", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 7, 31)
        )
        cls.estudiante = crear_usuario("estudiante1", Usuario.Rol.ESTUDIANTE)
        cls.par = crear_usuario("estudiante2", Usuario.Rol.ESTUDIANTE)
        cls.ajeno = crear_usuario("estudiante3", Usuario.Rol.ESTUDIANTE)
        cls.tutor = crear_usuario(
            "academico1", Usuario.Rol.TUTOR_ACADEMICO, cls.carrera
        )
        cls.otro_tutor = crear_usuario(
            "academico2", Usuario.Rol.TUTOR_ACADEMICO, cls.carrera
        )
        cls.coordinador = crear_usuario(
            "coordinador1", Usuario.Rol.COORDINADOR, cls.carrera
        )
        cls.coordinador_par = crear_usuario(
            "coordinador2", Usuario.Rol.COORDINADOR, cls.otra_carrera
        )
        cls.director = crear_usuario("director1", Usuario.Rol.DIRECTOR, cls.carrera)
        cls.secretaria = crear_usuario(
            "secretaria1", Usuario.Rol.SECRETARIA, cls.carrera
        )
        cls.externo = crear_usuario("externo1", Usuario.Rol.TUTOR_ENTIDAD)
        cls.practica = cls.crear_practica(
            cls.estudiante, horas=120, tutor_entidad=cls.externo
        )
        cls.practica_par = cls.crear_practica(cls.par, horas=80)
        cls.ajena = cls.crear_practica(cls.ajeno, carrera=cls.otra_carrera, horas=60)
        for practica in (cls.practica, cls.practica_par):
            AsignacionTutor.objects.create(
                practica=practica,
                tutor_academico=cls.tutor,
                desde=date(2026, 1, 1),
            )
        AsignacionTutor.objects.create(
            practica=cls.practica,
            tutor_academico=cls.otro_tutor,
            desde=date(2025, 1, 1),
            hasta=date(2025, 12, 31),
        )
        for practica in (cls.practica, cls.practica_par, cls.ajena):
            PlanActividades.objects.create(
                practica=practica,
                version=1,
                contenido="Actividades previstas para la práctica.",
                estado=PlanActividades.Estado.APROBADO,
            )

    @classmethod
    def crear_practica(cls, estudiante, carrera=None, horas=240, tutor_entidad=None):
        practica = Practica(
            estudiante=estudiante,
            carrera=carrera or cls.carrera,
            entidad=cls.entidad,
            periodo=cls.periodo,
            tipo=Practica.Tipo.LABORAL,
            subtipo=Practica.Subtipo.PRACTICA,
            tutor_entidad=tutor_entidad,
            horas_requeridas=horas,
            estado=Practica.Estado.EN_CURSO,
        )
        practica.full_clean()
        practica.save()
        return practica

    def crear_reporte(
        self,
        practica=None,
        semana=1,
        horas=8,
        estado=ReporteSemanal.Estado.EN_REVISION,
    ):
        return ReporteSemanal.objects.create(
            practica=practica or self.practica,
            semana=semana,
            horas_reportadas=horas,
            estado=estado,
        )

    def cliente(self, usuario=None):
        cliente = APIClient()
        if usuario is not None:
            cliente.force_authenticate(user=usuario)
        return cliente

    def get(self, usuario, practica=None):
        objetivo = self.practica if practica is None else practica
        pk = objetivo.pk if isinstance(objetivo, Practica) else objetivo
        return self.cliente(usuario).get(HORAS.format(pk))

    def assertExito(self, respuesta, estado=200):
        self.assertEqual(respuesta.status_code, estado)
        cuerpo = respuesta.json()
        self.assertIs(cuerpo["success"], True)
        self.assertEqual(cuerpo["message"], "Operación exitosa.")
        self.assertEqual(cuerpo["errors"], None)
        self.assertEqual(cuerpo["meta"], {})
        return cuerpo["data"]

    def assertRechazo(self, respuesta, estado, mensaje, errores):
        self.assertEqual(respuesta.status_code, estado)
        self.assertEqual(
            respuesta.json(),
            {
                "success": False,
                "message": mensaje,
                "data": None,
                "errors": errores,
                "meta": {},
            },
        )

    def fotografia(self):
        """Conteos por modelo y estado de cada reporte: un GET no debe cambiarlos."""
        conteos = {modelo.__name__: modelo.objects.count() for modelo in MODELOS}
        reportes = tuple(
            ReporteSemanal.objects.order_by("pk").values_list(
                "pk",
                "estado",
                "horas_reportadas",
                "requiere_revision",
                "fecha_registro",
            )
        )
        return conteos, reportes


class HorasAcumuladasCalculoTests(HorasAcumuladasFixturesMixin, TestCase):
    """La fórmula suma solo lo que el estado permite y nunca resta horas."""

    def test_suma_validadas_y_en_revision_y_descarta_las_devueltas(self):
        self.crear_reporte(semana=1, horas=12, estado=ReporteSemanal.Estado.VALIDADO)
        self.crear_reporte(semana=2, horas=8, estado=ReporteSemanal.Estado.VALIDADO)
        self.crear_reporte(semana=3, horas=5, estado=ReporteSemanal.Estado.EN_REVISION)
        self.crear_reporte(semana=4, horas=3, estado=ReporteSemanal.Estado.EN_REVISION)
        self.crear_reporte(semana=5, horas=50, estado=ReporteSemanal.Estado.DEVUELTO)

        data = self.assertExito(self.get(self.estudiante))

        self.assertEqual(
            data,
            {
                "horas_validadas": 20,
                "horas_en_revision": 8,
                "horas_requeridas": 120,
                "horas_faltantes": 100,
                "semana_en_revision": False,
            },
        )
        self.assertEqual(set(data), CAMPOS)

    def test_las_horas_requeridas_salen_de_la_practica(self):
        self.practica.horas_requeridas = 77
        self.practica.save(update_fields=["horas_requeridas"])

        data = self.assertExito(self.get(self.estudiante))

        self.assertEqual(data["horas_requeridas"], 77)
        self.assertEqual(data["horas_faltantes"], 77)

    def test_las_horas_faltantes_nunca_son_negativas(self):
        practica = self.crear_practica(self.par, horas=10)
        self.crear_reporte(
            practica=practica,
            semana=1,
            horas=7,
            estado=ReporteSemanal.Estado.VALIDADO,
        )
        self.crear_reporte(
            practica=practica,
            semana=2,
            horas=5,
            estado=ReporteSemanal.Estado.VALIDADO,
        )

        data = horas_practica(practica)

        self.assertEqual(data["horas_validadas"], 12)
        self.assertEqual(data["horas_requeridas"], 10)
        self.assertEqual(data["horas_faltantes"], 0)

    def test_una_practica_sin_reportes_esta_en_cero(self):
        data = self.assertExito(self.get(self.estudiante))

        self.assertEqual(
            data,
            {
                "horas_validadas": 0,
                "horas_en_revision": 0,
                "horas_requeridas": 120,
                "horas_faltantes": 120,
                "semana_en_revision": False,
            },
        )

    def test_la_senal_aparece_solo_si_un_reporte_supera_las_40_horas(self):
        practica = self.crear_practica(self.par, horas=240)
        self.crear_reporte(practica=practica, semana=1, horas=UMBRAL_REVISION_HORAS)
        self.assertIs(horas_practica(practica)["semana_en_revision"], False)

        self.crear_reporte(
            practica=practica,
            semana=2,
            horas=UMBRAL_REVISION_HORAS + 1,
            estado=ReporteSemanal.Estado.VALIDADO,
        )
        self.assertIs(horas_practica(practica)["semana_en_revision"], True)

    def test_un_reporte_devuelto_de_mas_de_40_horas_no_deja_la_senal(self):
        practica = self.crear_practica(self.par, horas=240)
        self.crear_reporte(
            practica=practica,
            semana=1,
            horas=UMBRAL_REVISION_HORAS + 1,
            estado=ReporteSemanal.Estado.DEVUELTO,
        )

        self.assertIs(horas_practica(practica)["semana_en_revision"], False)


class HorasAcumuladasEndpointTests(HorasAcumuladasFixturesMixin, TestCase):
    """El endpoint conserva el alcance de filas de T019 y no escribe."""

    def test_el_estudiante_ve_su_propia_practica_con_el_envelope(self):
        data = self.assertExito(self.get(self.estudiante))
        self.assertEqual(set(data), CAMPOS)
        self.assertEqual(data["horas_requeridas"], 120)

    def test_anonimo_e_inactivo_reciben_401_sin_escribir(self):
        inactivo = crear_usuario("inactivo1", Usuario.Rol.ESTUDIANTE)
        Usuario.objects.filter(pk=inactivo.pk).update(is_active=False)
        antes = self.fotografia()

        for actor in (None, inactivo, Usuario(username="fantasma")):
            with self.subTest(actor=getattr(actor, "username", "anonimo")):
                respuesta = self.get(actor)
                self.assertRechazo(
                    respuesta,
                    401,
                    "Autenticación requerida.",
                    {"detail": "Se requiere autenticación.", "code": "no_autenticado"},
                )

        self.assertEqual(self.fotografia(), antes)

    def test_la_practica_ajena_y_la_inexistente_dan_el_mismo_404(self):
        antes = self.fotografia()
        ajena = self.get(self.estudiante, self.practica_par)
        otra_carrera = self.get(self.estudiante, self.ajena)
        inexistente = self.get(self.estudiante, 999_999)

        for respuesta in (ajena, otra_carrera):
            self.assertEqual(respuesta.status_code, 404)
            self.assertEqual(respuesta.json(), inexistente.json())
        self.assertRechazo(
            inexistente,
            404,
            "Recurso no encontrado.",
            {"detail": "No encontrado.", "code": "no_encontrado"},
        )
        self.assertEqual(self.fotografia(), antes)

    def test_coordinador_director_y_secretaria_ven_su_carrera_y_no_la_ajena(self):
        for actor in (self.coordinador, self.director, self.secretaria):
            with self.subTest(rol=actor.rol):
                for practica in (self.practica, self.practica_par):
                    self.assertExito(self.get(actor, practica))
                self.assertEqual(self.get(actor, self.ajena).status_code, 404)

        self.assertExito(self.get(self.coordinador_par, self.ajena))
        self.assertEqual(self.get(self.coordinador_par, self.practica).status_code, 404)

    def test_el_tutor_academico_solo_ve_sus_asignaciones_activas(self):
        self.assertExito(self.get(self.tutor, self.practica))
        self.assertExito(self.get(self.tutor, self.practica_par))
        self.assertEqual(self.get(self.otro_tutor, self.practica).status_code, 404)
        self.assertEqual(self.get(self.tutor, self.ajena).status_code, 404)

    def test_el_tutor_de_entidad_ve_solo_su_practica_laboral_vinculada(self):
        self.assertExito(self.get(self.externo, self.practica))
        self.assertEqual(self.get(self.externo, self.practica_par).status_code, 404)
        self.assertEqual(self.get(self.externo, self.ajena).status_code, 404)

    def test_el_get_no_escribe_nada(self):
        self.crear_reporte(semana=1, horas=12, estado=ReporteSemanal.Estado.VALIDADO)
        antes = self.fotografia()

        self.assertExito(self.get(self.estudiante))
        self.assertExito(self.get(self.tutor))
        self.get(None)
        self.get(self.estudiante, 999_999)

        self.assertEqual(self.fotografia(), antes)

    @override_settings(DEBUG=True)
    def test_el_endpoint_aparece_en_swagger_con_su_404(self):
        documento = yaml.safe_load(self.client.get("/api/v1/schema/").content)
        operacion = documento["paths"][HORAS.replace("{}", "{practica_id}")]["get"]
        self.assertLessEqual({"200", "404"}, set(operacion["responses"]))
