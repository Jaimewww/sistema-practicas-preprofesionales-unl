"""Endpoints de validación del reporte semanal (S2-S8, #122).

Recorre las tres rutas del issue #122 con ``APIClient``: la cola de pendientes del
tutor académico (``GET /api/v1/pendientes/``), la validación
(``POST /api/v1/reportes/{id}/validar/``, sin cuerpo) y la devolución
(``POST /api/v1/reportes/{id}/devolver/``, con ``observacion`` obligatoria).

S7: solo los reportes «en revisión» de las prácticas asignadas al tutor aparecen
en la cola; validar o devolver deja el reporte en su estado y registra la
``Validacion`` con autor y fecha (S4). Un rechazo no escribe y el cuerpo es el
envelope de #77 con ``errors.code`` en todos los casos.
"""

from collections.abc import Callable
from datetime import date

from apps.reportes.services import MENSAJE_PRACTICA_NO_EN_CURSO, MENSAJE_TUTOR
from django.test import TestCase
from rest_framework.test import APIClient

from apps.actividades.models import MENSAJE_OBSERVACION, PlanActividades, Validacion
from apps.auditoria.models import HistorialEstado
from apps.carreras.models import Carrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import AsignacionTutor, Periodo, Practica
from apps.reportes.api import MENSAJE_CUERPO_DEVOLVER, MENSAJE_PENDIENTES
from apps.reportes.models import ReporteSemanal
from apps.usuarios.models import Usuario

PENDIENTES = "/api/v1/pendientes/"
VALIDAR = "/api/v1/reportes/{}/validar/"
DEVOLVER = "/api/v1/reportes/{}/devolver/"
OBSERVACION = "Detalle las semanas 3 y 4."
CAMPOS_PENDIENTE = {"id", "practica_id", "semana", "horas_reportadas", "estado"}
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


