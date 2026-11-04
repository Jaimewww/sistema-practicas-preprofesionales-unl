# ADR 0007 — Alertas por comando de gestión programado (cron)

- **Estado**: aceptada
- **Implementación**: planificada — no existe el comando; la demo calcula alertas en cada consulta con fecha fija
- **Registro**: 2026-11-03, retrospectivo

## Contexto

RF-07 pide alertas por reportes no enviados, revisiones pendientes, rezago e incumplimientos, con los plazos y el umbral de rezago de la carrera. La escala supuesta es de ~150 prácticas activas, sin necesidad de reintentos ni volumen alto.

## Decisión

- Un comando de gestión de Django lee `ConfiguracionCarrera` (plazos y umbral) y crea las `Alerta`, ejecutado por cron, por ejemplo a diario.
- No se agregan colas, reintentos ni servicios extra para el MVP.

## Alternativas registradas

- **Celery con Redis**: descartado; agrega dos servicios que complican la instalación y el arranque con un comando. Se reevalúa si la escala o el volumen lo exigen.
- **Señales de Django al cambiar de estado**: diferidas hasta que exista más de un emisor; la detección programada cubre el MVP.

## Consecuencias

- La demo calcula las alertas al consultar `GET /api/v1/alertas/` y C2; no hay tarea programada ni notificaciones enviadas.
- El prototipo evalúa con `HOY = 2026-06-05` y no con el reloj real, y usa los plazos de la configuración de la demo.
- Al implementar, la detección debe recibir la fecha de evaluación y no depender del disparador, para poder probarla de forma determinista.

**Fuentes**: [research](../../specs/001-seguimiento-practicas/research.md) Tema 2 de la sesión 2026-10-12 · [tasks](../../specs/001-seguimiento-practicas/tasks.md) T043–T044 · [api.md](../api.md) §8 · [sample_data.py](../../backend/apps/prototipo/sample_data.py) (`HOY`) · [arquitectura](../arquitectura.md) §3.
