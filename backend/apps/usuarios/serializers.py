"""Proyección del perfil propio para ``GET /api/v1/me/`` (S7).

Lista cerrada de campos: lo que el front necesita para el menú por rol. La
contraseña, las banderas de privilegio, los grupos y los permisos no salen nunca;
``carrera`` es el id de la FK tal como lo guarda el modelo (``null`` en los roles
sin carrera).
"""

from rest_framework import serializers


# Es un ``Serializer`` explícito y no un ``ModelSerializer`` por la misma razón
# que ``ReporteSemanalSerializer``: el ``Meta`` anidado de ``ModelSerializer``
# solo existe en los stubs de DRF y el checker lo trata como un reemplazo
# incompatible. El payload no cambia: ``carrera`` sigue siendo el ``id`` de la
# FK tal como lo guarda el modelo (``null`` en los roles sin carrera).
class UsuarioActualSerializer(serializers.Serializer):
    """Cinco campos de solo lectura del usuario autenticado."""

    id = serializers.IntegerField(read_only=True)
    nombre = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    rol = serializers.CharField(read_only=True)
    carrera = serializers.IntegerField(
        source="carrera_id", read_only=True, allow_null=True
    )
