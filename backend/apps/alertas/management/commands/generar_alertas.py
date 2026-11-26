"""Genera las alertas diarias de todas las prácticas «en curso» (T044, RF-07).

Uso::

    DJANGO_SECRET_KEY=<clave> python manage.py generar_alertas --fecha 2026-03-20

El comando es el lote diario de HU-06 y CU-03: recorre las prácticas
**guardadas «en curso»** cuyo período incluye ``--fecha`` (ambos extremos
incluidos) y les aplica, una por una, los tres generadores de
``apps.alertas.services``: rezago, revisión vencida y reporte no enviado.

``--fecha`` es obligatoria y se escribe en ISO (``AAAA-MM-DD``). Ningún servicio
lee el reloj: quien programa el comando en cron decide la fecha evaluada, así
que una corrida repetida puede evaluarse con la misma fecha sin adivinar el día.
``Alerta.fecha`` sigue siendo la fecha real de creación de la alerta.

Política del lote, sin reglas nuevas:

- **Alcance.** Solo prácticas persistidas ``en_curso`` con la fecha dentro de su
  período. Las demás no se evalúan: no reciben alertas y no aparecen en el
  resumen.
- **Idempotencia.** Cada generador usa ``get_or_create`` sobre la causa activa
  ``(práctica, tipo, atendida=False)``, así que repetir la corrida con la misma
  fecha no duplica alertas: las que ya existían se cuentan como existentes y no
  se reescriben.
- **Configuración faltante.** Si falta la ``ConfiguracionCarrera`` vigente de una
  práctica, el generador lanza ``ValidationError`` bajo la clave «carrera». El
  comando **no** aborta el lote: informa esa práctica en una línea
  ``Práctica <pk>: <mensaje>``, cuenta el error en el resumen y sigue con las
  demás. Los errores de configuración no son alertas: no se escriben filas.
- **Resumen.** Al final escribe en la salida estándar, siempre y en este orden,
  las cuatro líneas de conteo del lote.

No resuelve alertas atendidas, no notifica, no toca destinatarios y no decide
reemplazos ni reagendamientos: eso queda fuera de T044.
"""

from datetime import date

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from apps.alertas.services import (
    generar_alerta_reporte_no_enviado,
    generar_alerta_revision_vencida,
    generar_alerta_rezago,
)
from apps.practicas.models import Practica

GENERADORES = (
    generar_alerta_rezago,
    generar_alerta_revision_vencida,
    generar_alerta_reporte_no_enviado,
)


class Command(BaseCommand):
    help = (
        "Genera las alertas de rezago, revisión pendiente y reporte no enviado "
        "de las prácticas en curso a la fecha indicada."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fecha",
            required=True,
            type=date.fromisoformat,
            help=(
                "Fecha de evaluación en formato ISO (AAAA-MM-DD). Es obligatoria "
                "porque los servicios no leen el reloj."
            ),
        )

    def handle(self, *args, **options):
        fecha = options["fecha"]
        evaluadas = creadas = existentes = errores = 0
        practicas = Practica.objects.filter(
            estado=Practica.Estado.EN_CURSO,
            periodo__fecha_inicio__lte=fecha,
            periodo__fecha_fin__gte=fecha,
        ).order_by("pk")
        for practica in practicas:
            evaluadas += 1
            try:
                for generar in GENERADORES:
                    alerta, created = generar(practica, fecha=fecha)
                    if alerta is None:
                        continue
                    if created:
                        creadas += 1
                    else:
                        existentes += 1
            except ValidationError as error:
                # Una práctica sin configuración vigente no decide el lote: se
                # informa y se sigue con las demás.
                errores += 1
                self.stdout.write(
                    f"Práctica {practica.pk}: {'; '.join(error.messages)}"
                )
        self.stdout.write(f"Prácticas en curso evaluadas: {evaluadas}")
        self.stdout.write(f"Alertas creadas: {creadas}")
        self.stdout.write(f"Alertas ya existentes: {existentes}")
        self.stdout.write(f"Prácticas con error de configuración: {errores}")
