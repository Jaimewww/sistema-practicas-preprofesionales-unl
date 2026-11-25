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

Este módulo es **política pura**: recibe el inicio real, el número de semana, la
fecha evaluada y el plazo configurado; no lee el reloj, no consulta la base de
datos, no arma el conjunto de semanas esperadas de una práctica, no decide sobre
semanas parciales, suspensión ni fin de práctica, y no crea ni cierra alertas.
El plazo por defecto (3 días) vive en ``ConfiguracionCarrera.plazo_reporte_dias``
y todavía no está cableado a persistencia ni a la ejecución diaria.
"""

from datetime import date, timedelta
from typing import NamedTuple

# Mismo texto que ``ReporteSemanal.semana`` (``apps.reportes.models``). Se repite
# aquí para que la política pura no dependa de un módulo de modelos y mantenga
# la convención de ``ValueError`` de las reglas de alertas.
MENSAJE_SEMANA = "La semana del reporte debe ser un número entero positivo."
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
