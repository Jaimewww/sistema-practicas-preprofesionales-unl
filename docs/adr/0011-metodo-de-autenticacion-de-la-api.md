# 0011. Método de autenticación de la API

- **Estado**: Propuesta (se confirma con Jaime en #79)
- **Fecha**: 2026-11-03
- **Decisores**: Jaime (#79) y Alejandro (#84)

## Contexto

Hoy el header `X-Rol` selecciona una persona sintética y **no autentica** (`backend/apps/prototipo/api.py`, decorador `_demo`); los endpoints solo responden con `DEBUG=True`. Con datos reales hace falta identidad verificable (RNF-01) y cierre de sesión por inactividad de 30 minutos (RNF-03). [docs/api.md](../api.md) reservaba la sesión de Django para la implementación real y `Authorization: Bearer` para integraciones (RNF-11). El issue #79 deja abierta la elección entre JWT (`djangorestframework-simplejwt`) y Token de DRF y pide registrarla en un ADR.

## Decisión

**Recomendación: JWT con `djangorestframework-simplejwt`**, con token de acceso de vida corta (15 minutos, configurable) y refresh con rotación y lista de bloqueo (`token_blacklist`) para el cierre de sesión. La sesión de Django se mantiene solo para el admin y las pantallas del prototipo. Los valores de vida de los tokens se fijan en #79.

| Criterio | JWT (simplejwt) | Token de DRF | Sesión de Django |
| --- | --- | --- | --- |
| Expiración (RNF-03) | Nativa y corta | No expira por defecto; exige código propio | Nativa (`SESSION_COOKIE_AGE`) |
| Revocación | Con blacklist de refresh | Inmediata (borrar el token) | Inmediata |
| CSRF | No aplica con `Authorization: Bearer` | No aplica | Obligatorio (cookie) |
| Soporte en Swagger (drf-spectacular) | Esquema Bearer estándar | Esquema de API key | Cookie, incómodo en «Try it out» |
| Dependencias | Una (`simplejwt`) | Ninguna (incluido en DRF) | Ninguna |
| Cliente no navegador (curl, integraciones) | Natural | Natural | Incómodo |

## Alternativas consideradas

- **Token de DRF**: es lo más simple, pero un token que no expira contradice RNF-03 y su filtración es una cuenta comprometida indefinidamente; añadir expiración equivale a reescribir lo que simplejwt ya trae.
- **Sesión de Django**: coincide literalmente con RNF-01 y revoca al instante, pero obliga a CSRF y a cookies en cada cliente de la API, y dificulta probar en Swagger y con `curl`.

## Consecuencias

- **Positivas**: expiración controlada, sin estado de sesión en el servidor para los accesos, CSRF deja de ser un riesgo para el API y se puede retirar el `csrf_exempt` del PATCH de decisiones al migrar a DRF.
- **Negativas o costos**: una dependencia más; el cliente debe guardar el token con cuidado; la revocación del access token espera a su vencimiento (por eso es corto).
- **Pendiente**: confirmar con Jaime la vida de los tokens y si los tokens y contraseñas nunca aparecen en logs ni respuestas (criterio de #79); registrar el resultado cambiando el estado a Aceptada.

## Referencias

- Issue #79, [seguridad.md](../seguridad.md)
- [spec.md, RNF-01, RNF-03](../../specs/001-seguimiento-practicas/spec.md)
- [docs/api.md, §1](../api.md)