class ValidacionReportesFixturesMixin:
    """Dos prácticas asignadas al tutor, una sin asignar y los seis roles."""

    assertEqual: Callable[..., None]
    assertFalse: Callable[..., None]
    assertIs: Callable[..., None]
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
        cls.estudiante = crear_usuario("estudiante1", Usuario.Rol.ESTUDIANTE)
        cls.par = crear_usuario("estudiante2", Usuario.Rol.ESTUDIANTE)
        cls.tutor = crear_usuario(
            "academico1", Usuario.Rol.TUTOR_ACADEMICO, cls.carrera
        )
        cls.otro_tutor = crear_usuario(
            "academico2", Usuario.Rol.TUTOR_ACADEMICO, cls.carrera
        )
        cls.coordinador = crear_usuario(
            "coordinador1", Usuario.Rol.COORDINADOR, cls.carrera
        )
        cls.externo = crear_usuario("externo1", Usuario.Rol.TUTOR_ENTIDAD)
        cls.practica = cls.crear_practica(cls.estudiante)
        cls.otra_practica = cls.crear_practica(cls.par)
        cls.ajena = cls.crear_practica(cls.estudiante)
        for practica in (cls.practica, cls.otra_practica):
            AsignacionTutor.objects.create(
                practica=practica, tutor_academico=cls.tutor, desde=date(2026, 1, 1)
            )

    @classmethod
    def crear_practica(cls, estudiante):
        practica = Practica(
            estudiante=estudiante,
            carrera=cls.carrera,
            entidad=cls.entidad,
            periodo=cls.periodo,
            tipo=Practica.Tipo.LABORAL,
            subtipo=Practica.Subtipo.PRACTICA,
            horas_requeridas=240,
            estado=Practica.Estado.EN_CURSO,
        )
        practica.full_clean()
        practica.save()
        return practica

    def crear_reporte(
        self, practica=None, semana=1, horas=8, estado=ReporteSemanal.Estado.EN_REVISION
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

    def publicar(self, ruta, usuario, datos=None):
        return self.cliente(usuario).post(
            ruta, datos if datos is not None else {}, format="json"
        )

    def fotografia(self):
        """Filas por modelo y estados de reportes y prácticas: un rechazo no cambia nada."""
        foto = {modelo.__name__: modelo.objects.count() for modelo in MODELOS}
        foto["estados_reporte"] = list(
            ReporteSemanal.objects.order_by("pk").values_list("pk", "estado")
        )
        foto["estados_practica"] = list(
            Practica.objects.order_by("pk").values_list("pk", "estado")
        )
        return foto

    def assertRechazo(self, respuesta, estado, mensaje, errores):
        """Estado, envelope exacto (mensaje y ``errors`` con ``code``) y sin datos."""
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

    def assertExito(self, respuesta, estado=200):
        """Envelope de éxito completo: ``errors`` nulo y ``meta`` vacío."""
        self.assertEqual(respuesta.status_code, estado)
        cuerpo = respuesta.json()
        self.assertIs(cuerpo["success"], True)
        self.assertEqual(cuerpo["errors"], None)
        self.assertEqual(cuerpo["meta"], {})
        self.assertEqual(
            respuesta.json()["message"],
            "Recurso creado." if estado == 201 else "Operación exitosa.",
        )
        return cuerpo["data"]


class PendientesTests(ValidacionReportesFixturesMixin, TestCase):
    """S2/S7: la cola del tutor son los reportes en revisión de sus prácticas."""

    def test_el_tutor_ve_solo_los_reportes_en_revision_de_sus_practicas(self):
        pendiente = self.crear_reporte(practica=self.practica, semana=2, horas=12)
        self.crear_reporte(practica=self.practica, semana=1, estado="validado")
        self.crear_reporte(practica=self.practica, semana=3, estado="devuelto")
        self.crear_reporte(practica=self.ajena, semana=1)

        data = self.assertExito(self.cliente(self.tutor).get(PENDIENTES))

        self.assertEqual(
            data,
            [
                {
                    "id": pendiente.pk,
                    "practica_id": self.practica.pk,
                    "semana": 2,
                    "horas_reportadas": 12,
                    "estado": "en_revision",
                }
            ],
        )
        self.assertEqual(set(data[0]), CAMPOS_PENDIENTE)

    def test_la_cola_incluye_las_dos_practicas_asignadas_y_nada_mas(self):
        self.crear_reporte(practica=self.practica, semana=1)
        self.crear_reporte(practica=self.otra_practica, semana=1)

        data = self.assertExito(self.cliente(self.tutor).get(PENDIENTES))

        self.assertEqual(
            {fila["practica_id"] for fila in data},
            {self.practica.pk, self.otra_practica.pk},
        )

    def test_una_asignacion_cerrada_deja_de_mostrar_sus_pendientes(self):
        self.crear_reporte(practica=self.practica, semana=1)
        AsignacionTutor.objects.filter(practica=self.practica).update(
            hasta=date(2026, 6, 1)
        )

        self.assertEqual(self.assertExito(self.cliente(self.tutor).get(PENDIENTES)), [])

    def test_otro_tutor_no_ve_los_pendientes_ajenos(self):
        self.crear_reporte(practica=self.practica, semana=1)

        self.assertEqual(
            self.assertExito(self.cliente(self.otro_tutor).get(PENDIENTES)), []
        )

    def test_sin_token_responde_401(self):
        respuesta = self.cliente().get(PENDIENTES)
        self.assertRechazo(
            respuesta,
            401,
            "Autenticación requerida.",
            {"detail": "Se requiere autenticación.", "code": "no_autenticado"},
        )

    def test_un_rol_que_no_es_tutor_academico_responde_403(self):
        for actor in (self.estudiante, self.coordinador, self.externo):
            with self.subTest(rol=actor.rol):
                respuesta = self.cliente(actor).get(PENDIENTES)
                self.assertRechazo(
                    respuesta,
                    403,
                    "Permiso denegado.",
                    {"detail": MENSAJE_PENDIENTES, "code": "permiso_denegado"},
                )


class ValidarReporteEndpointTests(ValidacionReportesFixturesMixin, TestCase):
    """S3/S4: ``POST /api/v1/reportes/{id}/validar/`` sin cuerpo, 200 con el reporte."""

    def test_validar_responde_200_y_deja_el_reporte_validado(self):
        reporte = self.crear_reporte(semana=5, horas=9)

        data = self.assertExito(self.publicar(VALIDAR.format(reporte.pk), self.tutor))

        self.assertEqual(
            (data["id"], data["estado"], data["semana"]),
            (reporte.pk, "validado", 5),
        )
        self.assertEqual(ReporteSemanal.objects.get(pk=reporte.pk).estado, "validado")
        validacion = Validacion.objects.get()
        self.assertEqual(
            (
                validacion.decision,
                validacion.reporte_id,
                validacion.autor_id,
                validacion.plan_id,
            ),
            ("aprobado", reporte.pk, self.tutor.pk, None),
        )
        self.assertIsNotNone(validacion.fecha)

    def test_validar_sin_token_responde_401_y_no_escribe(self):
        reporte = self.crear_reporte()
        antes = self.fotografia()
        respuesta = self.publicar(VALIDAR.format(reporte.pk), None)
        self.assertRechazo(
            respuesta,
            401,
            "Autenticación requerida.",
            {"detail": "Se requiere autenticación.", "code": "no_autenticado"},
        )
        self.assertEqual(self.fotografia(), antes)

    def test_solo_el_tutor_academico_puede_validar(self):
        reporte = self.crear_reporte()
        antes = self.fotografia()
        for actor in (self.estudiante, self.par, self.coordinador, self.externo):
            with self.subTest(rol=actor.rol):
                respuesta = self.publicar(VALIDAR.format(reporte.pk), actor)
                self.assertRechazo(
                    respuesta,
                    403,
                    "Permiso denegado.",
                    {"detail": MENSAJE_TUTOR, "code": "permiso_denegado"},
                )
        self.assertEqual(self.fotografia(), antes)

    def test_un_reporte_ya_validado_responde_409_sin_escribir(self):
        reporte = self.crear_reporte()
        self.assertExito(self.publicar(VALIDAR.format(reporte.pk), self.tutor))
        antes = self.fotografia()

        respuesta = self.publicar(VALIDAR.format(reporte.pk), self.tutor)

        self.assertRechazo(
            respuesta,
            409,
            "Solicitud inválida.",
            {
                "detail": "Transición no permitida: el reporte está en «validado» y "
                "solo se valida uno «en_revision».",
                "code": "reporte_no_en_revision",
            },
        )
        self.assertEqual(self.fotografia(), antes)

    def test_un_reporte_devuelto_tampoco_se_valida(self):
        reporte = self.crear_reporte(estado=ReporteSemanal.Estado.DEVUELTO)
        antes = self.fotografia()
        respuesta = self.publicar(VALIDAR.format(reporte.pk), self.tutor)
        self.assertEqual(respuesta.status_code, 409)
        self.assertEqual(self.fotografia(), antes)

    def test_inexistente_y_fuera_de_alcance_dan_el_mismo_404(self):
        ajeno = self.crear_reporte(practica=self.ajena)
        antes = self.fotografia()
        inexistente = self.publicar(VALIDAR.format(999_999), self.tutor)
        fuera = self.publicar(VALIDAR.format(ajeno.pk), self.tutor)
        self.assertRechazo(
            inexistente,
            404,
            "Recurso no encontrado.",
            {"detail": "No encontrado.", "code": "no_encontrado"},
        )
        self.assertEqual(fuera.status_code, 404)
        self.assertEqual(fuera.json(), inexistente.json())
        self.assertEqual(self.fotografia(), antes)


class DevolverReporteEndpointTests(ValidacionReportesFixturesMixin, TestCase):
    """S3/S6/S8: devolver exige observación; sin ella, 400 y nada se escribe."""

    def test_devolver_con_observacion_responde_200_y_deja_devuelto(self):
        reporte = self.crear_reporte(semana=6, horas=7)

        data = self.assertExito(
            self.publicar(
                DEVOLVER.format(reporte.pk),
                self.tutor,
                {"observacion": f"  {OBSERVACION}  "},
            )
        )

        self.assertEqual((data["id"], data["estado"]), (reporte.pk, "devuelto"))
        self.assertEqual(ReporteSemanal.objects.get(pk=reporte.pk).estado, "devuelto")
        self.assertEqual(ReporteSemanal.objects.count(), 1)
        validacion = Validacion.objects.get()
        self.assertEqual(
            (validacion.decision, validacion.observacion, validacion.reporte_id),
            ("devuelto", OBSERVACION, reporte.pk),
        )
        # El estudiante ve la observación en la fila devuelta (S8).
        self.assertEqual(list(reporte.validaciones.all()), [validacion])

    def test_devolver_sin_observacion_responde_400_y_no_escribe(self):
        reporte = self.crear_reporte()
        antes = self.fotografia()
        for datos in ({}, {"observacion": ""}, {"observacion": "   "}):
            with self.subTest(datos=datos):
                respuesta = self.publicar(
                    DEVOLVER.format(reporte.pk), self.tutor, datos
                )
                self.assertRechazo(
                    respuesta,
                    400,
                    "Datos inválidos.",
                    {"observacion": [MENSAJE_OBSERVACION]},
                )
        self.assertEqual(self.fotografia(), antes)

    def test_devolver_sin_token_responde_401(self):
        reporte = self.crear_reporte()
        antes = self.fotografia()
        respuesta = self.publicar(
            DEVOLVER.format(reporte.pk), None, {"observacion": OBSERVACION}
        )
        self.assertRechazo(
            respuesta,
            401,
            "Autenticación requerida.",
            {"detail": "Se requiere autenticación.", "code": "no_autenticado"},
        )
        self.assertEqual(self.fotografia(), antes)

    def test_solo_el_tutor_academico_puede_devolver(self):
        reporte = self.crear_reporte()
        antes = self.fotografia()
        for actor in (self.estudiante, self.coordinador, self.externo):
            with self.subTest(rol=actor.rol):
                respuesta = self.publicar(
                    DEVOLVER.format(reporte.pk), actor, {"observacion": OBSERVACION}
                )
                self.assertRechazo(
                    respuesta,
                    403,
                    "Permiso denegado.",
                    {"detail": MENSAJE_TUTOR, "code": "permiso_denegado"},
                )
        self.assertEqual(self.fotografia(), antes)

    def test_devolver_un_reporte_ya_devuelto_responde_409(self):
        reporte = self.crear_reporte()
        self.publicar(
            DEVOLVER.format(reporte.pk), self.tutor, {"observacion": OBSERVACION}
        )
        antes = self.fotografia()
        respuesta = self.publicar(
            DEVOLVER.format(reporte.pk), self.tutor, {"observacion": "Otra."}
        )
        self.assertRechazo(
            respuesta,
            409,
            "Solicitud inválida.",
            {
                "detail": "Transición no permitida: el reporte está en «devuelto» y "
                "solo se valida uno «en_revision».",
                "code": "reporte_no_en_revision",
            },
        )
        self.assertEqual(self.fotografia(), antes)

    def test_un_reporte_fuera_de_alcance_responde_404_identico_al_inexistente(self):
        ajeno = self.crear_reporte(practica=self.ajena)
        antes = self.fotografia()
        inexistente = self.publicar(
            DEVOLVER.format(999_999), self.tutor, {"observacion": OBSERVACION}
        )
        fuera = self.publicar(
            DEVOLVER.format(ajeno.pk), self.tutor, {"observacion": OBSERVACION}
        )
        self.assertRechazo(
            inexistente,
            404,
            "Recurso no encontrado.",
            {"detail": "No encontrado.", "code": "no_encontrado"},
        )
        self.assertEqual(fuera.json(), inexistente.json())
        self.assertEqual(self.fotografia(), antes)

class PracticaNoEnCursoEndpointTests(ValidacionReportesFixturesMixin, TestCase):
    """CU-01 2b (spec.md:497): con la práctica suspendida, cancelada o cerrada no
    se valida ni se devuelve (409 ``practica_no_en_curso``) y no se escribe nada."""

    ESTADOS = (
        Practica.Estado.SUSPENDIDA,
        Practica.Estado.CANCELADA,
        Practica.Estado.CERRADA,
    )

    def con_practica_en(self, estado):
        Practica.objects.filter(pk=self.practica.pk).update(estado=estado)

    # S9a: ni antes de empezar ni ya en revisión final la práctica está en curso.
    ESTADOS_FUERA_DE_CURSO = (
        Practica.Estado.ASIGNADA,
        Practica.Estado.EN_REVISION_FINAL,
    )

    def afirmar_409(self, ruta, datos=None, estados=None):
        for i, estado in enumerate(estados or self.ESTADOS):
            with self.subTest(estado=estado):
                reporte = self.crear_reporte(semana=i + 1)
                self.con_practica_en(estado)
                antes = self.fotografia()

                respuesta = self.publicar(ruta.format(reporte.pk), self.tutor, datos)

                self.assertRechazo(
                    respuesta,
                    409,
                    "Solicitud inválida.",
                    {
                        "detail": MENSAJE_PRACTICA_NO_EN_CURSO.format(estado=estado),
                        "code": "practica_no_en_curso",
                    },
                )
                self.assertEqual(self.fotografia(), antes)

    def test_validar_con_la_practica_no_en_curso_responde_409(self):
        self.afirmar_409(VALIDAR)

    def test_devolver_con_la_practica_no_en_curso_responde_409(self):
        self.afirmar_409(DEVOLVER, {"observacion": OBSERVACION})

    def test_validar_con_la_practica_asignada_o_en_revision_final_responde_409(self):
        self.afirmar_409(VALIDAR, estados=self.ESTADOS_FUERA_DE_CURSO)

    def test_devolver_con_la_practica_asignada_o_en_revision_final_responde_409(
        self,
    ):
        self.afirmar_409(
            DEVOLVER,
            {"observacion": OBSERVACION},
            estados=self.ESTADOS_FUERA_DE_CURSO,
        )

    def test_la_cola_excluye_las_practicas_asignadas_o_en_revision_final(self):
        self.crear_reporte(practica=self.practica)
        visible = self.crear_reporte(practica=self.otra_practica)
        for estado in self.ESTADOS_FUERA_DE_CURSO:
            with self.subTest(estado=estado):
                self.con_practica_en(estado)

                data = self.assertExito(self.cliente(self.tutor).get(PENDIENTES))

                self.assertEqual([fila["id"] for fila in data], [visible.pk])

    def test_tutor_no_asignado_en_practica_no_en_curso_recibe_el_mismo_404(self):
        """S9d: fuera de alcance manda el 404, no el 409 que revelaría la fila."""
        reporte = self.crear_reporte()
        ajeno = self.crear_reporte(practica=self.ajena)
        Practica.objects.filter(pk=self.ajena.pk).update(
            estado=Practica.Estado.SUSPENDIDA
        )
        self.con_practica_en(Practica.Estado.CERRADA)
        antes = self.fotografia()
        for ruta, datos in ((VALIDAR, None), (DEVOLVER, {"observacion": OBSERVACION})):
            inexistente = self.publicar(ruta.format(999_999), self.tutor, datos)
            self.assertRechazo(
                inexistente,
                404,
                "Recurso no encontrado.",
                {"detail": "No encontrado.", "code": "no_encontrado"},
            )
            for actor, objetivo in ((self.otro_tutor, reporte), (self.tutor, ajeno)):
                with self.subTest(ruta=ruta, actor=actor.username, reporte=objetivo.pk):
                    respuesta = self.publicar(ruta.format(objetivo.pk), actor, datos)
                    self.assertEqual(respuesta.status_code, 404)
                    self.assertEqual(respuesta.json(), inexistente.json())
        self.assertEqual(self.fotografia(), antes)

    def test_la_cola_excluye_los_reportes_de_una_practica_suspendida(self):
        self.crear_reporte(practica=self.practica)
        visible = self.crear_reporte(practica=self.otra_practica)
        self.con_practica_en(Practica.Estado.SUSPENDIDA)

        respuesta = self.cliente(self.tutor).get(PENDIENTES)

        data = self.assertExito(respuesta)
        self.assertEqual([fila["id"] for fila in data], [visible.pk])

    def test_devolver_con_un_cuerpo_que_no_es_objeto_responde_400(self):
        reporte = self.crear_reporte()
        antes = self.fotografia()
        for cuerpo in ([1], ["observacion"], "x", 7):
            with self.subTest(cuerpo=cuerpo):
                respuesta = self.publicar(DEVOLVER.format(reporte.pk), self.tutor, cuerpo)
                self.assertRechazo(
                    respuesta,
                    400,
                    "Datos inválidos.",
                    {"non_field_errors": [MENSAJE_CUERPO_DEVOLVER]},
                )
        self.assertEqual(self.fotografia(), antes)

    def test_devolver_con_un_cuerpo_vacio_que_no_es_objeto_responde_400(self):
        """S9c: ``[]`` y ``""`` son falsos pero tampoco son objetos: 400, no 500."""
        reporte = self.crear_reporte()
        antes = self.fotografia()
        for cuerpo in ([], ""):
            with self.subTest(cuerpo=cuerpo):
                respuesta = self.publicar(DEVOLVER.format(reporte.pk), self.tutor, cuerpo)
                self.assertRechazo(
                    respuesta,
                    400,
                    "Datos inválidos.",
                    {"non_field_errors": [MENSAJE_CUERPO_DEVOLVER]},
                )
        self.assertEqual(self.fotografia(), antes)
        self.assertEqual(
            ReporteSemanal.objects.get(pk=reporte.pk).estado,
            ReporteSemanal.Estado.EN_REVISION,
        )
