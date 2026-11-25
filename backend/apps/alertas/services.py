"""Política de rezago por horas y su generación por práctica (HU-06, CU-03, T040, T043).

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

Esta unidad es **solo la política matemática y su uso por práctica**: la regla
no lee ``ConfiguracionCarrera``, ni el reloj, ni la base de datos; la fecha de
evaluación y el umbral entran como argumentos y el 80 % por defecto vive en
``ConfiguracionCarrera.umbral_rezago``. ``generar_alerta_rezago`` conecta esa
regla con la persistencia de una práctica puntual (T043), con la fecha inyectada
y sin ejecución en lote; los plazos, el comando diario y la consulta son
T044-T045.
"""

from datetime import date
from fractions import Fraction
from typing import NamedTuple

from django.core.exceptions import ValidationError

from apps.alertas.models import Alerta
from apps.carreras.models import ConfiguracionCarrera
from apps.practicas.models import Practica
from apps.reportes.services import horas_practica

MENSAJE_PERIODO = "La fecha de fin debe ser posterior a la fecha de inicio."
MENSAJE_CONFIGURACION = (
    "No hay una configuración de carrera vigente para esa modalidad: "
    "no se puede evaluar el rezago de la práctica."
)


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


def generar_alerta_rezago(
    practica: Practica, *, fecha: date
) -> tuple[Alerta | None, bool]:
    """Genera, si corresponde, la alerta activa de rezago de ``practica`` a ``fecha``.

    Devuelve ``(alerta, created)``: ``(None, False)`` cuando no hay nada que
    alertar y ``(alerta, True|False)`` cuando la causa ya existía (``False``)
    o se creó ahora (``True``).

    Solo se evalúan prácticas **guardadas «en curso»** y dentro del período
    inclusivo de la práctica (``fecha_inicio <= fecha <= fecha_fin``); fuera de
    esa guarda no se lee configuración, no se escribe nada y no hay error. La
    configuración vigente se resuelve como en ``practicas.services``: la fila de
    la misma carrera y modalidad con ``vigente_desde`` no posterior a ``fecha``,
    la más reciente primero y la de mayor ``pk`` para desempatar. No hay respaldo
    a otra carrera, otra modalidad ni a una fila futura: sin configuración
    vigente se rechaza con ``ValidationError`` bajo la clave «carrera» sin
    escribir nada.

    Las horas salen de ``horas_practica`` —validadas más en revisión; un devuelto
    no suma— y las requeridas de la práctica, no de la configuración. La causa
    activa se obtiene con ``get_or_create`` sobre ``(practica, tipo, atendida=False)``:
    la unicidad la impone la base, una fila activa existente se devuelve sin
    reescribir su ``fecha`` y una atendida no bloquea una nueva. Un
    ``IntegrityError`` ajeno a esa unicidad se propaga: no se confunde con un
    duplicado. La función no resuelve alertas, no notifica y no lee el reloj;
    ``Alerta.fecha`` sigue siendo la fecha real de creación.
    """
    fila = None
    if getattr(practica, "pk", None):
        fila = (
            Practica.objects.select_related("periodo", "carrera")
            .filter(pk=practica.pk)
            .first()
        )
    if fila is None or fila.estado != Practica.Estado.EN_CURSO:
        return None, False
    periodo = fila.periodo
    if not periodo.fecha_inicio <= fecha <= periodo.fecha_fin:
        return None, False
    configuracion = (
        ConfiguracionCarrera.objects.filter(
            carrera=fila.carrera, modalidad=fila.tipo, vigente_desde__lte=fecha
        )
        .order_by("-vigente_desde", "-pk")
        .first()
    )
    if configuracion is None:
        raise ValidationError({"carrera": [MENSAJE_CONFIGURACION]})
    resumen = horas_practica(fila)
    evaluacion = evaluar_rezago(
        horas_requeridas=resumen["horas_requeridas"],
        horas_validadas=resumen["horas_validadas"],
        horas_en_revision=resumen["horas_en_revision"],
        fecha_inicio=periodo.fecha_inicio,
        fecha_fin=periodo.fecha_fin,
        fecha=fecha,
        umbral_rezago=configuracion.umbral_rezago,
    )
    if not evaluacion.en_rezago:
        return None, False
    return Alerta.objects.get_or_create(
        practica=fila, tipo=Alerta.Tipo.REZAGO, atendida=False
    )
