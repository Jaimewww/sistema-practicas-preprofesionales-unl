"""Reconstrucción conservadora de suspensiones desde ``HistorialEstado`` (T15).

La selección de semanas sin reporte (T14) recibe suspensiones explícitas como
intervalos inclusivos. Este módulo las recupera del historial persistido de una
práctica **guardada «en curso»**, leyendo el diario canónico en orden de ``pk``
(el orden en que ocurrieron las transiciones, no el de una fecha editable).

Solo forman un período las aristas ``en_curso → suspendida`` y
``suspendida → en_curso``: la primera fecha es el inicio y la segunda el fin,
ambas inclusivas, convertidas con la zona configurada del proyecto
(``settings.TIME_ZONE``), aunque haya otra zona activa. Las transiciones de
revisión (``en_curso → en_revision_final`` y su regreso) no son suspensiones y
siguen siendo válidas.

El resultado es **conservador**: ``conocida=True`` solo cuando la cadena
completa es canónica y termina en el estado actual. Un historial vacío,
incompleto, discontinuo, con una arista imposible, con un par invertido o que no
coincide con la fila persistida devuelve ``conocida=False``. Ese «desconocido»
**no** equivale a «no hubo suspensiones»: el llamador no debe generar una alerta
que dependa de la ausencia de suspensiones hasta resolver la ambigüedad.

No escribe, no repara ni completa filas históricas, no lee el reloj, no genera
alertas y no toma decisiones de negocio más allá de certificar lo registrado.
"""

from datetime import date
from typing import NamedTuple

from django.utils import timezone

from apps.auditoria.models import HistorialEstado
from apps.practicas.models import Practica
from apps.practicas.services import ARISTAS

Estado = Practica.Estado


class SuspensionesReconstruidas(NamedTuple):
    """Períodos inclusivos recuperados y si el historial los certifica.

    ``conocida`` es ``False`` cuando el historial no alcanza para afirmar nada;
    en ese caso ``periodos`` es la tupla vacía y **no** significa «sin
    suspensiones». Con ``conocida=True``, ``periodos`` puede ser vacío (no hubo
    suspensiones) o una tupla de pares ``(inicio, fin)`` inclusivos en el orden
    del historial.
    """

    conocida: bool
    periodos: tuple[tuple[date, date], ...]


DESCONOCIDO = SuspensionesReconstruidas(conocida=False, periodos=())


def reconstruir_suspensiones(practica: Practica) -> SuspensionesReconstruidas:
    """Recupera los períodos de suspensión de una práctica persistida «en curso».

    Solo se resuelven prácticas guardadas cuyo estado persistido es ``en_curso``
    (CU-03 no evalúa las demás): una instancia sin guardar, una fila inexistente
    o cualquier otro estado devuelven ``DESCONOCIDO`` sin leer el historial. La
    fila actual se lee de la base, no se confía en el objeto del llamador.

    El diario se lee **completo y ordenado por ``pk``**. La primera fila debe ser
    el alta canónica (``estado_anterior`` nulo → ``asignada``); cada fila
    siguiente debe encadenar con la anterior y usar una arista de la tabla
    canónica ``ARISTAS`` de ``practicas.services``. La última fila debe terminar
    en el estado persistido actual. Cualquier ruptura devuelve ``DESCONOCIDO``,
    igual que un par de suspensión sin cierre o con el fin anterior al inicio.

    Cada instante se convierte a fecha con ``timezone.get_default_timezone()``,
    la zona configurada del proyecto, nunca con la zona activa. Los períodos se
    devuelven como pares inclusivos ``(inicio, fin)`` y la función no modifica
    filas ni completa datos faltantes.
    """
    if not getattr(practica, "pk", None):
        return DESCONOCIDO
    estado_actual = (
        Practica.objects.filter(pk=practica.pk).values_list("estado", flat=True).first()
    )
    if estado_actual != Estado.EN_CURSO:
        return DESCONOCIDO
    registros = list(
        HistorialEstado.objects.filter(practica_id=practica.pk)
        .order_by("pk")
        .values_list("estado_anterior", "estado_nuevo", "fecha")
    )
    return _reconstruir(registros, zona=timezone.get_default_timezone())


def _reconstruir(registros, *, zona) -> SuspensionesReconstruidas:
    """Valida la cadena canónica y arma los pares; sin ORM ni reloj."""
    if not registros:
        return DESCONOCIDO
    estado_anterior, estado_nuevo, _ = registros[0]
    if estado_anterior is not None or estado_nuevo != Estado.ASIGNADA:
        return DESCONOCIDO

    previo = estado_nuevo
    abierta: date | None = None
    periodos: list[tuple[date, date]] = []
    for estado_anterior, estado_nuevo, fecha in registros[1:]:
        if estado_anterior != previo:
            return DESCONOCIDO
        if estado_nuevo not in ARISTAS.get(estado_anterior, ()):
            return DESCONOCIDO
        if estado_nuevo == Estado.SUSPENDIDA:
            abierta = timezone.localdate(fecha, zona)
        elif estado_anterior == Estado.SUSPENDIDA and estado_nuevo == Estado.EN_CURSO:
            if abierta is None:
                return DESCONOCIDO
            cierre = timezone.localdate(fecha, zona)
            if cierre < abierta:
                return DESCONOCIDO
            periodos.append((abierta, cierre))
            abierta = None
        previo = estado_nuevo

    if previo != Estado.EN_CURSO or abierta is not None:
        return DESCONOCIDO
    return SuspensionesReconstruidas(conocida=True, periodos=tuple(periodos))
