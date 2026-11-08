# Seguridad: JWT real y permisos por rol y por objeto (#79)

Autenticación de la API real con `djangorestframework-simplejwt` y las clases DRF de
permiso por rol y por objeto. No incluye el flujo de login del cliente, la rotación ni
la revocación de tokens (ADR #84), ni toca el demo del prototipo.

## Ruta rápida

1. Permisos: `backend/apps/seguridad/permissions.py` (`rol_requerido`,
   `PermitirPracticaVisible`, `rol_guardado`).
2. Rutas de token: `backend/apps/seguridad/api.py`
   (`TokenObtainEnvelopeView`, `TokenRefreshEnvelopeView`).
3. Wiring: `backend/config/settings.py` (`INSTALLED_APPS`, `REST_FRAMEWORK`) y
   `backend/config/urls.py` (las dos rutas van antes del demo del prototipo).
4. Vistas protegidas: `backend/apps/practicas/api.py` y `backend/apps/reportes/api.py`.
5. Pruebas: `backend/tests/unit/test_seguridad.py` (permisos) y
   `backend/tests/integration/test_auth_seguridad.py` (S4 de punta a punta).

Fuente: issue #79 (S3/S4), `docs/adr/0011-metodo-de-autenticacion-de-la-api.md` y el
alcance de filas de T019 (`apps/usuarios/permissions.py`).

## Flujo de autenticación

| Método y ruta | Cuerpo | Respuesta |
| --- | --- | --- |
| `POST /api/v1/auth/token/` | `{username, password}` | 200, `data`: `{access, refresh}` |
| `POST /api/v1/auth/token/refresh/` | `{refresh}` | 200, `data`: `{access}` |

El cliente manda `Authorization: Bearer <access>` en el resto de la API real. Las dos
rutas son las únicas públicas (`AllowAny`): sin credenciales no hay a dónde pedir el
token. Todo lo demás es **auth-first**: `DEFAULT_AUTHENTICATION_CLASSES` es
`JWTAuthentication`, `DEFAULT_PERMISSION_CLASSES` es `IsAuthenticated` y el 401 sale con
el envelope de #77 (`errors.detail` = «Se requiere autenticación.»). La autenticación
corre antes del despacho, así que una ruta inexistente o un `id` que no existe también
responde 401 sin credenciales; el 404 aparece recién autenticado.

El envelope no distingue *por qué* falló el token (basura, firma alterada, vencido,
cuenta inactiva o borrada): todas dan 401 con el mismo cuerpo, así que el cliente no
aprende nada del token recibido. Con credenciales pero sin permiso el estado es 403
(`errors.detail` = «No tiene permiso para esta operación.»), también con el envelope.

**CSRF**: las rutas DRF con JWT no usan `csrf_exempt` ni cookies de sesión, así que no
hay exención que agregar ni lógica CSRF nueva en esta unidad. El `csrf_exempt` del
`PATCH` de decisiones del demo es una excepción del prototipo, no se extiende y queda
como deuda del ADR.

## Modelo de permisos

- `rol_requerido(*roles)` fabrica la clase de permiso que exige alguno de esos roles
  (por ejemplo `rol_requerido(Usuario.Rol.ESTUDIANTE)`). Un rol desconocido o una lista
  vacía es un error de programa: la fábrica falla en vez de dejar pasar a nadie.
- `PermitirPracticaVisible`: la entrada exige una cuenta guardada y activa; el objeto se
  decide con `practicas_visibles_para` (T019) acotado al `pk` pedido. No reimplementa el
  alcance de filas: pregunta si el objeto está dentro del alcance, con la misma
  semántica (estudiante = sus prácticas, tutor académico = las asignadas, tutor de
  entidad = las laborales vinculadas, coordinador/director/secretaría = su carrera).
- El rol se relee siempre de la fila guardada por `pk`: el objeto del llamador no decide
  e `is_staff`/`is_superuser` no abren nada.

| Vista | Permisos | Efecto |
| --- | --- | --- |
| `GET /api/v1/practicas/` | `PermitirPracticaVisible` | 200 con las filas de T019; 401 anónimo; 403 sin fila |
| `GET /api/v1/practicas/{id}/` | `PermitirPracticaVisible` | 200 del dueño; 404 fuera de alcance (lo ajeno no existe) |
| `POST /api/v1/practicas/{id}/reportes/` | `rol_requerido(estudiante)` + `PermitirPracticaVisible` | 201 del dueño; 403 por rol u objeto ajeno; 404 si no existe |

En el POST del reporte quedan además los chequeos explícitos de existencia y de dueño
como segunda barrera: el permiso DRF rechaza primero (403) y el chequeo no se retiró.

## Deuda visible: el X-Rol del demo

El demo server-rendered del prototipo sigue seleccionando personas sintéticas con
`X-Rol` y **no autentica** a nadie. Es provisional por decisión explícita (S2) hasta que
el ADR co-escrito con Alejandro (#84) lo resuelva; esta unidad no toca `prototipo/`. La
API real ya no comparte ese mecanismo.

## Límite

`token_blacklist` **no** está habilitada (agregaría migraciones y revocación de sesión
fuera de la unidad) y los tiempos de vida son los valores por defecto de simplejwt
(5 min el access, 1 día el refresh). Que el access venza no equivale al cierre de sesión
por inactividad de RNF-03 (ADR 0011). Las pruebas corren sobre SQLite en memoria.

## Checklist

- [ ] `apps.seguridad` figura en `INSTALLED_APPS` y la API real exige JWT por defecto.
- [ ] `POST /api/v1/auth/token/` devuelve `{access, refresh}` envuelto y el refresh
      renueva el `access`.
- [ ] Sin credenciales, toda la API real responde 401 con envelope.
- [ ] Token basura, alterado, vencido o de cuenta inactiva responde 401 con el mismo cuerpo.
- [ ] Un rol sin permiso recibe 403 y una práctica ajena 404 (detalle) o 403 (POST).
- [ ] Ni la contraseña ni los tokens aparecen en respuestas ni en logs.
- [ ] El demo del prototipo no cambió y su X-Rol sigue marcado como provisional.
