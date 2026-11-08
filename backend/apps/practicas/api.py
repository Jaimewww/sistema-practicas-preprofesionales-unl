"""Endpoints de lectura de prácticas (S2, #78): lista y detalle con alcance de filas.

Solo lectura y solo las filas que ``practicas_visibles_para`` (T019) entrega al
actor guardado: la vista no calcula permisos propios. Al llamar al helper sin
consulta, el alcance parte de todas las prácticas; pasarle una consulta vacía
sigue devolviendo vacío. El detalle de una práctica fuera de su alcance responde
404, igual que una que no existe. La tarjeta expone lo mínimo y nada sensible (sin
motivos ni proyecto).

#79 (D5): el alcance de filas sigue siendo el del helper y encima van los permisos
DRF de ``apps.seguridad`` —toda la API real es auth-first y el permiso de objeto
declara la misma regla en la capa de permisos—, sin reimplementar T019.
"""

from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import generics, serializers

from apps.practicas.models import Practica
from apps.seguridad.permissions import PermitirPracticaVisible, SinFilaEs401
from apps.usuarios.permissions import practicas_visibles_para


class PracticaCardSerializer(serializers.ModelSerializer):
    """Proyección mínima de una práctica: seis campos de solo lectura."""

    estudiante_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Practica
        fields = ("id", "estudiante_id", "tipo", "subtipo", "estado", "horas_requeridas")
        read_only_fields = fields


@extend_schema_view(get=extend_schema(summary="Prácticas visibles para el actor"))
class PracticasListaView(SinFilaEs401, generics.ListAPIView):
    """``GET /api/v1/practicas/``: prácticas visibles del actor (RF-11)."""

    serializer_class = PracticaCardSerializer
    permission_classes = [PermitirPracticaVisible]

    def get_queryset(self):
        return practicas_visibles_para(self.request.user)


@extend_schema_view(
    get=extend_schema(
        summary="Detalle de una práctica visible para el actor",
        responses={
            200: PracticaCardSerializer,
            404: OpenApiResponse(
                description=(
                    "La práctica no existe o está fuera del alcance del actor "
                    "(`no_encontrado`); ambos casos responden igual."
                )
            ),
        },
    )
)
class PracticaDetalleView(SinFilaEs401, generics.RetrieveAPIView):
    """``GET /api/v1/practicas/{id}/``: 404 fuera del alcance o inexistente."""

    serializer_class = PracticaCardSerializer
    permission_classes = [PermitirPracticaVisible]
    lookup_url_kwarg = "practica_id"

    def get_queryset(self):
        return practicas_visibles_para(self.request.user)
