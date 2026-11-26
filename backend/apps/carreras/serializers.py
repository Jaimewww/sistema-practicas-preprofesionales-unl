"""Serializers del endpoint de configuración por carrera (RF-12, C-17, D1).

Entrada: **una** modalidad por llamada (D1) con sus horas, sus plazos, su umbral
y la fecha desde la que rige. El serializer es estricto como
``EnvioPlanSerializer``: un cuerpo que no es objeto y cualquier clave que no sea
del contrato —incluidas las que fija el servidor— son un 400 con su clave, nunca
un campo ignorado. Los rangos de S3/S5 se validan acá para que el rechazo llegue
en el campo correcto: ``horas_requeridas`` > 0, ``umbral_rezago`` en 0–100 y
plazos sin valores negativos.

Salida: la fila guardada con el código de su carrera (``carrera``), la modalidad,
los cuatro números y ``vigente_desde``.
"""

from collections.abc import Mapping
from typing import Any, cast

from rest_framework import serializers
from rest_framework.settings import api_settings

from apps.carreras.models import ConfiguracionCarrera

MENSAJE_CUERPO_CONFIGURACION = (
    "El cuerpo debe ser un objeto JSON con «modalidad», «horas_requeridas», "
    "«plazo_reporte_dias», «plazo_revision_dias», «umbral_rezago» y "
    "«vigente_desde»."
)
MENSAJE_CAMPO_NO_ADMITIDO_CONFIGURACION = (
    "Campo no admitido: la configuración solo envía «modalidad», "
    "«horas_requeridas», «plazo_reporte_dias», «plazo_revision_dias», "
    "«umbral_rezago» y «vigente_desde»."
)
MENSAJE_HORAS_REQUERIDAS = "Las horas requeridas deben ser mayores que cero."
MENSAJE_PLAZOS = "Los plazos se miden en días y no admiten valores negativos."
MENSAJE_UMBRAL_REZAGO = "El umbral de rezago es un porcentaje entre 0 y 100."
MENSAJE_MODALIDAD = "La modalidad debe ser «laboral» o «comunitaria»."
MENSAJE_VIGENTE_DESDE = (
    "La fecha de vigencia es obligatoria y debe ser una fecha sin hora (AAAA-MM-DD)."
)


def _mensajes(texto, claves):
    """Un mismo texto para las claves de error que el campo puede devolver."""
    return {clave: texto for clave in claves}


class ConfiguracionCarreraEntradaSerializer(serializers.Serializer):
    """Entrada del ``PUT``: una modalidad y sus cuatro números por llamada (D1)."""

    modalidad = serializers.ChoiceField(
        choices=ConfiguracionCarrera.Modalidad.choices,
        error_messages=_mensajes(
            MENSAJE_MODALIDAD,
            ("required", "null", "invalid_choice", "incorrect_type"),
        ),
    )
    horas_requeridas = serializers.IntegerField(
        min_value=1,
        error_messages=_mensajes(
            MENSAJE_HORAS_REQUERIDAS, ("required", "null", "invalid", "min_value")
        ),
    )
    plazo_reporte_dias = serializers.IntegerField(
        min_value=0,
        error_messages=_mensajes(
            MENSAJE_PLAZOS, ("required", "null", "invalid", "min_value")
        ),
    )
    plazo_revision_dias = serializers.IntegerField(
        min_value=0,
        error_messages=_mensajes(
            MENSAJE_PLAZOS, ("required", "null", "invalid", "min_value")
        ),
    )
    umbral_rezago = serializers.IntegerField(
        min_value=0,
        max_value=100,
        error_messages=_mensajes(
            MENSAJE_UMBRAL_REZAGO,
            ("required", "null", "invalid", "min_value", "max_value"),
        ),
    )
    vigente_desde = serializers.DateField(
        error_messages=_mensajes(
            MENSAJE_VIGENTE_DESDE, ("required", "null", "invalid")
        ),
    )

    def to_internal_value(self, data: object) -> dict:
        """Acepta solo un objeto JSON con las seis claves del contrato.

        ``data`` es el cuerpo crudo: puede ser una lista, un texto o un número, y
        por eso entra como ``object`` y se estrecha acá. Una clave de más —también
        las que fija el servidor— se rechaza en su clave y nunca se ignora.
        """
        if not isinstance(data, Mapping):
            raise serializers.ValidationError(
                {str(api_settings.NON_FIELD_ERRORS_KEY): [MENSAJE_CUERPO_CONFIGURACION]}
            )
        sobrantes = sorted(set(data) - set(self.fields))
        if sobrantes:
            raise serializers.ValidationError(
                {
                    campo: [MENSAJE_CAMPO_NO_ADMITIDO_CONFIGURACION]
                    for campo in sobrantes
                }
            )
        return super().to_internal_value(data)

    def datos(self) -> dict[str, Any]:
        """Las seis claves ya validadas, en el orden del contrato.

        DRF no declara el tipo de ``validated_data``: el ``cast`` documenta el
        valor dinámico que ya validaron los campos y evita tipar de más la mezcla
        de DRF con las anotaciones del proyecto.
        """
        return dict(cast("dict[str, Any]", self.validated_data))


class ConfiguracionCarreraSerializer(serializers.Serializer):
    """Respuesta: la fila guardada, con el código de su carrera y sus números."""

    # DRF deriva la PK del modelo (``BigAutoField``) como ``BigIntegerField`` con
    # etiqueta «ID»; se declara igual para conservar el campo tal cual.
    id = serializers.BigIntegerField(read_only=True, label="ID")
    carrera = serializers.SerializerMethodField()
    modalidad = serializers.ChoiceField(
        choices=ConfiguracionCarrera.Modalidad.choices, read_only=True
    )
    horas_requeridas = serializers.IntegerField(read_only=True)
    plazo_reporte_dias = serializers.IntegerField(read_only=True)
    plazo_revision_dias = serializers.IntegerField(read_only=True)
    umbral_rezago = serializers.IntegerField(read_only=True)
    vigente_desde = serializers.DateField(read_only=True)

    def get_carrera(self, configuracion) -> str:
        """El ``codigo`` de la carrera, que es la clave de la ruta y del contrato."""
        return configuracion.carrera.codigo
