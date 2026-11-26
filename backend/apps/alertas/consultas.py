"""Consulta de alertas activas para el destinatario (T17, T045, HU-06).

``alertas_visibles_para`` es la base de solo lectura de la vista de T045 (CE-04):
cruza el alcance de filas de ``practicas_visibles_para`` (T019) con el mapeo de
destinatarios por tipo de ``DESTINATARIOS_POR_TIPO`` (HU-06) y devuelve las
alertas **activas** que le corresponden al usuario.

El alcance de filas es la regla existente, no una copia: el estudiante llega a
sus prácticas, el tutor académico a la práctica con asignación **vigente**
(``hasta`` nulo; un tutor anterior no conserva acceso) y el coordinador a las de
su carrera. El rol y el estado se releen de la fila guardada, de modo que una
cuenta anónima, sin guardar, borrada, inactiva o con un rol sin destinatario no
ve nada; ``is_staff`` e ``is_superuser`` no abren el alcance.

No escribe, no resuelve el historial de alertas atendidas, no notifica, no
interpreta encabezados del prototipo y no depende de la petición HTTP: devuelve
un ``QuerySet`` de ``Alerta`` para que la vista lo consuma.
"""

from apps.alertas.models import DESTINATARIOS_POR_TIPO, Alerta
from apps.usuarios.permissions import rol_y_practicas_visibles_para

# ``fecha`` es un ``DateField`` y varias alertas pueden compartir el día; el
# ``pk`` desempata para que el orden sea estable entre consultas.
ORDEN_ALERTAS = ("-fecha", "-pk")


def alertas_visibles_para(usuario):
    """Devuelve las alertas activas que ``usuario`` puede ver, ya ordenadas.

    ``usuario`` aporta solo su ``pk``. Una lectura de la fila guardada fija
    el rol activo y el alcance, sin mezclar autoridades de distintas lecturas.
    Los tipos se limitan a aquellos cuyo ``DESTINATARIOS_POR_TIPO`` incluye ese rol. Sin rol
    guardado, o con un rol que no es destinatario de ningún tipo —``director``,
    ``secretaria`` o ``tutor_entidad``, por ejemplo—, el resultado es vacío
    incluso si el alcance de filas incluyera la práctica.

    Solo se devuelven alertas ``atendida=False`` y de prácticas dentro de
    ese alcance. El orden es ``-fecha`` y, para el
    empate, ``-pk``. La función no escribe ni modifica la alerta ni la práctica.
    """
    rol, practicas = rol_y_practicas_visibles_para(usuario)
    if rol is None:
        return Alerta.objects.none()
    tipos = tuple(
        tipo
        for tipo, destinatarios in DESTINATARIOS_POR_TIPO.items()
        if rol in destinatarios
    )
    if not tipos:
        return Alerta.objects.none()
    return Alerta.objects.filter(
        atendida=False,
        tipo__in=tipos,
        practica__in=practicas,
    ).order_by(*ORDEN_ALERTAS)
