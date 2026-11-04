# 0012. Contrato universal de respuesta

- **Estado**: Aceptada
- **Fecha**: 2026-11-03
- **Decisores**: equipo (contrato compartido de #76 a #87)

## Contexto

Cada vista del prototipo arma su JSON: las consultas devuelven `{"practicas": [...]}`, `{"alertas": [...]}` o el DTO suelto, y los errores usan `{"error": {"code", "message", "recurso"}}` ([docs/api.md §2](../api.md)). Un cliente no puede tratar éxitos y errores de forma uniforme. El issue #77 fija el contrato.

## Decisión

Toda respuesta con cuerpo del API usa este envelope:

```json
{"success": true, "message": "", "data": {}, "errors": null, "meta": {}}
```

- `success` (bool), `message` (str), `data` (`{}`, `[]` o `null`), `errors` (`null` o un objeto) y `meta` (objeto, por ejemplo paginación).
- Las respuestas `204` van **sin cuerpo**.
- Lo aplican un **renderer** de DRF (éxitos) y un **exception handler** (validación, `401`, `403`, `404`, `405`, `409`, `422` y `500`); el `500` nunca expone trazas ni datos sensibles.
- La semántica HTTP no cambia: `201` al crear, `400` por validación, `401`/`403` por autenticación y rol, `404`, `409` por transición inválida, `422` por regla de negocio ([docs/http-analisis.md](../http-analisis.md)).

## Alternativas consideradas

- **Mantener el contrato de errores actual** (`{"error": {...}}`) y respuestas distintas por endpoint: no es uniforme y no se puede documentar una sola vez en OpenAPI.
- **Formato estándar RFC 9457 (problem+json)**: estandariza los errores, pero no cubre los éxitos y no coincide con el contrato ya acordado por el equipo.
- **Envelope solo en errores**: los clientes siguen sin una forma única para los datos.

## Consecuencias

- **Positivas**: un solo parser en el cliente; pruebas de contrato por código HTTP; Swagger documenta una única estructura.
- **Negativas o costos**: reemplaza el contrato de errores de [docs/api.md §2](../api.md); los clientes y pruebas actuales deben migrar; el campo `data` anida un nivel más.
- **Pendiente**: fijar en #77 cómo se conservan los códigos de dominio actuales (`transicion_invalida`, `dato_invalido`, …) dentro de `errors`, y actualizar `docs/api.md`.

## Referencias

- Issue #77 y contrato compartido de #76
- [0010](0010-adoptar-django-rest-framework-y-postgresql.md)
- [docs/api.md §2](../api.md)
