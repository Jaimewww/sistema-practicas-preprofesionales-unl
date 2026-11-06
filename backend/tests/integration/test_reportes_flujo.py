"""Flujo completo del registro de reportes semanales (S2-S7, #78).

Recorre las tres rutas del contrato con ``APIClient``: la lista y el detalle de
prácticas con el alcance de filas de T019 y el POST del reporte con sus reglas
(art. 341 para ayudantías, semana duplicada, estados finales, actor dueño). Un
rechazo no escribe: ni filas ni contadores cambian (S3).

Reconciliación de #79 (auth-first, doc L4): con el JWT real estas rutas exigen
credenciales, así que los casos anónimos pasan a 401 y los que ya no son del rol
(o del dueño) a 403. Las aserciones originales siguen: sus casos se conservan con
un actor forzado y el «no escribe» no se relajó — solo cambió el estado de
rechazo, que ahora también se verifica.
"""

from collections.abc import Callable
from datetime import date

import yaml
from apps.auditoria.models import HistorialEstado
from apps.carreras.models import Carrera, ConfiguracionCarrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import AsignacionTutor, Periodo, Practica
from apps.practicas.services import asignar_practica
from apps.reportes.models import ReporteSemanal
from apps.usuarios.models import Usuario
from apps.usuarios.permissions import practicas_visibles_para
from django.test import TestCase
from rest_framework.test import APIClient

LISTA = "/api/v1/practicas/"
DETALLE = "/api/v1/practicas/{}/"
REPORTES = "/api/v1/practicas/{}/reportes/"
PAYLOAD = {"semana": 1, "horas_reportadas": 8}
CAMPOS_TARJETA = {
    "id", "estudiante_id", "tipo", "subtipo", "estado", "horas_requeridas"
}
MODELOS = (
    Usuario, Carrera, ConfiguracionCarrera, Periodo, EntidadReceptora, Practica,
    AsignacionTutor, HistorialEstado, ReporteSemanal,
)


def crear_usuario(username, rol, carrera=None):
    return Usuario.objects.create_user(
        username=username, nombre=username.title(), email=f"{username}@example.com",
        rol=rol, carrera=carrera, password=None,
    )


class FlujoFixturesMixin:
    """Dos carreras con configuración, seis roles y prácticas en varios estados."""

    assertEqual: Callable[..., None]
    assertFalse: Callable[..., None]
    assertTrue: Callable[..., None]

    @classmethod
    def setUpTestData(cls):
        cls.carrera = Carrera.objects.create(
            codigo="ING-SIS", nombre="Ingeniería de Sistemas"
        )
        cls.otra_carrera = Carrera.objects.create(codigo="DER-001", nombre="Derecho")
        for carrera in (cls.carrera, cls.otra_carrera):
            for modalidad in ("laboral", "comunitaria"):
                ConfiguracionCarrera.objects.create(
                    carrera=carrera, modalidad=modalidad, horas_requeridas=240,
                    vigente_desde=date(2020, 1, 1),
                )
        cls.entidad = EntidadReceptora.objects.create(
            nombre="Junta Parroquial de San Lucas"
        )
        cls.periodo = Periodo.objects.create(
            nombre="2026-1", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 7, 31)
        )
        cls.estudiante = crear_usuario("estudiante1", Usuario.Rol.ESTUDIANTE)
        cls.par = crear_usuario("estudiante2", Usuario.Rol.ESTUDIANTE)
        cls.tutor = crear_usuario("academico1", Usuario.Rol.TUTOR_ACADEMICO, cls.carrera)
        cls.coordinador = crear_usuario("coordinador1", Usuario.Rol.COORDINADOR, cls.carrera)
        cls.coordinador_par = crear_usuario(
            "coordinador2", Usuario.Rol.COORDINADOR, cls.otra_carrera
        )
        cls.externo = crear_usuario("externo1", Usuario.Rol.TUTOR_ENTIDAD)
        cls.practica = cls.crear(cls.estudiante, tutor_entidad=cls.externo)
        cls.ayudantia = cls.crear(
            cls.estudiante, subtipo=Practica.Subtipo.AYUDANTIA_DOCENCIA
        )
        cls.ajena = cls.crear(cls.par, carrera=cls.otra_carrera)
        cls.cerrada = cls.crear(cls.par, estado=Practica.Estado.CERRADA)
        cls.cancelada = cls.crear(cls.par, estado=Practica.Estado.CANCELADA)
        AsignacionTutor.objects.create(
            practica=cls.practica, tutor_academico=cls.tutor, desde=date(2026, 1, 1)
        )

    @classmethod
    def crear(cls, estudiante, carrera=None, estado=None,
              subtipo=Practica.Subtipo.PRACTICA, tutor_entidad=None):
        """Asigna la práctica con el servicio de T018 y fija el estado pedido."""
        practica = asignar_practica(
            estudiante=estudiante, carrera=carrera or cls.carrera, periodo=cls.periodo,
            tipo=Practica.Tipo.LABORAL, autor=cls.coordinador, entidad=cls.entidad,
            subtipo=subtipo, tutor_entidad=tutor_entidad,
        )
        if estado is not None:
            practica.estado = estado
            practica.save(update_fields=["estado"])
        return practica

    def cliente(self, usuario=None):
        cliente = APIClient()
        if usuario is not None:
            cliente.force_authenticate(user=usuario)
        return cliente

    def ids_de_la_lista(self, usuario=None):
        respuesta = self.cliente(usuario).get(LISTA)
        self.assertEqual(respuesta.status_code, 200)
        cuerpo = respuesta.json()
        self.assertTrue(cuerpo["success"])
        return {fila["id"] for fila in cuerpo["data"]}

    def pks_carrera(self):
        return {
            self.practica.pk, self.ayudantia.pk, self.cerrada.pk, self.cancelada.pk
        }

    def crear_reporte(self, practica=None, semana=1, horas=8):
        return ReporteSemanal.objects.create(
            practica=practica or self.practica, semana=semana, horas_reportadas=horas
        )

    def fotografia(self):
        return {modelo.__name__: modelo.objects.count() for modelo in MODELOS}


