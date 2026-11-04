# ADR 0003 — DTO, fachada, capa de servicios y tabla de transiciones

- **Estado**: aceptada
- **Implementación**: parcial — existen `facade.py` y `dto.py`; no hay `services.py` ni `apps/practicas/estados.py`
- **Registro**: 2026-11-03, retrospectivo

## Contexto

El contrato JSON y los contextos de pantalla no deben acoplarse a la estructura interna. Las escrituras necesitan reglas y transiciones verificables, con `409` en lugar de un `500`.

## Decisión

- **DTO** por módulo: el dominio interno nunca sale crudo y el contrato absorbe cambios del modelo.
- **Fachada** como única puerta de entrada por módulo: las vistas y el API llaman casos de uso, no modelos de otro módulo.
- **Capa de servicios** para la lógica de escritura (validar, cerrar, suspender), separada de las vistas.
- **Máquina de estados** como tabla explícita con guardas; una transición no listada es `409`.

## Alternativas registradas

- **Repository**: descartado mientras el dominio de la demo está en memoria; con PostgreSQL, el ORM cumple ese rol.
- **Serializers de DRF**: descartados junto con DRF para el MVP; los DTO cubren esa función.
- **Señales de Django para transiciones**: diferidas hasta que exista más de un emisor, por ejemplo las alertas reales.

## Consecuencias

- La tabla real de la demo es `apps/prototipo/coordinador.py` → `TRANSICIONES` y solo cubre suspender, reanudar, cancelar y cerrar; la tabla completa de `data-model.md` (`asignada → en curso → …`) es objetivo.
- Las pantallas de estudiante, tutor y entidad todavía leen `sample_data` (directamente o vía `entidad.py`); coordinador, DVS, director y Secretaría consumen la fachada. Es una excepción heredada, no una regla nueva.
- `services.py` y `estados.py` de producción siguen como tareas pendientes; su ausencia no cambia la decisión.

**Fuentes**: [arquitectura](../arquitectura.md) §2–4 · [data-model](../../specs/001-seguimiento-practicas/data-model.md) (transiciones) · [tasks](../../specs/001-seguimiento-practicas/tasks.md) T017–T018 · [facade.py](../../backend/apps/prototipo/facade.py) · [coordinador.py](../../backend/apps/prototipo/coordinador.py) · [views.py](../../backend/apps/prototipo/views.py) · [entidad.py](../../backend/apps/prototipo/entidad.py).
