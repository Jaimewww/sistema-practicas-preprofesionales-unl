# 0015. Observabilidad mínima: logging estructurado y X-Request-ID

- **Estado**: Aceptada
- **Fecha**: 2026-11-03
- **Decisores**: equipo (issue #86)

## Contexto

Hoy el backend no configura `LOGGING` en `backend/config/settings.py` y `/health/` responde siempre `200` sin comprobar la base (`backend/apps/health/views.py`). Con persistencia real, un error de un cliente no se puede rastrear hasta la línea de log, y un `500` podría filtrar datos sensibles. RNF-06 pide medir la disponibilidad con `/health/`.

## Decisión

1. **Logging estructurado** configurado en `backend/config/logging.py`, con salida a la consola (Docker recoge `stdout`) y un campo `request_id` en cada línea.
2. **Middleware `X-Request-ID`** (`backend/apps/observability`): toma el id del cliente si cumple un formato acotado o genera un UUID, lo expone en cada respuesta y lo inyecta en los logs.
3. Los **errores `500` se registran con su traza en el log**, nunca en la respuesta (coherente con [0012](0012-contrato-universal-de-respuesta.md)); se evita registrar cuerpos, contraseñas, tokens y cabeceras `Authorization`.
4. **`/health/` comprueba la base** y responde `503` si no responde; sigue sin autenticación (RNF-01).

## Alternativas consideradas

- **Sentry u OpenTelemetry**: potentes, pero agregan un servicio o una cuenta externos que el MVP no necesita; se reevalúan si crece la escala.
- **Librerías de logging estructurado (`django-structlog`)**: ahorran código, pero suman una dependencia para un caso que cubre `logging` estándar.
- **Dejar la configuración por defecto de Django**: sin correlación por petición ni formato analizable.

## Consecuencias

- **Positivas**: un reporte de error se rastrea con un identificador; los fallos de base se detectan por el healthcheck de compose y CI; menos riesgo de fuga en `500`.
- **Negativas o costos**: un middleware más en cada petición; aceptar un id del cliente exige validarlo para evitar inyección en logs.
- **Pendiente**: rotación y retención de logs, y métricas, quedan fuera del incremento.

## Referencias

- Issue #86
- [spec.md, RNF-06](../../specs/001-seguimiento-practicas/spec.md)
- [seguridad.md](../seguridad.md)