class AlcanceDeFilasTests(FlujoFixturesMixin, TestCase):
    """La lista y el detalle entregan solo las prácticas visibles del actor (RF-11)."""

    def test_el_estudiante_solo_ve_sus_practicas(self):
        self.assertEqual(
            self.ids_de_la_lista(self.estudiante), {self.practica.pk, self.ayudantia.pk}
        )

    def test_el_coordinador_ve_su_carrera_y_no_la_ajena(self):
        self.assertEqual(self.ids_de_la_lista(self.coordinador), self.pks_carrera())
        self.assertEqual(self.ids_de_la_lista(self.coordinador_par), {self.ajena.pk})

    def test_el_tutor_externo_solo_ve_la_practica_vinculada_laboral(self):
        self.assertEqual(self.ids_de_la_lista(self.externo), {self.practica.pk})

    def test_anonimo_recibe_401_y_sin_fila_403_sin_filas_expuestas(self):
        """#79: la API real es auth-first; el alcance de T019 sigue vacío sin fila."""
        anonima = self.cliente().get(LISTA)
        self.assertEqual(anonima.status_code, 401)
        self.assertFalse(anonima.json()["success"])
        self.assertIsNone(anonima.json()["data"])

        sin_fila = self.cliente(Usuario(username="fantasma")).get(LISTA)
        self.assertEqual(sin_fila.status_code, 403)
        self.assertFalse(sin_fila.json()["success"])

        self.assertEqual(practicas_visibles_para(None).count(), 0)
        self.assertEqual(
            practicas_visibles_para(Usuario(username="fantasma")).count(), 0
        )

    def test_el_alcance_respeta_una_consulta_vacia_explicita(self):
        self.assertEqual(
            practicas_visibles_para(self.coordinador, Practica.objects.none()).count(), 0
        )
        self.assertEqual(
            set(practicas_visibles_para(self.coordinador).values_list("pk", flat=True)),
            self.pks_carrera(),
        )

    def test_el_detalle_del_dueno_trae_la_tarjeta(self):
        respuesta = self.cliente(self.estudiante).get(DETALLE.format(self.practica.pk))
        self.assertEqual(respuesta.status_code, 200)
        tarjeta = respuesta.json()["data"]
        self.assertEqual(set(tarjeta), CAMPOS_TARJETA)
        self.assertEqual(tarjeta["estudiante_id"], self.estudiante.pk)
        self.assertEqual(tarjeta["tipo"], Practica.Tipo.LABORAL)

    def test_el_detalle_fuera_de_alcance_o_inexistente_es_404(self):
        for actor, practica in (
            (self.coordinador_par, self.practica.pk), (self.estudiante, 999_999),
        ):
            with self.subTest(actor=getattr(actor, "username", "anon")):
                respuesta = self.cliente(actor).get(DETALLE.format(practica))
                self.assertEqual(respuesta.status_code, 404)
                self.assertFalse(respuesta.json()["success"])


