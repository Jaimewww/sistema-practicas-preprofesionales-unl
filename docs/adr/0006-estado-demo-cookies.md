# ADR 0006 — Estado de la demo en cookies firmadas del navegador

- **Estado**: aceptada (solo demostración; no es arquitectura de producción)
- **Implementación**: actual en el prototipo — sesión Django para reportes y tres cookies firmadas
- **Registro**: 2026-11-03, retrospectivo

## Contexto

El prototipo debe recorrerse en un navegador sin base de datos de producción, aislando navegadores y sin mutar los datos de ejemplo compartidos. El MVP de producción todavía no tiene persistencia ni identidad autenticada.

## Decisión

- Reportes enviados en la sesión Django del cliente; decisiones del tutor, cambios del coordinador y legalizaciones de la Secretaría en cookies firmadas de 24 h.
- Las cookies nuevas usan `Path=/` para compartirse entre `/api/` y `/prototipo/`; las anteriores con `Path=/prototipo/` se migran al recibirlas y las vencidas o inválidas se ignoran.
- Las escrituras que dependen de cookies conservan CSRF de Django, salvo la única excepción de demostración descrita a continuación.
- Única exención `csrf_exempt`: el `PATCH /api/v1/pendientes/<clave>/`, limitada a datos sintéticos con `DEBUG=True`; ninguna otra escritura hereda la exención.

## Alternativas registradas

- **Cambios globales en memoria**: descartados; mezclarían navegadores y mutarían los datos de ejemplo.
- **Sesión en base de datos para el estado del coordinador**: descartada en el diseño original de esa pantalla en favor de cookies. Los reportes sí usan sesión Django y `make run` aplica las migraciones necesarias; eso no aporta identidad real.
- **Persistencia compartida en base de datos**: diferida a otro issue con identidad autenticada, permisos y pruebas entre usuarios.
- **Mostrar solo el resultado del POST**: descartado; no permitiría consultar después el cambio desde el consolidado.

## Consecuencias

- Otro navegador ve los datos de ejemplo: no hay colaboración ni persistencia entre usuarios.
- Reiniciar la demo, borrar la cookie o expirar la sesión vuelve a los datos originales; las evidencias no se almacenan, solo su nombre.
- El API rechaza un estado firmado que supera el límite con `500 error_interno`, sin publicar cookie ni éxito; algunas pantallas conservan un `403` de demostración.
- Esta decisión no sustituye la persistencia del MVP ni se adopta como arquitectura de producción.

**Fuentes**: [prototipo-coordinador](../../specs/001-seguimiento-practicas/prototipo-coordinador.md) (Decisiones) · [research 002](../../specs/002-api-alertas-cierre/research.md) (Estado de demostración) · [api.md](../api.md) §5, §6, §8 y §9 · [api.py](../../backend/apps/prototipo/api.py).
