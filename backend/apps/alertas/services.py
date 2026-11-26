"""Políticas de alertas: rezago por horas, plazo de revisión y su generación (T040-T043).

RF-07 compara, a una fecha dada, las horas validadas más las en revisión contra
el umbral de rezago de las horas esperadas linealmente:

    horas esperadas = horas requeridas × (días transcurridos ÷ días del período)
    horas mínimas   = horas esperadas × (umbral de rezago ÷ 100)
    hay rezago      = horas validadas + horas en revisión < horas mínimas

El ejemplo canónico del spec (240 h en 16 semanas, al cerrar la semana 8) da
120 h esperadas y 96 h mínimas al 80 %: la alerta nace por debajo de 96 h, no al
llegar a 96. La comparación es estricta y se hace con ``Fraction``, sin
redondeo: las horas mínimas fraccionarias no se aproximan.

El plazo de revisión (HU-06 #2, CU-03 «más allá», T041) es la otra regla pura
de este módulo: cuenta los días hábiles entre el ingreso a revisión y la fecha
evaluada y vence cuando son **estrictamente más** que el límite configurado.
El calendario es «lunes a viernes, como en el demo»: sábado y domingo no
cuentan y un feriado entre semana sí.

La convención de días es la de ``Periodo.dias_totales``: el inicio y el fin
cuentan, así que el día 56 del período son 56 días transcurridos. Los días se
acotan al período (antes del inicio son 0 y después del fin son el total), de
modo que un período de 112 días nunca espera más de las horas requeridas.

Este módulo es **política pura y su uso por práctica**: las reglas no leen
``ConfiguracionCarrera``, ni el reloj, ni la base de datos; la fecha de
evaluación, el umbral y los plazos entran como argumentos y los valores por
defecto viven en ``ConfiguracionCarrera`` (80 % de umbral, 5 días hábiles de
revisión). ``generar_alerta_rezago`` conecta la regla de rezago con la
persistencia de una práctica puntual (T043), con la fecha inyectada y sin
ejecución en lote. ``generar_alerta_revision_vencida`` conecta el plazo de
revisión con el ingreso persistido de los reportes de una práctica (T13).
``generar_alerta_reporte_no_enviado`` conecta la selección de semanas vencidas
(T14) y el historial certificado de suspensiones (T15) con la alerta de
``reporte_no_enviado`` de una práctica (T16); el comando diario y la consulta
son T044-T045.
"""

from datetime import date, timedelta
from fractions import Fraction
from typing import NamedTuple

from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.alertas.models import Alerta
from apps.alertas.plazos_reporte import (
    evaluar_plazo_reporte_semanal,
    semanas_sin_reporte_vencidas,
)
from apps.alertas.suspensiones import reconstruir_suspensiones
from apps.carreras.models import ConfiguracionCarrera
from apps.practicas.models import Practica
from apps.reportes.models import ReporteSemanal
from apps.reportes.services import horas_practica

