"""Endpoint de reenvío del reporte devuelto (S8, RF-03, #124).

``POST /api/v1/reportes/{id}/reenviar/`` devuelve a «en revisión» el reporte que
el tutor académico dejó «devuelto», para que el estudiante lo corrija. La fila es
la misma: el reporte no tiene ``version`` (data-model §ReporteSemanal) y el
reenvío no es una validación, así que no escribe ``Validacion`` ni renueva
``fecha_registro``.

Solo el estudiante de la práctica reenvía: cualquier otro rol recibe 403 y otro
estudiante recibe el mismo 404 que un id inexistente (sin oráculo de
existencia). Fuera de «devuelto» el reenvío responde 409 ``reporte_no_devuelto``.
Un rechazo no escribe nada y el cuerpo es el envelope de #77 con
``errors.code``; el éxito trae la tarjeta de cinco campos del reporte.
"""

from collections.abc import Callable
from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from apps.actividades.models import MENSAJE_OBSERVACION, PlanActividades, Validacion
from apps.auditoria.models import HistorialEstado
from apps.carreras.models import Carrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import AsignacionTutor, Periodo, Practica
from apps.reportes.models import ReporteSemanal
from apps.reportes.services import MENSAJE_ESTUDIANTE, MENSAJE_REENVIO
from apps.usuarios.models import Usuario

REENVIAR = "/api/v1/reportes/{}/reenviar/"
OBSERVACION = "Detalle las semanas 3 y 4."
CAMPOS_REPORTE = {"id", "practica_id", "semana", "horas_reportadas", "estado"}
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


