"""Plazo de reporte de una semana completa faltante (HU-06 #1, RF-07, T12).

Una semana se ancla en la **fecha real de inicio** de la práctica (decisión
``practice_start``): la semana 1 empieza el día del inicio real y cierra seis
días después, la semana 2 a los seis días siguientes y así sucesivamente. La
semana *n* cierra en:

    cierre = fecha_inicio_real + 7n − 1 días

Con un inicio el jueves 9 de abril de 2026, la semana 1 cierra el miércoles 15,
no el domingo: el calendario de semanas no se inventa, se deriva del inicio real.

El plazo de reporte es de **días naturales**, como en el demo
(``hoy > cierre + plazo_reporte_dias``): no se descuentan sábados, domingos ni
feriados.

    último día oportuno = cierre + plazo_reporte_dias
    vencido             = fecha > último día oportuno

``semanas_sin_reporte_vencidas`` compone esta regla con entradas explícitas
(inicio real, fecha, plazo, semanas enviadas, suspensiones y fin real conocido)
para elegir las semanas completas sin reporte, sin renumerar ni examinar una
semana que cierre después de la fecha evaluada o del fin real conocido.

Este módulo sigue siendo **política pura**: recibe fechas, números e intervalos;
no lee el reloj, no consulta la base de datos, no interpreta historial, no
infiere un fin real, no muta sus entradas y no crea ni cierra alertas.
"""

from collections.abc import Collection, Iterable
from datetime import date, timedelta
from typing import NamedTuple

# Mismo texto que ``ReporteSemanal.semana`` (``apps.reportes.models``). Se repite
# aquí para que la política pura no dependa de un módulo de modelos y mantenga
# la convención de ``ValueError`` de las reglas de alertas.
MENSAJE_SEMANA = "La semana del reporte debe ser un número entero positivo."
# Entradas confirmadas: un intervalo invertido o un fin real anterior al inicio
# no describen una práctica real, así que se rechazan en vez de reinterpretarse.
MENSAJE_SUSPENSION = (
    "La fecha de fin de una suspensión no puede ser anterior a su fecha de inicio."
)
MENSAJE_FIN_REAL = (
    "La fecha de fin real no puede ser anterior a la fecha de inicio real."
)
DIAS_POR_SEMANA = 7


class EvaluacionPlazoReporte(NamedTuple):
    """Resultado exacto de la regla para una semana completa a una fecha.

    ``fecha_cierre`` es el último día de la semana *n*, ``ultimo_dia_oportuno``
    agrega el plazo configurado y ``vencido`` es la comparación estricta ya
    resuelta.
    """

    fecha_cierre: date
    ultimo_dia_oportuno: date
    vencido: bool


def evaluar_plazo_reporte_semanal(
    *,
    fecha_inicio_real: date,
    numero_semana: int,
    fecha: date,
    plazo_reporte_dias: int,
) -> EvaluacionPlazoReporte:
    """Evalúa el plazo del reporte de la semana ``numero_semana`` a ``fecha``.

    ``fecha_inicio_real`` es la fecha real de inicio de la práctica
    (``Practica.fecha_inicio_real``), explícita: no se deriva del período, de la
    aprobación del plan ni de otra marca, y no se sustituye por el inicio del
    período. ``numero_semana`` empieza en 1, porque la numeración la aporta
    quien reporta; un valor menor que 1 se rechaza con ``ValueError`` y el
    mensaje de ``ReporteSemanal``.

    ``plazo_reporte_dias`` es el plazo configurado por carrera
    (``ConfiguracionCarrera.plazo_reporte_dias``, 3 por defecto) en **días
    naturales**. Como en ``evaluar_plazo_revision``, esta función no valida la
    configuración: toma el valor que recibe y un 0 significa que el reporte
    vence el día siguiente al cierre.

    Una fecha anterior o igual al cierre no vence; el último día oportuno
    tampoco. La función no consulta la base de datos, no lee el reloj, no
    resuelve destinatarios, no crea ni cierra alertas y no modela semanas
    parciales, suspensión o fin de práctica.
    """
    if numero_semana < 1:
        raise ValueError(MENSAJE_SEMANA)
    fecha_cierre = fecha_inicio_real + timedelta(
        days=DIAS_POR_SEMANA * numero_semana - 1
    )
    ultimo_dia_oportuno = fecha_cierre + timedelta(days=plazo_reporte_dias)
    return EvaluacionPlazoReporte(
        fecha_cierre=fecha_cierre,
        ultimo_dia_oportuno=ultimo_dia_oportuno,
        vencido=fecha > ultimo_dia_oportuno,
    )