MENSAJE_PERIODO = "La fecha de fin debe ser posterior a la fecha de inicio."
MENSAJE_CONFIGURACION = (
    "No hay una configuración de carrera vigente para esa modalidad: "
    "no se puede evaluar el rezago de la práctica."
)
MENSAJE_CONFIGURACION_REVISION = (
    "No hay una configuración de carrera vigente para esa modalidad: "
    "no se puede evaluar el plazo de revisión de la práctica."
)
MENSAJE_CONFIGURACION_REPORTE = (
    "No hay una configuración de carrera vigente para esa modalidad: "
    "no se puede evaluar el plazo de reporte de la práctica."
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


class EvaluacionPlazoRevision(NamedTuple):
    """Resultado de la regla de plazo de revisión a una fecha.

    ``dias_habiles`` son los días contados en ``(fecha_ingreso, fecha]`` y
    ``vencido`` es la comparación estricta ya resuelta contra el límite.
    """

    dias_habiles: int
    vencido: bool


def evaluar_plazo_revision(
    *, fecha_ingreso: date, fecha: date, plazo_revision_dias: int
) -> EvaluacionPlazoRevision:
    """Evalúa el plazo de revisión de un pendiente, sin efectos ni reloj.

    ``fecha_ingreso`` es la fecha explícita en que el pendiente entró a
    revisión (no se infiere de ``fecha_registro`` ni de otra fecha) y ``fecha``
    la de evaluación. Se cuentan los días **de lunes a viernes** del intervalo
    ``(fecha_ingreso, fecha]``: el día de ingreso no cuenta y la fecha evaluada
    sí. Es el calendario del demo —sábado y domingo no suman—, así que un
    feriado entre semana cuenta como día hábil.

    ``plazo_revision_dias`` es el límite configurado por carrera
    (``ConfiguracionCarrera.plazo_revision_dias``, 5 por defecto). El plazo está
    cumplido solo cuando se cuentan **más** días hábiles que el límite: con 5,
    el quinto día hábil no vence y el sexto sí. Una fecha anterior o igual al
    ingreso no cuenta días y nunca vence (salvo que el límite sea negativo, que
    se toma como dato del llamador; esta función no valida la configuración).

    El conteo es aritmética entera sobre fechas: semanas completas de cinco
    días hábiles más los días sobrantes (a lo sumo seis), sin recorrer rangos
    largos. La función no consulta la base de datos, no lee el reloj, no resuelve
    destinatarios y no crea ni cierra alertas.
    """
    dias_habiles = 0
    if fecha > fecha_ingreso:
        dias_habiles = _dias_habiles(fecha_ingreso + timedelta(days=1), fecha)
    return EvaluacionPlazoRevision(
        dias_habiles=dias_habiles,
        vencido=dias_habiles > plazo_revision_dias,
    )


def _dias_habiles(inicio: date, fin: date) -> int:
    """Días de lunes a viernes en ``[inicio, fin]``, con ``inicio <= fin``.

    Cada bloque de siete días consecutivos aporta exactamente cinco días
    hábiles, empiece el día que empiece; solo los días sobrantes se revisan de
    uno en uno.
    """
    semanas, sobrantes = divmod((fin - inicio).days + 1, 7)
    dias = semanas * 5
    dia_semana = inicio.isoweekday()  # 1 = lunes … 7 = domingo
    for _ in range(sobrantes):
        if dia_semana <= 5:
            dias += 1
        dia_semana = dia_semana % 7 + 1
    return dias


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


def generar_alerta_revision_vencida(
    practica: Practica, *, fecha: date
) -> tuple[Alerta | None, bool]:
    """Genera, si corresponde, la alerta de revisión vencida de ``practica``.

    Devuelve ``(alerta, created)`` como ``generar_alerta_rezago``:
    ``(None, False)`` cuando no hay nada que alertar y ``(alerta, True|False)``
    cuando la causa se creó ahora o ya existía.

    Solo se evalúan prácticas **guardadas «en curso»** y dentro del período
    inclusivo (``fecha_inicio <= fecha <= fecha_fin``); fuera de esa guarda no
    se lee configuración, no se escribe nada y no hay error. Las candidatas son
    solo las de esa práctica con estado «en_revision» e ``ingreso_revision_en``
    conocido: una fila histórica sin ese dato no es candidata y no se infiere de
    ``fecha_registro``. El instante se convierte a fecha en la zona configurada
    del proyecto (``settings.TIME_ZONE``), aunque haya una zona activa distinta,
    antes de aplicar ``evaluar_plazo_revision``.

    Sin candidatas devuelve ``(None, False)`` sin exigir configuración. Con
    candidatas, la configuración vigente se resuelve como en
    ``generar_alerta_rezago``: misma carrera y modalidad, ``vigente_desde`` no
    posterior a ``fecha``, la más reciente y el mayor ``pk`` para desempatar. No
    hay respaldo a otra carrera, otra modalidad ni a una fila futura: sin
    configuración vigente se rechaza con ``ValidationError`` bajo la clave
    «carrera» sin escribir nada.

    Algún reporte vencido produce **una única** alerta activa de tipo
    «revision_pendiente» por práctica, sin identificar un reporte particular.
    La causa se obtiene con ``get_or_create`` sobre ``(practica, tipo,
    atendida=False)``: la unicidad la impone la base, una fila activa existente
    se devuelve sin reescribir su ``fecha`` y una atendida no se reactiva
    —queda como historial y no bloquea una nueva—. Un ``IntegrityError`` ajeno a
    esa unicidad se propaga. La función no cierra alertas, no notifica, no exige
    tutor asignado y no lee el reloj.
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
    ingresos = list(
        ReporteSemanal.objects.filter(
            practica=fila,
            estado=ReporteSemanal.Estado.EN_REVISION,
            ingreso_revision_en__isnull=False,
        ).values_list("ingreso_revision_en", flat=True)
    )
    if not ingresos:
        return None, False
    configuracion = (
        ConfiguracionCarrera.objects.filter(
            carrera=fila.carrera, modalidad=fila.tipo, vigente_desde__lte=fecha
        )
        .order_by("-vigente_desde", "-pk")
        .first()
    )
    if configuracion is None:
        raise ValidationError({"carrera": [MENSAJE_CONFIGURACION_REVISION]})
    vencida = any(
        evaluar_plazo_revision(
            fecha_ingreso=timezone.localdate(ingreso, timezone.get_default_timezone()),
            fecha=fecha,
            plazo_revision_dias=configuracion.plazo_revision_dias,
        ).vencido
        for ingreso in ingresos
    )
    if not vencida:
        return None, False
    return Alerta.objects.get_or_create(
        practica=fila, tipo=Alerta.Tipo.REVISION_PENDIENTE, atendida=False
    )


def generar_alerta_reporte_no_enviado(
    practica: Practica, *, fecha: date
) -> tuple[Alerta | None, bool]:
    """Genera, si corresponde, la alerta de reporte no enviado de ``practica``.

    Devuelve ``(alerta, created)`` como las otras generaciones:
    ``(None, False)`` cuando no hay nada que alertar y ``(alerta, True|False)``
    cuando la causa se creó ahora o ya existía.

    La evaluación, en orden, no lee el reloj y conserva la fecha real de
    creación de la alerta:

    1. **Guarda de estado y período.** Solo la práctica guardada en ``en_curso``
       (manda la fila de la base, no el objeto del llamador) cuyo período incluye
       la fecha, con ambos extremos incluidos. Fuera de la guarda devuelve
       ``(None, False)`` sin leer configuración ni escribir.
    2. **Inicio real.** Sin ``fecha_inicio_real`` no hay calendario y no hay
       alerta: no se sustituye por el inicio del período ni otra fecha. Una
       fecha anterior al inicio real tampoco alerta ni exige configuración.
    3. **Historial certificado.** La reconstrucción de suspensiones debe ser
       ``conocida``. Un historial vacío o incoherente no se lee como «no hubo
       suspensiones»: devuelve ``(None, False)`` sin alerta y sin configuración.
    4. **Semanas completas posibles.** La primera semana cierra el día
       ``inicio + 6``, sin depender del plazo; si aún no cerró ninguna, ninguna
       configuración produce alerta y no se exige.
    5. **Configuración vigente.** La fila de la misma carrera y modalidad con
       ``vigente_desde`` no posterior a la fecha, la más reciente y el mayor
       ``pk`` para desempatar. No hay respaldo: sin configuración vigente se
       lanza ``ValidationError`` bajo la clave «carrera» sin crear filas.
    6. **Semanas elegibles.** ``semanas_sin_reporte_vencidas`` recibe el inicio
       real, la fecha, el ``plazo_reporte_dias`` configurado en días naturales,
       el conjunto de semanas ya reportadas —cualquier estado, porque un
       ``devuelto`` ya fue enviado— y los períodos certificados. No se pasa fin
       real: no está persistido y el fin del período no lo sustituye.
    7. **Causa activa.** Cualquier semana elegida produce **una única** alerta
       activa ``reporte_no_enviado`` por práctica, con ``get_or_create`` sobre
       ``(practica, tipo, atendida=False)``. La unicidad la impone la base, una
       fila activa existente se devuelve sin reescribir su ``fecha`` y una
       atendida no se reactiva. Un ``IntegrityError`` ajeno a esa unicidad se
       propaga: no se confunde con un duplicado.

    La función no cierra alertas, no notifica, no escribe estados ni historial y
    no resuelve destinatarios concretos.
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
    inicio = fila.fecha_inicio_real
    if inicio is None or fecha < inicio:
        return None, False
    historial = reconstruir_suspensiones(fila)
    if not historial.conocida:
        return None, False
    primera_semana = evaluar_plazo_reporte_semanal(
        fecha_inicio_real=inicio,
        numero_semana=1,
        fecha=fecha,
        plazo_reporte_dias=0,
    )
    if primera_semana.fecha_cierre > fecha:
        return None, False
    configuracion = (
        ConfiguracionCarrera.objects.filter(
            carrera=fila.carrera, modalidad=fila.tipo, vigente_desde__lte=fecha
        )
        .order_by("-vigente_desde", "-pk")
        .first()
    )
    if configuracion is None:
        raise ValidationError({"carrera": [MENSAJE_CONFIGURACION_REPORTE]})
    semanas = semanas_sin_reporte_vencidas(
        fecha_inicio_real=inicio,
        fecha=fecha,
        plazo_reporte_dias=configuracion.plazo_reporte_dias,
        semanas_reportadas=set(
            ReporteSemanal.objects.filter(practica=fila).values_list(
                "semana", flat=True
            )
        ),
        suspensiones=historial.periodos,
    )
    if not semanas:
        return None, False
    return Alerta.objects.get_or_create(
        practica=fila, tipo=Alerta.Tipo.REPORTE_NO_ENVIADO, atendida=False
    )