class RegistroDeReportesTests(FlujoFixturesMixin, TestCase):
    """POST del reporte semanal: 201 al crear y 400/404 sin escribir (S2-S5)."""

    def test_el_post_registra_el_reporte_y_responde_201(self):
        respuesta = self.cliente(self.estudiante).post(
            REPORTES.format(self.practica.pk), PAYLOAD, format="json"
        )
        self.assertEqual(respuesta.status_code, 201)
        cuerpo = respuesta.json()
        self.assertTrue(cuerpo["success"])
        self.assertEqual(cuerpo["data"]["semana"], 1)
        self.assertEqual(cuerpo["data"]["horas_reportadas"], 8)
        self.assertEqual(cuerpo["data"]["estado"], ReporteSemanal.Estado.EN_REVISION)
        self.assertEqual(cuerpo["data"]["practica_id"], self.practica.pk)
        self.assertTrue(cuerpo["data"]["fecha_registro"])
        reporte = ReporteSemanal.objects.get(practica=self.practica)
        self.assertEqual((reporte.semana, reporte.horas_reportadas), (1, 8))

    def test_un_campo_fuera_del_data_model_se_rechaza(self):
        respuesta = self.cliente(self.estudiante).post(
            REPORTES.format(self.practica.pk), {**PAYLOAD, "contenido": "texto"},
            format="json",
        )
        self.assertEqual(respuesta.status_code, 400)
        errores = respuesta.json()["errors"]
        self.assertIn("contenido", errores)
        self.assertEqual(ReporteSemanal.objects.count(), 0)

    def test_semana_y_horas_deben_ser_positivas(self):
        casos = (("semana", 0), ("horas_reportadas", 0), ("horas_reportadas", -3))
        for campo, valor in casos:
            with self.subTest(campo=campo, valor=valor):
                respuesta = self.cliente(self.estudiante).post(
                    REPORTES.format(self.practica.pk), {**PAYLOAD, campo: valor},
                    format="json",
                )
                self.assertEqual(respuesta.status_code, 400)
                self.assertIn(campo, respuesta.json()["errors"])
        self.assertEqual(ReporteSemanal.objects.count(), 0)

    def test_la_semana_duplicada_se_rechaza_sin_escribir(self):
        self.crear_reporte()
        respuesta = self.cliente(self.estudiante).post(
            REPORTES.format(self.practica.pk), PAYLOAD, format="json"
        )
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("semana", respuesta.json()["errors"])
        self.assertEqual(ReporteSemanal.objects.count(), 1)

    def test_la_ayudantia_rechaza_mas_de_10_horas_con_el_art_341(self):
        respuesta = self.cliente(self.estudiante).post(
            REPORTES.format(self.ayudantia.pk), {"semana": 1, "horas_reportadas": 11},
            format="json",
        )
        self.assertEqual(respuesta.status_code, 400)
        mensaje = " ".join(respuesta.json()["errors"]["horas_reportadas"])
        self.assertIn("Art. 341", mensaje)
        self.assertEqual(ReporteSemanal.objects.count(), 0)

    def test_la_ayudantia_admite_exactamente_10_horas(self):
        respuesta = self.cliente(self.estudiante).post(
            REPORTES.format(self.ayudantia.pk), {"semana": 1, "horas_reportadas": 10},
            format="json",
        )
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(ReporteSemanal.objects.count(), 1)

    def test_la_practica_laboral_acepta_mas_de_40_horas(self):
        """S5: se identifica para revisión del tutor; el mecanismo no vive aquí."""
        respuesta = self.cliente(self.estudiante).post(
            REPORTES.format(self.practica.pk), {"semana": 1, "horas_reportadas": 41},
            format="json",
        )
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(ReporteSemanal.objects.get().horas_reportadas, 41)

    def test_un_actor_ajeno_o_sin_credenciales_no_escribe(self):
        """#79: 401 sin credenciales; 403 por rol sin permiso o por objeto ajeno."""
        casos = (
            (None, 401),
            (self.par, 403),
            (self.tutor, 403),
            (self.coordinador, 403),
            (self.externo, 403),
        )
        for actor, esperado in casos:
            with self.subTest(actor=getattr(actor, "username", "anon")):
                respuesta = self.cliente(actor).post(
                    REPORTES.format(self.practica.pk), PAYLOAD, format="json"
                )
                self.assertEqual(respuesta.status_code, esperado)
                self.assertFalse(respuesta.json()["success"])
        self.assertEqual(ReporteSemanal.objects.count(), 0)

    def test_una_practica_en_estado_final_rechaza_el_reporte(self):
        for practica in (self.cerrada, self.cancelada):
            with self.subTest(estado=practica.estado):
                respuesta = self.cliente(self.par).post(
                    REPORTES.format(practica.pk), PAYLOAD, format="json"
                )
                self.assertEqual(respuesta.status_code, 400)
                self.assertIn("estado", respuesta.json()["errors"])
        self.assertEqual(ReporteSemanal.objects.count(), 0)

    def test_una_practica_inexistente_responde_404(self):
        respuesta = self.cliente(self.estudiante).post(
            REPORTES.format(999_999), PAYLOAD, format="json"
        )
        self.assertEqual(respuesta.status_code, 404)
        self.assertFalse(respuesta.json()["success"])
        self.assertEqual(ReporteSemanal.objects.count(), 0)

    def test_un_rechazo_no_cambia_datos_ni_contadores(self):
        self.crear_reporte()
        antes = self.fotografia()
        rechazos = (
            (self.estudiante, self.practica.pk, {**PAYLOAD, "semana": 2, "extra": 1}),
            (self.estudiante, self.practica.pk, {"semana": 0, "horas_reportadas": 8}),
            (self.estudiante, self.practica.pk, PAYLOAD),
            (self.estudiante, self.ayudantia.pk, {"semana": 1, "horas_reportadas": 12}),
            (self.par, self.practica.pk, PAYLOAD),
            (self.par, self.cerrada.pk, PAYLOAD),
        )
        for actor, practica, datos in rechazos:
            with self.subTest(practica=practica, datos=datos):
                respuesta = self.cliente(actor).post(
                    REPORTES.format(practica), datos, format="json"
                )
                self.assertIn(respuesta.status_code, (400, 403, 404))
                self.assertEqual(self.fotografia(), antes)

    def test_el_endpoint_aparece_en_swagger_con_sus_errores(self):
        respuesta = self.client.get("/api/v1/schema/")
        self.assertEqual(respuesta.status_code, 200)
        documento = yaml.safe_load(respuesta.content)
        self.assertIn("get", documento["paths"][LISTA])
        operacion = documento["paths"]["/api/v1/practicas/{practica_id}/reportes/"]["post"]
        self.assertLessEqual({"201", "400", "404"}, set(operacion["responses"]))
        esquema = operacion["requestBody"]["content"]["application/json"]["schema"]
        if "$ref" in esquema:
            nombre = esquema["$ref"].rsplit("/", 1)[-1]
            esquema = documento["components"]["schemas"][nombre]
        self.assertEqual(set(esquema["properties"]), {"semana", "horas_reportadas"})


