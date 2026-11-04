# ADR 0005 — Sesión Django, RBAC y aislamiento por consulta

- **Estado**: aceptada
- **Implementación**: planificada — no hay login ni usuarios reales; el prototipo selecciona personas sintéticas con `X-Rol`
- **Registro**: 2026-11-03, retrospectivo

## Contexto

RNF-01 exige inicio de sesión en toda ruta protegida salvo `/login/` y `/health/`. RF-11 exige una matriz rol × acción, y el tutor de entidad es externo a la institución: no debe ver prácticas ajenas.

## Decisión

- Sesión Django para las personas; `Authorization: Bearer` queda reservado a integraciones institucionales (RNF-11).
- RBAC nativo (usuarios, grupos y permisos) más filtrado obligatorio en la consulta por carrera y por practicantes asignados.
- Una acción fuera del rol responde `403` y no modifica ningún dato.

## Alternativas registradas

- **Permisos por objeto con `django-guardian`**: descartado; agrega una dependencia y filas de permisos para un aislamiento expresable con consultas.
- **Filtrar solo en las vistas**: descartado; cualquier endpoint nuevo podría exponer datos de otra carrera.

## Consecuencias

- `X-Rol` selecciona datos de ejemplo, no autentica usuarios de dominio. Con `DEBUG=False` las vistas de demostración se bloquean con `404`; el middleware CSRF puede rechazar un POST antes con `403`.
- El prototipo no debe usarse con datos reales mientras no exista identidad autenticada.
- La matriz RF-11 incluye al director (historial y cierres de su carrera, solo lectura) y a la Secretaría (legalización de anexos) desde el incremento #62; las rutas anteriores no amplían su acceso.
- El spec todavía llama «actor secundario» al director en su sección 2 mientras la matriz lo incluye. Se registra la matriz como fuente vigente y la contradicción queda señalada, sin corregir el spec en este aporte.

**Fuentes**: [spec](../../specs/001-seguimiento-practicas/spec.md) (RNF-01 y matriz RF-11) · [research](../../specs/001-seguimiento-practicas/research.md) Tema 4 · [data-model](../../specs/001-seguimiento-practicas/data-model.md) (regla 1) · [api.md](../api.md) §1 · [api.py](../../backend/apps/prototipo/api.py).