class SemanaSinReporte(NamedTuple):
    """Una semana completa, vencida y sin reporte, con su anclaje exacto.

    ``numero_semana`` es el número original, sin renumerar; ``fecha_inicio`` y
    ``fecha_cierre`` delimitan la semana inclusiva y ``ultimo_dia_oportuno`` es
    el cierre más el plazo configurado.
    """

    numero_semana: int
    fecha_inicio: date
    fecha_cierre: date
    ultimo_dia_oportuno: date


def semanas_sin_reporte_vencidas(
    *,
    fecha_inicio_real: date,
    fecha: date,
    plazo_reporte_dias: int,
    semanas_reportadas: Collection[int] = (),
    suspensiones: Iterable[tuple[date, date]] = (),
    fecha_fin_real: date | None = None,
) -> tuple[SemanaSinReporte, ...]:
    """Selecciona las semanas completas vencidas que siguen sin reporte.

    El calendario se ancla en ``fecha_inicio_real`` (decisión ``practice_start``)
    y se numera desde 1 con ``evaluar_plazo_reporte_semanal``, sin reiniciar ni
    renumerar al omitir una semana. Solo se examinan semanas **completas** cuyo
    cierre no sea posterior a ``fecha`` ni a ``fecha_fin_real``: la primera que
    cierre después de cualquiera de esos límites detiene el recorrido, porque los
    cierres son crecientes. Sin ``fecha_fin_real`` no se supone un fin; ese fin es
    el real **conocido**, no el administrativo del período, y no se deriva de otra
    fecha.

    Se omite una semana cuyo número esté en ``semanas_reportadas`` (el conjunto
    explícito de semanas ya enviadas: un reporte ``devuelto`` ya se envió, L28,
    pero interpretar los estados es del llamador) o cuyo intervalo inclusivo
    [inicio, cierre] toque algún intervalo inclusivo de ``suspensiones``: los
    extremos cuentan, así que un día de transición dentro de la semana la omite
    entera (L29). No se interpreta el historial ni se infiere una suspensión.

    Se devuelven solo las ``vencidas`` por la comparación estricta de
    ``evaluar_plazo_reporte_semanal``, en orden ascendente y en una tupla
    inmutable. Validación conservadora previa, independiente de la fecha: un
    intervalo invertido se rechaza con ``ValueError`` (``MENSAJE_SUSPENSION``) y    un ``fecha_fin_real`` anterior al inicio con ``MENSAJE_FIN_REAL``. No hay
    ORM, reloj, escritura, destinatarios ni alertas.
    """
    if fecha_fin_real is not None and fecha_fin_real < fecha_inicio_real:
        raise ValueError(MENSAJE_FIN_REAL)

    intervalos = list(suspensiones)
    if any(fin < inicio for inicio, fin in intervalos):
        raise ValueError(MENSAJE_SUSPENSION)

    seleccionadas: list[SemanaSinReporte] = []
    numero_semana = 1
    while True:
        evaluacion = evaluar_plazo_reporte_semanal(
            fecha_inicio_real=fecha_inicio_real,
            numero_semana=numero_semana,
            fecha=fecha,
            plazo_reporte_dias=plazo_reporte_dias,
        )
        if evaluacion.fecha_cierre > fecha:
            break
        if fecha_fin_real is not None and evaluacion.fecha_cierre > fecha_fin_real:
            break

        fecha_inicio = evaluacion.fecha_cierre - timedelta(days=DIAS_POR_SEMANA - 1)
        superpuesta = any(
            inicio_suspension <= evaluacion.fecha_cierre
            and fecha_inicio <= fin_suspension
            for inicio_suspension, fin_suspension in intervalos
        )
        if (
            evaluacion.vencido
            and numero_semana not in semanas_reportadas
            and not superpuesta
        ):
            seleccionadas.append(
                SemanaSinReporte(
                    numero_semana=numero_semana,
                    fecha_inicio=fecha_inicio,
                    fecha_cierre=evaluacion.fecha_cierre,
                    ultimo_dia_oportuno=evaluacion.ultimo_dia_oportuno,
                )
            )
        numero_semana += 1

    return tuple(seleccionadas)
