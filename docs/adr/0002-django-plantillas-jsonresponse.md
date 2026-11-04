# ADR 0002 — Django 5.2 con plantillas y `JsonResponse`; sin DRF ni SPA

- **Estado**: aceptada (stack ratificado en la constitución v1.1)
- **Implementación**: parcial — el prototipo usa plantillas y `JsonResponse`; los módulos de producción están planificados
- **Registro**: 2026-11-03, retrospectivo

## Contexto

El plan inicial eligió un servicio reproducible con un comando, sin cliente separado ni API REST completa. Después se incorporó el contrato JSON versionado del API v1 para las pantallas del prototipo; no se adoptó DRF.

## Decisión

- Python 3.12 con Django 5.2 LTS.
- Frontend server-rendered con plantillas de Django.
- JSON con `JsonResponse`, el mismo patrón que `/health/`; sin Django REST Framework ni serializers.
- Sin SPA en el MVP.

## Alternativas registradas

- **NestJS y Spring Boot**: descartados frente a Django, que ya integra RBAC, `FileField` y auditoría con menos dependencias.
- **SPA con API REST (DRF)**: descartada para el MVP; queda como vía de migración si el producto la pide.
- **Híbrido plantillas más endpoints JSON**: prematuro en la fase de plan; los endpoints se agregan a demanda.

## Consecuencias

- Cambiar el framework o el enfoque de frontend exige enmendar la constitución, que fija el stack.
- Los payloads se arman con DTOs y se sirven con `JsonResponse`; no hay serializers que mantengan un contrato paralelo.
- Dependencias declaradas pero no instaladas: `psycopg`, `django-simple-history` y `pytest`/`pytest-django`. `backend/requirements.txt` solo fija Django y `make test` usa el runner de Django.

**Fuentes**: [constitución](../constitution.md) (stack tecnológico) · [research](../../specs/001-seguimiento-practicas/research.md) Temas 1 y frontend · [plan](../../specs/001-seguimiento-practicas/plan.md) (Technical Context) · [requirements.txt](../../backend/requirements.txt) · [Makefile](../../Makefile).
