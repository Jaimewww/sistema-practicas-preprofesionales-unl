# ADR 0008 — API v1 con `JsonResponse`, error anidado y sin `DELETE`

- **Estado**: aceptada (contrato adoptado)
- **Implementación**: parcial — endpoints del prototipo implementados (#60–#64); identidad real y persistencia compartida pendientes
- **Registro**: 2026-11-03, retrospectivo

## Contexto

Las pantallas necesitan JSON sin adoptar una API REST completa. El historial es inalterable y los errores deben ser accionables por la interfaz, incluido qué falta para cerrar una práctica.

## Decisión

- Base `/api/v1/`, versionada: los cambios incompatibles van a `/api/v2/` y v1 no se muta.
- `JsonResponse` con DTOs; sin Django REST Framework.
- Errores anidados en `error`, con `code` y `message`; `recurso` se incluye según el caso y `faltante` es una lista en los conflictos de cierre.
- Un método por endpoint (`405` con `Allow`); `POST` crea, `PUT` reemplaza, `PATCH` cambia parcialmente; no existe `DELETE`.
- Transición no listada: `409`; dato inválido: `422`; acción fuera del rol: `403`.

## Alternativas registradas

- **Errores planos**: descartado en #61 para conservar el contrato anidado ya adoptado.
- **`DELETE`**: descartado por RF-10, que exige un historial inalterable.
- **API REST completa con DRF**: descartada para el MVP (ver [ADR 0002](0002-django-plantillas-jsonresponse.md)).
- **Eximir CSRF en las validaciones**: se mantiene solo como excepción de demostración, no como parte del contrato.

## Consecuencias

- Hay respuestas fuera del JSON: una URL sin ruta y el bloqueo con `DEBUG=False` usan el `404` HTML de Django, y un rechazo CSRF usa el `403` HTML del middleware.
- Los endpoints son de demostración con `X-Rol` (ver [ADR 0005](0005-autenticacion-rbac.md)); `DEBUG=False` bloquea sus vistas con `404`, aunque CSRF puede rechazar antes un POST con `403`.
- Cambiar la forma de un payload rompe clientes: exige v2 y actualizar `docs/api.md` junto con las pantallas.

**Fuentes**: [api.md](../api.md) · [research 002](../../specs/002-api-alertas-cierre/research.md) (Transporte) · [plan 002](../../specs/002-api-alertas-cierre/plan.md) · [spec](../../specs/001-seguimiento-practicas/spec.md) RF-09 y RF-10.
