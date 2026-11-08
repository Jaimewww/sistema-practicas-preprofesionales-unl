# 0011. Método de autenticación de la API

- **Estado**: Aceptada (2026-11-08, implementada en #102 / #79)
- **Fecha**: 2026-11-03
- **Decisores**: Jaime (#79) y Alejandro (#84)

## Contexto

El header `X-Rol` selecciona una persona sintética y **no autentica** (`backend/apps/prototipo/api.py`, decorador `_demo`); esos endpoints solo responden con `DEBUG=True` y, desde #102, viven en `/prototipo/api/v1/`, fuera de la API real. Con datos reales hace falta identidad verificable (RNF-01) y cierre de sesión por inactividad de 30 minutos (RNF-03). [docs/api.md](../api.md) reservaba la sesión de Django para la implementación real y `Authorization: Bearer` para integraciones (RNF-11). El issue #79 deja abierta la elección entre JWT (`djangorestframework-simplejwt`) y Token de DRF y pide registrarla en un ADR.

## Decisión

**JWT con `djangorestframework-simplejwt`**, con token de acceso de vida corta y refresh con rotación y lista de bloqueo (`token_blacklist`) para el cierre de sesión. La sesión de Django se mantiene solo para el admin y las pantallas del prototipo.

Valores efectivos (`SIMPLE_JWT` en `backend/config/settings.py`):

| Parámetro | Valor | Razón |
| --- | --- | --- |
| `ACCESS_TOKEN_LIFETIME` | 15 minutos | Un access robado deja de servir pronto; no se revoca, vence. |
| `REFRESH_TOKEN_LIFETIME` | 30 minutos | RNF-03 pide cerrar la sesión tras 30 minutos de inactividad: con rotación, cada renovación abre otra ventana de 30, y 30 minutos sin renovar la cierran. |
| `ROTATE_REFRESH_TOKENS` | `True` | Cada renovación entrega un refresh nuevo. |
| `BLACKLIST_AFTER_ROTATION` | `True` | El refresh anterior queda bloqueado: reusarlo da 401. |
| `rest_framework_simplejwt.token_blacklist` | en `INSTALLED_APPS` | Guarda los refresh emitidos y bloqueados (migraciones propias de la app). |

Además:

- **Cierre de sesión**: `POST /api/v1/auth/logout/` con `{refresh}` y un access vigente bloquea ese refresh (RNF-03). Un refresh inválido, ya revocado o de otra cuenta responde 400 y no revoca nada; las demás sesiones de la cuenta siguen vivas.
- **Tope de intentos**: `POST /api/v1/auth/token/` usa `ScopedRateThrottle` con el scope `auth` a 5 intentos por minuto y origen; el sexto responde 429 (`demasiadas_solicitudes`, con `Retry-After`). El contador vive en la cache por defecto (`LocMemCache`), por proceso.
- **Rutas públicas**: solo obtener y renovar el token (el login de RNF-01) y `/health/`. El schema y Swagger son anónimos únicamente con `DEBUG` encendido y exigen un access en cualquier otro modo.
- **`X-Rol` en la API real**: se ignora. Una ruta de negocio con `X-Rol` y sin token responde 401 con `DEBUG` encendido y apagado.

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
- **Negativas o costos**: una dependencia más y las tablas de la lista de bloqueo; el cliente debe guardar el token con cuidado; la revocación del access token espera a su vencimiento (por eso es corto); el refresh con rotación obliga al cliente a guardar el refresh nuevo en cada renovación.
- **Límites conocidos**: el tope de intentos usa la cache local del proceso, así que con varios procesos el límite efectivo es por proceso (hoy corre uno solo); pasar a una cache compartida (base o Redis) es un cambio de configuración. Las filas de la lista de bloqueo vencidas se limpian con `manage.py flushexpiredtokens`, que aún no está programado.
- **Verificado** (criterio de #79): los tokens y las contraseñas no aparecen en respuestas ni en logs (`tests/integration/test_auth_seguridad.py`).

## Referencias

- Issue #79, [seguridad.md](../seguridad.md)
- [spec.md, RNF-01, RNF-02, RNF-03](../../specs/001-seguimiento-practicas/spec.md) (líneas 365-367)
- Pruebas: `backend/tests/integration/test_auth_sesion.py` (ciclo de la sesión, tope, schema) y `test_demo_xrol_aislado.py` (`X-Rol` ignorado)
- [docs/api.md, §1](../api.md)
