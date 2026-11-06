"""Permisos DRF por rol y por objeto (#79, S3-S4) sobre el alcance de filas de T019.

Dos piezas, y ninguna reimplementa el alcance de filas:

* ``rol_requerido(*roles)`` — fábrica de permisos de rol para la vista. El rol se
  relee de la fila guardada y activa por ``pk`` en cada llamada: el objeto del
  llamador no decide, e ``is_staff``/``is_superuser`` no abren nada.
* ``PermitirObjetoAlDueno`` — permiso por objeto y de entrada: la entrada exige
  una cuenta guardada y activa; el objeto se decide con ``practicas_visibles_para``
  (T019) acotado al ``pk`` pedido, así que el estudiante solo alcanza sus
  prácticas y el tutor solo las asignadas, con la misma semántica que la consulta.

Se usan como clases DRF en ``permission_classes``; el envelope 401/403 es de
``apps.contrato`` (#77) y no se duplica aquí.
"""

from rest_framework.permissions import BasePermission

from apps.practicas.models import Practica
from apps.usuarios.models import Usuario
from apps.usuarios.permissions import practicas_visibles_para


def rol_guardado(usuario):
    """Rol de la fila guardada y activa de ``usuario``, o ``None`` si no hay fila."""
    if not isinstance(usuario, Usuario) or getattr(usuario, "pk", None) is None:
        return None
    fila = Usuario.objects.filter(pk=usuario.pk, is_active=True).only("rol").first()
    return None if fila is None else fila.rol


class RolRequerido(BasePermission):
    """Entra solo quien tiene uno de los roles declarados en ``roles``."""

    roles = frozenset()

    def has_permission(self, request, view):
        return rol_guardado(getattr(request, "user", None)) in self.roles


def rol_requerido(*roles):
    """Devuelve la clase de permiso que exige alguno de ``roles``.

    Un rol fuera de ``Usuario.Rol`` (o una lista vacía) es un error de programa,
    no un permiso: falla al construirse en vez de dejar pasar a nadie.
    """
    nombres = frozenset(roles)
    desconocidos = nombres - frozenset(Usuario.Rol.values)
    if not nombres:
        raise ValueError("rol_requerido necesita al menos un rol.")
    if desconocidos:
        raise ValueError(f"Roles desconocidos: {sorted(desconocidos)}.")
    sufijo = "".join(
        parte.title().replace("_", "") for parte in sorted(nombres)
    )
    return type(f"RolRequerido{sufijo}", (RolRequerido,), {"roles": nombres})


class PermitirObjetoAlDueno(BasePermission):
    """El objeto se permite solo si el alcance de filas de T019 lo incluye."""

    def has_permission(self, request, view):
        return rol_guardado(getattr(request, "user", None)) is not None

    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Practica) or obj.pk is None:
            return False
        # ``practicas_visibles_para`` acotado al objeto: una sola existencia, sin
        # traer el alcance completo a memoria.
        return practicas_visibles_para(request.user).filter(pk=obj.pk).exists()
