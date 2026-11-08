"""Límite de filas por rol en la consulta de prácticas (T011/T019, RF-11).

Primitive de alcance de filas de data-model.md, solo como límite de filas: los
permisos de acción y endpoints son otras tareas y ninguna vista lo usa aquí.
"""

from apps.practicas.models import AsignacionTutor, Practica
from apps.usuarios.models import Usuario


def practicas_visibles_para(usuario, practicas=None):
    """Filtra ``practicas`` por el rol guardado de ``usuario`` y devuelve un QuerySet.

    ``practicas`` se respeta tal cual cuando no es ``None``: una consulta vacía
    nunca se reemplaza por todas, y la intersección conserva su orden. El rol y la
    carrera se releen de la fila guardada por pk en cada llamada, nunca del objeto
    del llamador: anónimo, no guardado, borrado, inactivo o rol desconocido no ve
    nada; ``is_staff`` e ``is_superuser`` no evitan el filtro.
    """
    consulta = practicas if practicas is not None else Practica.objects.all()
    if not isinstance(usuario, Usuario) or getattr(usuario, "pk", None) is None:
        return consulta.none()
    fila = (
        Usuario.objects.filter(pk=usuario.pk, is_active=True)
        .only("rol", "carrera_id")
        .first()
    )
    if fila is None:
        return consulta.none()
    if fila.rol == Usuario.Rol.ESTUDIANTE:
        return consulta.filter(estudiante_id=fila.pk)
    if fila.rol == Usuario.Rol.TUTOR_ACADEMICO:
        return consulta.filter(
            pk__in=AsignacionTutor.objects.filter(
                tutor_academico_id=fila.pk, hasta__isnull=True
            ).values("practica_id")
        )
    if fila.rol == Usuario.Rol.TUTOR_ENTIDAD:
        return consulta.filter(
            tutor_entidad_id=fila.pk, tipo=Practica.Tipo.LABORAL
        )
    if fila.rol in Usuario.ROLES_CON_CARRERA:
        if fila.carrera_id is None:
            return consulta.none()
        return consulta.filter(carrera_id=fila.carrera_id)
    return consulta.none()
