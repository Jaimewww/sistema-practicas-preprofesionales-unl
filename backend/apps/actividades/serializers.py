"""Serializers del plan de actividades para la API (S8).

``PlanActividadesSerializer`` es la salida: la versión del plan con su estado y,
si el tutor ya decidió, la observación y la fecha de esa ``Validacion`` (el plan
no guarda fechas propias). ``EnvioPlanSerializer`` es la entrada del estudiante:
exactamente ``contenido``; un cuerpo que no es objeto o un campo de más (``version``,
``estado``…, que decide el servicio) es un 400, nunca se ignora.
"""

from collections.abc import Mapping

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.settings import api_settings

MENSAJE_CUERPO_PLAN = "El cuerpo debe ser un objeto JSON con «contenido»."
MENSAJE_CAMPO_NO_ADMITIDO = "Campo no admitido: el plan solo envía «contenido»."
MENSAJE_CAMPO_NO_ADMITIDO_DEVOLVER = (
    "Campo no admitido: la devolución solo envía «observacion»."
)
MENSAJE_CONTENIDO = "El contenido del plan es obligatorio y no puede estar vacío."


def ultima_validacion(plan):
    """La decisión más reciente del plan, o ``None``; usa el prefetch si lo hay."""
    validaciones = list(plan.validaciones.all())
    if not validaciones:
        return None
    return max(validaciones, key=lambda validacion: (validacion.fecha, validacion.pk))


# Es un ``Serializer`` explícito y no un ``ModelSerializer`` por la misma razón que
# ``ReporteSemanalSerializer``: el ``Meta`` anidado de ``ModelSerializer`` solo
# existe en los stubs de DRF y el checker lo trata como un reemplazo
# incompatible. Los campos replican la proyección del ``ModelSerializer``
# original; la lectura y el OpenAPI no cambian.
class PlanActividadesSerializer(serializers.Serializer):
    """Versión del plan y su última decisión; todo de solo lectura."""

    id = serializers.IntegerField(read_only=True)
    practica_id = serializers.IntegerField(read_only=True)
    version = serializers.IntegerField(read_only=True)
    contenido = serializers.CharField(read_only=True)
    estado = serializers.CharField(read_only=True)
    observacion = serializers.SerializerMethodField()
    fecha_validacion = serializers.SerializerMethodField()

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_observacion(self, plan):
        validacion = ultima_validacion(plan)
        return None if validacion is None else validacion.observacion

    @extend_schema_field(OpenApiTypes.DATETIME)
    def get_fecha_validacion(self, plan):
        validacion = ultima_validacion(plan)
        if validacion is None:
            return None
        return serializers.DateTimeField().to_representation(validacion.fecha)


class EnvioPlanSerializer(serializers.Serializer):
    """Entrada de ``POST …/plan/``: solo ``contenido``, texto no vacío."""

    contenido = serializers.CharField(
        error_messages={
            clave: MENSAJE_CONTENIDO for clave in ("required", "blank", "null", "invalid")
        }
    )

    def to_internal_value(self, data):
        if not isinstance(data, Mapping):
            raise serializers.ValidationError(
                {api_settings.NON_FIELD_ERRORS_KEY: [MENSAJE_CUERPO_PLAN]}
            )
        sobrantes = sorted(set(data) - set(self.fields))
        if sobrantes:
            raise serializers.ValidationError(
                {campo: [MENSAJE_CAMPO_NO_ADMITIDO] for campo in sobrantes}
            )
        return super().to_internal_value(data)
