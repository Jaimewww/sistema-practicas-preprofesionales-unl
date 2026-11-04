# ADR 0001 — Monolito modular por dominio

- **Estado**: aceptada
- **Implementación**: parcial — solo existen `apps/health` y `apps/prototipo`
- **Registro**: 2026-11-03, retrospectivo

## Contexto

El MVP atiende 5 carreras y ~150 prácticas activas con un equipo pequeño, un solo ciclo académico y un despliegue reproducible con un comando. Necesita trazabilidad y permisos por carrera sin costo operativo distribuido.

## Decisión

- Un único proyecto Django y un único despliegue, organizado en módulos por dominio dentro de `backend/apps/`.
- Cada módulo expone una fachada y DTOs; las vistas, plantillas y el API no consumen modelos ni helpers privados de otro módulo.
- Apps objetivo: `usuarios`, `carreras`, `entidades`, `practicas`, `actividades`, `alertas`, `auditoria` y `reportes`.

## Alternativas registradas

- **Microservicios**: descartados por el costo de varios despliegues, red, transacciones distribuidas y observabilidad a esta escala.
- **Monolito sin fronteras** (una sola app): descartado porque pierde el aislamiento por dominio que exigen la trazabilidad y el RBAC.

## Consecuencias

- El mapa de módulos es objetivo: no existe `backend/apps/practicas/` y el prototipo es una sola app, `apps/prototipo`.
- La regla de fronteras se verifica en revisión de PR; mientras no existan módulos de dominio, la regla todavía no se ejerce.
- El mapa vigente y las fronteras se mantienen en [docs/arquitectura.md](../arquitectura.md), sección 1.

**Fuentes**: [arquitectura](../arquitectura.md) §1 · [plan](../../specs/001-seguimiento-practicas/plan.md) (Structure Decision y Technical Context) · [research](../../specs/001-seguimiento-practicas/research.md) (escala resuelta, Tema 3 de la sesión 2026-10-12).
