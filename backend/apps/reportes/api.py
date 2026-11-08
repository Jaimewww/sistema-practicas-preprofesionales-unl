"""Endpoint de registro del reporte semanal (S2-S5, #78).

``POST /api/v1/practicas/{id}/reportes/`` es el único camino de escritura de esta
unidad y decide en este orden, sin escribir nada hasta el final:

1. sin actor guardado y activo -> 401; actor que no es estudiante -> 403;
2. la práctica se busca **dentro de la transacción**, con ``select_for_update`` y
   solo entre las del propio estudiante: la inexistente y la ajena dan el mismo 404
   (sin fuga de existencia);
3. solo una práctica «en curso» admite reportes (eso implica plan aprobado y excluye
   asignada, suspendida, revisión final y los estados finales) -> 409
   ``practica_no_en_curso``;
4. validación del cuerpo (400) y semana ya reportada -> 409 ``semana_duplicada``.

La restricción única de la base es la última red de la semana duplicada: solo ese
``IntegrityError`` se traduce a 409; cualquier otro se relanza (500 genérico). El
envelope y los códigos de error vienen de #77.

S5: la ayudantía con más de 10 horas se rechaza con el mensaje del Art. 341 (lo
hace el serializer). La práctica laboral o comunitaria con más de 40 horas **se
acepta** y queda marcada con ``requiere_revision`` para el tutor (ver README).

#79 (D5): la vista declara permisos DRF —rol estudiante y objeto dentro del
alcance de T019— y conserva el chequeo explícito de actor y de dueño (la búsqueda
acotada a las prácticas del estudiante) como segunda barrera; el alcance de filas
no se reimplementa. La práctica ajena sigue dando el mismo 404 que la inexistente
(decisión de #101): el permiso de objeto nunca la ve, porque la búsqueda ya la excluye.
"""

from django.db import IntegrityError, transaction
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.practicas.models import Practica
from apps.reportes.models import MENSAJE_SEMANA_DUPLICADA, ReporteSemanal
from apps.reportes.serializers import ReporteSemanalSerializer
from apps.seguridad.permissions import (
    PermitirPracticaVisible,
    SinFilaEs401,
    rol_requerido,
)
from apps.usuarios.models import Usuario

MENSAJE_ACTOR = "Solo el estudiante de la práctica puede registrar sus reportes semanales."
MENSAJE_NO_EN_CURSO = (
    "La práctica está en «{estado}»: solo una práctica en curso admite reportes semanales."
)
RESTRICCION_SEMANA_UNICA = "reportes_reporte_semana_unica"
# SQLite no nombra la restricción: informa las columnas de la clave única.
COLUMNAS_SEMANA_UNICA = (
    "reportes_reportesemanal.practica_id",
    "reportes_reportesemanal.semana",
)


class PracticaNoEnCurso(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "practica_no_en_curso"


class SemanaDuplicada(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = MENSAJE_SEMANA_DUPLICADA
    default_code = "semana_duplicada"


def actor_estudiante(usuario):
    """Estudiante activo desde la fila guardada; el objeto del llamador no decide."""
    if not isinstance(usuario, Usuario) or getattr(usuario, "pk", None) is None:
        raise NotAuthenticated()
    fila = Usuario.objects.filter(pk=usuario.pk, is_active=True).only("rol").first()
    if fila is None:
        raise NotAuthenticated()
    if fila.rol != Usuario.Rol.ESTUDIANTE:
        raise PermissionDenied(MENSAJE_ACTOR)
    return fila


def semana_ya_reportada(practica, semana):
    return ReporteSemanal.objects.filter(practica=practica, semana=semana).exists()


def es_semana_unica(error):
    """¿Este ``IntegrityError`` es la restricción de semana única y no otra?"""
    nombre = getattr(getattr(error.__cause__, "diag", None), "constraint_name", None)
    texto = str(error)
    return (
        nombre == RESTRICCION_SEMANA_UNICA
        or RESTRICCION_SEMANA_UNICA in texto
        or all(columna in texto for columna in COLUMNAS_SEMANA_UNICA)
    )


class ReportePracticaView(SinFilaEs401, APIView):
    """Registra el reporte semanal de la práctica; solo su propio estudiante."""

    # #79: permiso de rol (solo estudiante registra reportes) y de objeto con el
    # alcance de T019; los chequeos explícitos de abajo quedan como segunda
    # barrera (D5, defensa en profundidad).
    permission_classes = [
        rol_requerido(Usuario.Rol.ESTUDIANTE, mensaje=MENSAJE_ACTOR),
        PermitirPracticaVisible,
    ]

    @extend_schema(
        summary="Registrar el reporte semanal de una práctica",
        request=ReporteSemanalSerializer,
        responses={
            201: ReporteSemanalSerializer,
            400: OpenApiResponse(
                description=(
                    "Validación de la entrada: cuerpo que no es objeto, campo no "
                    "admitido, semana u horas inválidas (máximo 168 por semana) o "
                    "ayudantía con más de 10 horas."
                )
            ),
            401: OpenApiResponse(description="Sin actor autenticado (`no_autenticado`)."),
            403: OpenApiResponse(
                description="El actor no es estudiante (`permiso_denegado`)."
            ),
            404: OpenApiResponse(
                description=(
                    "La práctica no existe o no es del estudiante (`no_encontrado`); "
                    "ambos casos responden igual."
                )
            ),
            409: OpenApiResponse(
                description=(
                    "La práctica no está en curso (`practica_no_en_curso`) o la "
                    "semana ya tiene reporte (`semana_duplicada`)."
                )
            ),
        },
    )
    def post(self, request, practica_id):
        actor = actor_estudiante(request.user)
        with transaction.atomic():
            practica = (
                Practica.objects.select_for_update()
                .filter(pk=practica_id, estudiante_id=actor.pk)
                .first()
            )
            if practica is None:
                raise NotFound()
            self.check_object_permissions(request, practica)
            if practica.estado != Practica.Estado.EN_CURSO:
                raise PracticaNoEnCurso(MENSAJE_NO_EN_CURSO.format(estado=practica.estado))
            serializer = ReporteSemanalSerializer(
                data=request.data, context={"practica": practica}
            )
            serializer.is_valid(raise_exception=True)
            if semana_ya_reportada(practica, serializer.validated_data["semana"]):
                raise SemanaDuplicada()
            try:
                with transaction.atomic():
                    reporte = serializer.save(practica=practica)
            except IntegrityError as error:
                if not es_semana_unica(error):
                    raise
                raise SemanaDuplicada() from None
        return Response(
            ReporteSemanalSerializer(reporte).data, status=status.HTTP_201_CREATED
        )
