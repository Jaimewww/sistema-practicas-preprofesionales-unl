"""Política pura de rezago por horas (HU-06, CU-03, T040).

RF-07 compara, a una fecha dada, las horas validadas más las en revisión contra
el umbral de rezago de las horas esperadas linealmente:

    horas esperadas = horas requeridas × (días transcurridos ÷ días del período)
    horas mínimas   = horas esperadas × (umbral de rezago ÷ 100)
    hay rezago      = horas validadas + horas en revisión < horas mínimas

El ejemplo canónico del spec (240 h en 16 semanas, al cerrar la semana 8) da
120 h esperadas y 96 h mínimas al 80 %: la alerta nace por debajo de 96 h, no al
llegar a 96. La comparación es estricta y se hace con ``Fraction``, sin
redondeo: las horas mínimas fraccionarias no se aproximan.

La convención de días es la de ``Periodo.dias_totales``: el inicio y el fin
cuentan, así que el día 56 del período son 56 días transcurridos. Los días se
acotan al período (antes del inicio son 0 y después del fin son el total), de
modo que un período de 112 días nunca espera más de las horas requeridas.

Esta unidad es **solo la política matemática**: no lee ``ConfiguracionCarrera``
ni el reloj, no consulta ni escribe la base de datos, no crea ``Alerta`` ni
notifica a nadie. La fecha de evaluación y el umbral entran como argumentos; el
80 % por defecto vive en ``ConfiguracionCarrera.umbral_rezago`` (T042-T045
conectan esta regla con la persistencia, la ejecución diaria y la consulta).
"""

from datetime import date
from fractions import Fraction
from typing import NamedTuple

MENSAJE_PERIODO = "La fecha de fin debe ser posterior a la fecha de inicio."


class EvaluacionRezago(NamedTuple):
    """Resultado exacto de la regla para una práctica a una fecha.

    ``horas_esperadas`` y ``horas_minimas`` son ``Fraction`` para no perder
    exactitud; ``en_rezago`` es la comparación estricta ya resuelta.
    """

    horas_esperadas: Fraction
    horas_minimas: Fraction
    en_rezago: bool


def evaluar_rezago(
    *,
    horas_requeridas: int,
    horas_validadas: int,
    horas_en_revision: int,
    fecha_inicio: date,
    fecha_fin: date,
    fecha: date,
    umbral_rezago: int,
) -> EvaluacionRezago:
    """Evalúa el rezago de una práctica a ``fecha`` sin efectos ni reloj.

    ``umbral_rezago`` es el porcentaje configurado (``ConfiguracionCarrera``,
    80 por defecto), no un valor fijo de esta función. ``horas_validadas`` y
    ``horas_en_revision`` son los dos saldos que CU-03 suma; un reporte devuelto
    no entra en ninguno.

    Un período con ``fecha_fin`` no posterior a ``fecha_inicio`` es inválido y
    se rechaza: es la misma regla que impone ``Periodo`` y evita dividir por
    cero. No se valida nada más.
    """
    if fecha_fin <= fecha_inicio:
        raise ValueError(MENSAJE_PERIODO)

    dias_totales = (fecha_fin - fecha_inicio).days + 1
    dias_transcurridos = min(max((fecha - fecha_inicio).days + 1, 0), dias_totales)

    horas_esperadas = Fraction(horas_requeridas * dias_transcurridos, dias_totales)
    horas_minimas = horas_esperadas * Fraction(umbral_rezago) / 100
    acumuladas = Fraction(horas_validadas) + Fraction(horas_en_revision)

    return EvaluacionRezago(
        horas_esperadas=horas_esperadas,
        horas_minimas=horas_minimas,
        en_rezago=acumuladas < horas_minimas,
    )
