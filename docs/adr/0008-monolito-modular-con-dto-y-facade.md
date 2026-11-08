# 0008. Monolito modular con DTO y Facade

- **Estado**: Aceptada
- **Fecha**: 2026-10-21
- **Decisores**: equipo (ver Gobernanza de [docs/arquitectura.md](../arquitectura.md))

## Contexto

A la escala del MVP (5 carreras, ~300 estudiantes, ~150 prácticas activas) hay que dar trazabilidad y control de acceso sin el costo operativo de servicios distribuidos. El principio V de la [constitución](../constitution.md) exige decisiones con alternativas descartadas.

## Decisión

Un único proceso Django organizado en **módulos por dominio** con fronteras explícitas. Cada módulo expone una **fachada** (`facade.py`) y **DTO** (`dto.py`); las vistas del API y de plantilla solo consumen la fachada. La máquina de estados se implementa como tabla de transiciones explícita. Implementación actual: `apps/health` y `apps/prototipo`.

## Alternativas consideradas

- **Microservicios**: el costo operativo (despliegues, red, transacciones distribuidas, observabilidad) no se justifica y contradice «arranca con un solo comando».
- **Monolito sin fronteras**: pierde el aislamiento por dominio que exigen la trazabilidad y el RBAC.

## Consecuencias

- **Positivas**: un deploy, una base; vistas finas y testeables; el contrato del API no depende de la estructura interna.
- **Negativas o costos**: las fronteras se sostienen por revisión de PR, no por el compilador.
- **Pendiente**: con DRF (#76) la fachada evoluciona a la capa `application/` y los DTO a serializers (ver [0010](0010-adoptar-django-rest-framework-y-postgresql.md)); este ADR sigue vigente en lo modular.

## Referencias

- [docs/arquitectura.md](../arquitectura.md)
- [docs/arquitectura/README.md](../arquitectura/README.md)