class PreservacionDemoTests(TestCase):
    """Retirado del demo (opción A): lo preservado conserva su payload."""

    def test_alertas_conserva_la_url_de_la_practica(self):
        from apps.prototipo.dto import to_alerta_dto

        salida = to_alerta_dto(
            {
                "tipo": "rezago", "tipo_display": "Rezago", "estado_badge": "warn",
                "detalle": "Detalle", "fecha": "2026-03-10",
                "practica": {
                    "id": 77, "estudiante": "Estudiante Um", "tipo": "laboral",
                    "tipo_display": "Laboral", "carrera": "ING",
                },
            },
            rol="estudiante",
        )
        self.assertEqual(salida["practica"]["url"], "/api/v1/practicas/77/")
        self.assertEqual(salida["practica"]["detalle_url"], "/prototipo/mi-practica/?practica=laboral")

    def test_el_dto_de_practica_payload_igual_con_url_real(self):
        from apps.prototipo.dto import PRACTICE_FIELDS, to_practica_dto

        salida = to_practica_dto(
            {
                **{campo: f"valor-{campo}" for campo in PRACTICE_FIELDS},
                "id": 77,
            },
            resumido=True,
        )
        self.assertEqual(salida["url"], "/api/v1/practicas/77/")

    def test_las_tres_rutas_reales_responden_antes_que_el_demo(self):
        from django.urls import resolve

        salida = resolve("/api/v1/practicas/")
        self.assertIn("PracticasListaView", salida.func.view_class.__name__)
