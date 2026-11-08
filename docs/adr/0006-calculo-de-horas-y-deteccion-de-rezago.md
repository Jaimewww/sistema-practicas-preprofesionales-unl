# 0006. Cálculo de horas esperadas y detección de rezago

- **Estado**: Aceptada
- **Fecha**: 2026-10-11
- **Decisores**: equipo (clarify de HU-06)

## Contexto

El coordinador necesita enterarse a tiempo de los atrasos (RF-07, HU-06). Alertar solo por horas validadas castigaría al estudiante por la demora del tutor. Origen: [research.md, Tema 6](../../specs/001-seguimiento-practicas/research.md).

## Decisión

Las horas esperadas a una fecha son `horas requeridas × (días transcurridos ÷ días del período)`. Hay **rezago** cuando las horas validadas **más las horas en revisión** quedan por debajo del umbral de la carrera (80 % por defecto, configurable por carrera, RF-12). El prototipo lo implementa en `sample_data._avance` y `sample_data.alertas_de` con `UMBRAL_REZAGO`.

## Alternativas consideradas

- **Contar solo las horas validadas**: castiga al estudiante por la demora del tutor; descartado en clarify.
- **Umbral fijo en el código**: contradice RF-12.

## Consecuencias

- **Positivas**: las alertas reflejan el incumplimiento real y no la cola de revisión.
- **Negativas o costos**: la regla vive en el dominio y necesita pruebas de borde (límite exacto del umbral).
- **Pendiente**: la generación periódica (comando de gestión por cron) no está implementada.

## Referencias

- [research.md, Tema 6](../../specs/001-seguimiento-practicas/research.md)
- [docs/api.md, §8](../api.md)
