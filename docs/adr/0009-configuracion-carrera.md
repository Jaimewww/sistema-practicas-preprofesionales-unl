# ADR 0009 — Configuración por carrera con horas copiadas a la práctica

- **Estado**: aceptada
- **Implementación**: parcial — la demo configura por cookie; el modelo `ConfiguracionCarrera` de producción no existe
- **Registro**: 2026-11-03, retrospectivo

## Contexto

RF-12 exige horas requeridas por carrera y modalidad, plazos de reporte y de revisión, y umbral de rezago configurables. Un cambio posterior de horas configuradas no debe alterar las horas requeridas de una práctica ya asignada.

## Decisión

- `ConfiguracionCarrera` guarda las horas requeridas por modalidad, los plazos (3 días naturales y 5 días hábiles por defecto) y el umbral de rezago (80 % por defecto).
- Al asignar la práctica se **copian** sus `horas_requeridas`; no se recalculan después.
- Los plazos y el umbral se leen de la configuración vigente al evaluar alertas; no se copian a la práctica.
- El sistema no fija horas por sí mismo: cada carrera las define.

## Alternativas registradas

- **Referenciar la configuración en vivo**: descartado; un cambio posterior quitaría o sumaría horas a un estudiante que ya venía cumpliendo.
- **Umbral fijo en el código**: descartado por RF-12.
- **Una práctica con dos componentes** (laboral y comunitaria): descartado; duplicaría tutores, planes y cierres dentro del mismo registro.

## Consecuencias

- Solo las horas quedan congeladas en la práctica; los plazos y el umbral se aplican con la configuración vigente en cada evaluación.
- La demo guarda la configuración en una cookie firmada y conserva las horas ya asignadas; el modelo persistente sigue como objetivo.
- El rezago compara horas validadas más en revisión contra las horas esperadas lineales a la fecha.

**Fuentes**: [spec](../../specs/001-seguimiento-practicas/spec.md) RF-12 · [research](../../specs/001-seguimiento-practicas/research.md) Temas 6 y 7 · [data-model](../../specs/001-seguimiento-practicas/data-model.md) (`ConfiguracionCarrera`, `Practica`) · [prototipo-coordinador](../../specs/001-seguimiento-practicas/prototipo-coordinador.md) (Decisiones) · [coordinador.py](../../backend/apps/prototipo/coordinador.py).
