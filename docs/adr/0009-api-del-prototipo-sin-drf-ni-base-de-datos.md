# 0009. API del prototipo sin Django REST Framework ni base de datos

- **Estado**: Reemplazada por [0010](0010-adoptar-django-rest-framework-y-postgresql.md)
- **Fecha**: 2026-10-21 (decisión original de 2026-10-12, registrada en [docs/api.md](../api.md))
- **Decisores**: equipo

## Contexto

Para el MVP se acordó plantillas de Django como frontend (sesión del 2026-10-12, [research.md, «Temas resueltos»](../../specs/001-seguimiento-practicas/research.md)) y no ofrecer una API REST completa. Los aportes del prototipo (#63 a #67) debían entregar funcionalidad rápido con datos sintéticos.

## Decisión

El API v1 del prototipo usa **`JsonResponse` de Django**, sin DRF, y **sin base de datos**: el catálogo sale de `sample_data.py` y el estado de la demo vive en la sesión y en cookies firmadas, solo con `DEBUG=True`. `X-Rol` selecciona la persona sintética y no autentica. Los DTO cubren lo que haría un serializer.

## Alternativas consideradas

- **SPA con API REST (DRF)**: mejor interacción, pero agrega contrato de API, CORS y más superficie de pruebas; quedó como camino de migración si el producto lo pedía.
- **Híbrido (plantillas + endpoints JSON puntuales)**: viable, pero prematuro.

## Consecuencias

- **Positivas**: arranque con un comando, pocas dependencias, entrega incremental.
- **Negativas o costos**: sin persistencia compartida, sin identidad real, sin OpenAPI ni envelope uniforme; el estado depende del navegador.
- **Reemplazo**: el equipo decidió pasar a modelos Django, PostgreSQL y DRF (#76 a #80); ver [0010](0010-adoptar-django-rest-framework-y-postgresql.md). Este ADR se conserva como historia.

## Referencias

- [docs/api.md](../api.md) (alcance actual y §1)
- [docs/arquitectura.md, §3](../arquitectura.md)
- [plan.md](../../specs/001-seguimiento-practicas/plan.md)