class ReenvioReporteFixturesMixin:
    """Dos prácticas asignadas al tutor, una sin asignar y los seis roles."""

    assertEqual: Callable[..., None]
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
        )
        practica.full_clean()
        practica.save()
        return practica

    def crear_reporte(
        self, practica=None, semana=1, horas=8, estado=ReporteSemanal.Estado.DEVUELTO
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
        """Conteos por modelo más el estado y la fecha de registro de cada reporte."""
        conteos = {modelo.__name__: modelo.objects.count() for modelo in MODELOS}
        reportes = tuple(
            ReporteSemanal.objects.order_by("pk").values_list(
                "pk", "estado", "fecha_registro"
            )
        )
        return conteos, reportes

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
        self.assertEqual(cuerpo["message"], "Operación exitosa.")
        return cuerpo["data"]


class ReenviarReporteEndpointTests(ReenvioReporteFixturesMixin, TestCase):
    """S8: el estudiante reenvía su reporte devuelto y vuelve a «en revisión»."""

    def test_el_estudiante_reenvia_su_reporte_devuelto_y_queda_en_revision(self):
        reporte = self.crear_reporte(semana=4, horas=11)
        fecha_registro = reporte.fecha_registro

        data = self.assertExito(
            self.publicar(REENVIAR.format(reporte.pk), self.estudiante)
        )

        self.assertEqual(
            data,
            {
                "id": reporte.pk,
                "practica_id": self.practica.pk,
                "semana": 4,
                "horas_reportadas": 11,
                "estado": "en_revision",
            },
        )
        self.assertEqual(set(data), CAMPOS_REPORTE)
        guardado = ReporteSemanal.objects.get(pk=reporte.pk)
        self.assertEqual(guardado.estado, "en_revision")
        self.assertEqual(ReporteSemanal.objects.count(), 1)  # misma fila, sin version
        self.assertEqual(guardado.fecha_registro, fecha_registro)
        self.assertEqual(Validacion.objects.count(), 0)  # reenviar no es validar

    def test_el_reenvio_sobre_una_devolucion_previa_funciona_y_conserva_la_observacion(
        self,
    ):
        reporte = self.crear_reporte(semana=2, estado=ReporteSemanal.Estado.EN_REVISION)
        self.publicar(
            f"/api/v1/reportes/{reporte.pk}/devolver/",
            self.tutor,
            {"observacion": f"  {OBSERVACION}  "},
        )

        data = self.assertExito(
            self.publicar(REENVIAR.format(reporte.pk), self.estudiante)
        )

        self.assertEqual(data["estado"], "en_revision")
        validacion = Validacion.objects.get()
        self.assertEqual(
            (validacion.decision, validacion.observacion, validacion.reporte_id),
            ("devuelto", OBSERVACION, reporte.pk),
        )
        self.assertEqual(Validacion.objects.count(), 1)

    def test_sin_token_responde_401_y_no_escribe(self):
        reporte = self.crear_reporte()
        antes = self.fotografia()

        respuesta = self.publicar(REENVIAR.format(reporte.pk), None)

        self.assertRechazo(
            respuesta,
            401,
            "Autenticación requerida.",
            {"detail": "Se requiere autenticación.", "code": "no_autenticado"},
        )
        self.assertEqual(self.fotografia(), antes)

    def test_solo_el_estudiante_de_la_practica_reenvia_su_reporte(self):
        reporte = self.crear_reporte()
        antes = self.fotografia()

        for actor in (
            self.tutor,
            self.otro_tutor,
            self.coordinador,
            self.externo,
        ):
            with self.subTest(rol=actor.rol):
                respuesta = self.publicar(REENVIAR.format(reporte.pk), actor)
                self.assertRechazo(
                    respuesta,
                    403,
                    "Permiso denegado.",
                    {"detail": MENSAJE_ESTUDIANTE, "code": "permiso_denegado"},
                )

        self.assertEqual(self.fotografia(), antes)

    def test_otro_estudiante_recibe_el_mismo_404_sin_oraculo_y_no_escribe(self):
        ajeno = self.crear_reporte(practica=self.otra_practica)
        antes = self.fotografia()

        respuesta = self.publicar(REENVIAR.format(ajeno.pk), self.estudiante)
        inexistente = self.publicar(REENVIAR.format(999_999), self.estudiante)

        self.assertRechazo(
            respuesta,
            404,
            "Recurso no encontrado.",
            {"detail": "No encontrado.", "code": "no_encontrado"},
        )
        self.assertEqual(inexistente.status_code, 404)
        self.assertEqual(inexistente.json(), respuesta.json())
        self.assertEqual(self.fotografia(), antes)

    def test_un_reporte_en_revision_responde_409_sin_escribir(self):
        reporte = self.crear_reporte(estado=ReporteSemanal.Estado.EN_REVISION)
        antes = self.fotografia()

        respuesta = self.publicar(REENVIAR.format(reporte.pk), self.estudiante)

        self.assertRechazo(
            respuesta,
            409,
            "Solicitud inválida.",
            {
                "detail": MENSAJE_REENVIO.format(estado="en_revision"),
                "code": "reporte_no_devuelto",
            },
        )
        self.assertEqual(self.fotografia(), antes)

    def test_un_reporte_ya_validado_responde_409_sin_escribir(self):
        reporte = self.crear_reporte(estado=ReporteSemanal.Estado.VALIDADO)
        antes = self.fotografia()

        respuesta = self.publicar(REENVIAR.format(reporte.pk), self.estudiante)

        self.assertRechazo(
            respuesta,
            409,
            "Solicitud inválida.",
            {
                "detail": MENSAJE_REENVIO.format(estado="validado"),
                "code": "reporte_no_devuelto",
            },
        )
        self.assertEqual(self.fotografia(), antes)

    def test_cada_estudiante_reenvia_solo_la_fila_de_su_propia_practica(self):
        """El alcance sale de la práctica del actor: el dueño sí puede."""
        propio = self.crear_reporte(practica=self.otra_practica, semana=3)

        data = self.assertExito(self.publicar(REENVIAR.format(propio.pk), self.par))

        self.assertEqual(
            (data["practica_id"], data["estado"]),
            (self.otra_practica.pk, "en_revision"),
        )
        self.assertEqual(ReporteSemanal.objects.get(pk=propio.pk).estado, "en_revision")


class CicloCompletoTests(ReenvioReporteFixturesMixin, TestCase):
    """PRESERVE: devolver -> reenviar -> validar sigue siendo el ciclo de #122/#124.

    ``_traducir`` es compartido con ``validar``/``devolver``: su mapeo de 409 debe
    seguir dando ``reporte_no_en_revision`` para esas dos rutas aunque el reenvío
    estrene su propio código.
    """

    def test_el_ciclo_devolver_reenviar_validar_termina_validado(self):
        reporte = self.crear_reporte(
            semana=7, horas=6, estado=ReporteSemanal.Estado.EN_REVISION
        )
        devolver = f"/api/v1/reportes/{reporte.pk}/devolver/"
        validar = f"/api/v1/reportes/{reporte.pk}/validar/"

        self.assertExito(
            self.publicar(devolver, self.tutor, {"observacion": OBSERVACION})
        )
        self.assertExito(self.publicar(REENVIAR.format(reporte.pk), self.estudiante))
        data = self.assertExito(self.publicar(validar, self.tutor))

        self.assertEqual(data["estado"], "validado")
        self.assertEqual(
            list(Validacion.objects.order_by("pk").values_list("decision", flat=True)),
            ["devuelto", "aprobado"],
        )

    def test_validar_fuera_de_revision_conserva_su_409_de_siempre(self):
        reporte = self.crear_reporte(estado=ReporteSemanal.Estado.DEVUELTO)
        antes = self.fotografia()

        respuesta = self.publicar(f"/api/v1/reportes/{reporte.pk}/validar/", self.tutor)

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

    def test_devolver_sin_observacion_conserva_su_400_de_siempre(self):
        reporte = self.crear_reporte(estado=ReporteSemanal.Estado.EN_REVISION)
        antes = self.fotografia()

        respuesta = self.publicar(
            f"/api/v1/reportes/{reporte.pk}/devolver/", self.tutor, {}
        )

        self.assertRechazo(
            respuesta, 400, "Datos inválidos.", {"observacion": [MENSAJE_OBSERVACION]}
        )
        self.assertEqual(self.fotografia(), antes)
