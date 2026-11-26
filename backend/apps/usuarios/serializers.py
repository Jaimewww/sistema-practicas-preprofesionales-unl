"""Proyección del perfil propio para ``GET /api/v1/me/`` (S7).

Lista cerrada de campos: lo que el front necesita para el menú por rol. La
contraseña, las banderas de privilegio, los grupos y los permisos no salen nunca;
``carrera`` es el id de la FK tal como lo guarda el modelo (``null`` en los roles
sin carrera).
"""

from rest_framework import serializers

from apps.usuarios.models import Usuario


class UsuarioActualSerializer(serializers.ModelSerializer):
    """Cinco campos de solo lectura del usuario autenticado."""

    carrera = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)

    class Meta:
        model = Usuario
        fields = ("id", "nombre", "email", "rol", "carrera")
        read_only_fields = fields
