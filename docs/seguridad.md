# Modelo de amenazas y controles de seguridad

**Fecha**: 2026-11-12 | **Alcance**: backend Django del sistema de seguimiento de prácticas (incremento de la sumativa 1) | **Issue**: #84

Este documento identifica los activos, los actores y las fronteras de confianza, analiza las amenazas con **STRIDE** por componente y mapea el **OWASP Top 10 2021** a controles concretos. Cada amenaza tiene un control **implementado** (con `archivo:línea`), un control **planificado** (con su issue) o una **justificación** explícita de por qué se acepta el riesgo.

**Convenciones**

- Las líneas de código se midieron sobre el tip de `develop` en `9ef58f5` (cierre de la Sumativa 1); `Dockerfile`, `docker-compose.yml` y `.github/workflows/ci.yml` sobre las ramas de #81 y #82, ya mergeadas.
- **Implementado**: existe en el repositorio hoy. **Planificado (#N)**: depende de ese issue y aún no existe. **Aceptado**: riesgo conocido, con la justificación escrita.
- «Propuesta» marca un control que este documento sugiere y que **ningún issue cubre todavía**; hay que confirmarlo con el equipo.

## 1. Riesgos vigentes que hay que cerrar

| ID | Riesgo | Evidencia | Se cierra con |
| --- | --- | --- | --- |
| R-01 | ~~**`SECRET_KEY` por defecto en el código.**~~ **Resuelto (#98).** El valor por defecto ya no existe: sin `DJANGO_SECRET_KEY` y con `DEBUG` apagado, `settings.py` falla cerrado; con `DEBUG` encendido genera una clave efímera de proceso. | `backend/config/settings.py:43-56`; `backend/tests/unit/test_settings_env.py::SecretKeyTests::test_ausente_y_debug_apagado_falla_cerrado` | #98: fallo cerrado. `docker-compose.yml:29` ya exigía la variable. |
| R-02 | ~~**`X-Rol` no es autenticación.**~~ **Resuelto (#102, `b0af28a7`).** La API real (`/api/v1/`) solo autentica con JWT y no lee `X-Rol`; el demo que lo usa vive ahora en `/prototipo/api/v1/` y responde `404` con `DEBUG=False`. | `backend/config/urls.py:56`; `backend/tests/integration/test_demo_xrol_aislado.py::RutasDeNegocioIgnoranXRolTests::test_x_rol_sin_token_responde_401_con_debug_encendido_y_apagado` | Retiro del demo pendiente de ADR ([ADR 0011](adr/0011-metodo-de-autenticacion-de-la-api.md)). |
| R-03 | El `PATCH /prototipo/api/v1/pendientes/<clave>/` del demo sigue marcado `csrf_exempt`. | `backend/apps/prototipo/api.py:74` y `:63` | Con la API real autenticada por `Authorization: Bearer` el CSRF deja de aplicar; el demo se retira con el ADR pendiente. |
| R-04 | `docker-compose.yml` arranca con `DJANGO_DEBUG=True` por defecto y `backend/.env.example` también lo propone, porque el demo depende de `DEBUG`. | `docker-compose.yml:30`, `backend/.env.example:7` | Cambiar el valor por defecto a `False` cuando se retire el demo del prototipo. |

## 2. Activos

| Activo | Por qué importa | Dónde vive |
| --- | --- | --- |
| Datos personales de estudiantes y tutores (nombre, cédula, correo; RNF-11) | Privacidad: cada actor solo ve lo suyo (RF-11) | PostgreSQL (`POSTGRES_*`, desde #98); la cédula aún no está modelada
| Reportes, horas, evaluaciones y resultados | Base de la certificación de horas y de la titulación (Art. 235, 340) | PostgreSQL (#76) |
| Historial inalterable de estados (RF-10, CE-06) | Trazabilidad y no repudio | Tabla de solo inserción ([ADR 0003](adr/0003-historial-inalterable-con-django-simple-history.md)) |
| Evidencias PDF de hasta 5 MB | Respaldo legal de las horas | Almacén de evidencias (planificado) |
| Credenciales y tokens (contraseñas con hash, JWT) | Suplantación de identidad | PostgreSQL y cliente (JWT desde #102) |
| `DJANGO_SECRET_KEY` y `POSTGRES_PASSWORD` | Falsificación de firmas y acceso a la base | Variables de entorno (`.env` ignorado, `.gitignore:18`) |
| Logs de aplicación | Trazabilidad, pero pueden filtrar datos | `stdout` del contenedor (#86) |

## 3. Actores y fronteras de confianza

```text
 Internet / red UNL ──(F1: HTTPS, fuera del repo)──► Servidor web / proxy ──(F2)──► API Django ──(F3: red de compose)──► PostgreSQL
                                                                                       │
                                                                                       └──(F4: sistema de archivos)──► Evidencias PDF
 CI de GitHub (F5: sin secretos reales) ──► imagen Docker ──► despliegue
```

| Actor | Confianza | Qué puede amenazar |
| --- | --- | --- |
| Estudiante | Autenticado, mínimo privilegio | Leer o modificar la práctica de otro estudiante (IDOR); subir archivos hostiles |
| Tutor académico | Autenticado; solo sus tutorados | Decidir documentos de otro tutor |
| Tutor de la entidad receptora | **Externo a la UNL**, cuenta propia; solo sus practicantes | Acceder a prácticas ajenas (HU-07, caso 3) |
| Coordinador, director, secretaría | Autenticados, alcance por carrera | Acceder a otra carrera; modificar el historial |
| Usuario anónimo / Internet | No confiable | Fuerza bruta, enumeración, denegación de servicio |
| Integrante con acceso al repositorio o a los logs | Parcialmente confiable | Filtrar secretos o datos personales |
| Dependencia o imagen base comprometida | No confiable | Ejecutar código malicioso |

Frontera principal: **todo lo que entra por F1/F2 es no confiable** y se valida en el servidor; F3 y F4 no se exponen fuera de la red de compose (el servicio `db` no publica puertos: `docker-compose.yml` solo mapea el `8000` del `api`, línea 32-33).

## 4. STRIDE por componente

Leyenda de categorías: **S** suplantación, **T** manipulación, **R** repudio, **I** divulgación de información, **D** denegación de servicio, **E** elevación de privilegios.

### 4.1 API real (`backend/apps/practicas/api.py`, `apps/reportes/api.py`, `apps/seguridad/`) y demo (`backend/apps/prototipo/api.py`, `facade.py`, `forms.py`, `validaciones.py`)

| ID | Cat. | Amenaza | Control | Estado |
| --- | --- | --- | --- | --- |
| API-01 | S | Un cliente se hace pasar por otro rol enviando `X-Rol`. | **Resuelto en la API real (#102):** JWT con `Authorization: Bearer`, permisos por rol (`rol_requerido`) y por objeto (`PermitirPracticaVisible`); ninguna ruta de `/api/v1/` lee `X-Rol`. El demo con `X-Rol` quedó en `/prototipo/api/v1/` y responde `404` sin `DEBUG`. | Implementado (#102); demo aislado |
| API-02 | T | Cuerpo o parámetros manipulados: horas de ayudantía mayores a 10, observación de más de 500 caracteres, JSON malformado. | **En la API real (#101):** el serializer rechaza campos no admitidos, `semana` u `horas` inválidas y ayudantías de más de 10 h (Art. 341) con `400` por campo, sin escritura. **En el demo:** `forms.py:94-100` y `validaciones.py:89-91` devuelven `422`/`400`. | Implementado en la API real y en el demo |
| API-03 | T | Transición de estado inválida (cerrar sin requisitos, validar lo ya cerrado). | **En producción (#98):** la tabla de `apps/practicas/services.py:34` rechaza toda arista no listada y todo estado final; el guard de cierre con requisitos sigue en el demo (`facade.py:153`, `409`). | Implementado el mecanismo; el guard de RF-09 sigue en el demo |
| API-04 | R | Un actor niega haber enviado, validado o legalizado algo. | El autor y la fecha los fija el servidor, no el cliente: `Validacion` e `HistorialEstado` los ponen automáticamente y el historial no se edita ([ADR 0003](adr/0003-historial-inalterable-con-django-simple-history.md)); `POST /api/v1/auth/logout/` y `X-Request-ID` completan la trazabilidad. | Implementado (#98, #102, #95) |
| API-05 | I | Acceso a una práctica ajena (IDOR). | **En producción (#102):** `practicas_visibles_para` filtra la consulta y `PermitirPracticaVisible` controla el objeto; la práctica ajena responde `404` idéntico al inexistente. En el demo, `facade._visible` responde `403`. | Implementado (#102, [ADR 0004](adr/0004-autorizacion-rbac-y-filtrado-por-consulta.md)) |
| API-06 | I | Un `500` expone trazas o datos internos. | `DEBUG` apagado por defecto (`settings.py:25`); el exception handler del envelope devuelve un `500` genérico sin trazas y el error queda solo en el log. | Implementado (#100, #95) |
| API-07 | D | Ráfagas de peticiones o cuerpos grandes saturan el servidor. | **Tope de intentos implementado (#79):** `ScopedRateThrottle` con el scope `auth` a 5/min en `POST /api/v1/auth/token/` (`backend/config/settings.py:235`, `backend/apps/seguridad/api.py:56-58`); los intentos correctos y fallidos cuentan y `X-Forwarded-For` no lo reinicia (`NUM_PROXIES: 0`). Siguen el límite de 5 MB por evidencia (`forms.py:45`) y el de 3500 caracteres por cookie (`validaciones.py:19`). | Implementado en el login; límite de cuerpo en el proxy sigue siendo propuesta |
| API-08 | E | Un rol ejecuta una acción de otro (el estudiante cierra una práctica). | **En producción (#102):** `rol_requerido` en las vistas y los servicios leen el rol de la fila guardada; suspender, reanudar, cancelar y cerrar solo los produce el coordinador activo de la carrera (`apps/practicas/services.py:61`). El demo mantiene su `403 fuera_de_rol`. | Implementado (#102); la matriz rol × acción se prueba por caso |
| API-09 | T | CSRF: otra página ordena una acción con la cookie del usuario. | `CsrfViewMiddleware` (`settings.py:49`); la API real usa `Authorization: Bearer`, donde el CSRF de cookies no aplica, y el demo conserva el token CSRF con pruebas de `enforce_csrf_checks=True`. Excepción documentada: `PATCH` del demo (R-03). | Implementado; excepción del demo en R-03 |
| API-10 | T | Redirección abierta mediante el parámetro `next`. | `url_has_allowed_host_and_scheme` (`views.py:161`). | Implementado |

### 4.2 Autenticación y sesión

| ID | Cat. | Amenaza | Control | Estado |
| --- | --- | --- | --- | --- |
| AUT-01 | S | Fuerza bruta o credential stuffing contra el inicio de sesión. | **Tope de intentos implementado (#79, `9288d311`):** 5 por minuto por origen en `/api/v1/auth/token/`, con `429` y `Retry-After`; además, validadores de contraseña de Django (`settings.py:165`) y hash PBKDF2 por defecto. | Implementado; `tests/integration/test_auth_sesion.py::TopeDeIntentosTests` |
| AUT-02 | S | Robo o reutilización de un token. | **Implementado (#79, [ADR 0011](adr/0011-metodo-de-autenticacion-de-la-api.md)):** access de 15 min, refresh de 30 roto en cada renovación y lista de bloqueo (`settings.py:246-251`); TLS queda del despliegue. | Implementado; `tests/integration/test_auth_sesion.py::RotacionDelRefreshTests` |
| AUT-03 | I | Contraseñas o tokens aparecen en respuestas o logs. | Las respuestas de token no repiten la clave y el log no registra cuerpos ni `Authorization` ([ADR 0015](adr/0015-observabilidad-minima-logging-y-request-id.md)). | Implementado; `tests/integration/test_auth_seguridad.py::SinFugasDeSecretosTests` |
| AUT-04 | T | Cookies firmadas de la demo falsificadas o reutilizadas. | `django.core.signing` con `max_age` de 24 h (`validaciones.py:26,33`); `HttpOnly`, `SameSite=Lax` y `Secure` bajo HTTPS (`validaciones.py:36-37`, `coordinador.py:46-47`, `secretaria.py:40-41`). La firma vale lo que valga `SECRET_KEY`, que ya no tiene valor por defecto (R-01). Desaparecen cuando se retire el demo. | Implementado mientras exista el demo |
| AUT-05 | E | Sesión que no expira por inactividad (RNF-03). | **Implementado (#79):** access de 15 min y refresh de 30 con rotación, así que 30 minutos sin renovar cierran la sesión; `POST /api/v1/auth/logout/` revoca el refresh entregado (`backend/apps/seguridad/api.py:106-135`). | Implementado; `tests/integration/test_auth_sesion.py::CierreDeSesionTests` |
| AUT-06 | E | El admin de Django queda expuesto en `/admin/` con credenciales débiles. | Ruta `admin/` activa (`backend/config/urls.py:6`) sin superusuario por defecto ni datos reales. **Propuesta**: restringirla por red o deshabilitarla fuera de desarrollo en #76. | Aceptado con justificación (no hay cuentas ni datos reales en este incremento); propuesta |

### 4.3 Base de datos

| ID | Cat. | Amenaza | Control | Estado |
| --- | --- | --- | --- | --- |
| BD-01 | T | Modificación o borrado del historial inalterable. | **Implementado (#98):** `HistorialEstado` es de solo inserción y su queryset rechaza `update`, `delete`, `bulk_update` y `bulk_create` (`backend/apps/auditoria/models.py:15-33`); el API no ofrece `DELETE` ([api.md §1](api.md)). | Implementado; `tests/unit/test_historial_estado.py::HistorialEstadoInmutableTests` |
| BD-02 | I | Fuga de datos de otra carrera por una consulta sin filtro. | Filtrado obligatorio por consulta con `practicas_visibles_para` ([ADR 0004](adr/0004-autorizacion-rbac-y-filtrado-por-consulta.md)); pruebas de acceso ajeno (#102). | Implementado; `tests/integration/test_aislamiento_roles.py` |
| BD-03 | I | Credenciales de la base en el repositorio. | `POSTGRES_PASSWORD` sin valor por defecto (`docker-compose.yml:8`); `.env` ignorado (`.gitignore:18`); CI usa valores que no son secretos (`ci.yml`, job `test`). | Implementado |
| BD-04 | T | Inyección SQL. | La API real usa el ORM de Django sobre PostgreSQL, así que las consultas van parametrizadas; no se usa SQL crudo en el código de aplicación. El SQL crudo queda solo en el `SELECT 1` del healthcheck. | Implementado (#98) |
| BD-05 | S | Acceso a PostgreSQL desde fuera de la red de compose. | El servicio `db` no publica puertos (`docker-compose.yml:32-33` solo expone `api`). | Implementado |
| BD-06 | D | Pérdida de datos o indisponibilidad (RNF-06: 99 % y copia diaria). | Volumen `pgdata` (`docker-compose.yml:15-16`); healthcheck de la base. La copia diaria **no** se implementa en este incremento. | Aceptado con justificación (respaldo y operación son del despliegue institucional, fuera de alcance; spec RNF-06) |

### 4.4 Evidencias PDF

| ID | Cat. | Amenaza | Control | Estado |
| --- | --- | --- | --- | --- |
| EVI-01 | T | Subir un archivo que no es PDF o un ejecutable disfrazado. | Extensión `.pdf` y firma `%PDF-` (`forms.py:33-38`) con rechazo `422`. La API real todavía no acepta evidencias: cuando lo haga, la validación se repite en el serializer. | Implementado en el demo; sin evidencias en la API real |
| EVI-02 | D | Archivos enormes o cantidad ilimitada llenan el disco. | Máximo de 5 MB por archivo (`forms.py:5,45`, RNF-05). No hay tope de archivos por reporte. **Propuesta**: limitarlo en el serializer de #78. | Implementado en parte; propuesta |
| EVI-03 | I | Descarga de evidencias ajenas por URL adivinable. | Hoy no se almacenan (solo su nombre, [api.md §5](api.md)). Al guardarlas: servirlas por una vista con permiso por objeto (#79), nunca como `MEDIA_URL` público. | Planificado (#78, #79) |
| EVI-04 | T | Reemplazo de una evidencia ya validada. | Versionado: cada devolución conserva archivo y observación ([ADR 0005](adr/0005-gestion-de-evidencias-pdf-versionadas.md)); en producción la versión del plan sí se conserva (`PlanActividades.version`), la del reporte aún no existe. | Implementado en la demo y en el plan; pendiente en el reporte real |
| EVI-05 | T | Nombre de archivo malicioso (path traversal) o contenido con malware. | Hoy no se escribe nada en disco. Al almacenar: nombre generado por el servidor y sin ejecución del contenido. El escaneo antivirus **no** se incluye. | Aceptado con justificación (MVP; el archivo no se ejecuta ni se interpreta) |

### 4.5 Configuración y secretos

| ID | Cat. | Amenaza | Control | Estado |
| --- | --- | --- | --- | --- |
| CFG-01 | I | `SECRET_KEY` por defecto permite falsificar firmas y sesiones. | **Resuelto (#98):** ver R-01; sin valor por defecto y fallo cerrado (`settings.py:43-56`). `docker-compose.yml:29` la exige. | Implementado |
| CFG-02 | I | Secretos subidos a Git. | `.env` en `.gitignore:18`; `backend/.env.example` solo trae marcadores (`DJANGO_SECRET_KEY=django-insecure-change-me`, línea 6); compose exige las variables (`:?`). **Propuesta**: paso de escaneo de secretos en CI (#82). | Implementado; propuesta |
| CFG-03 | I | `DEBUG=True` en un despliegue expone trazas y habilita el prototipo. | Valor por defecto `False` (`settings.py:25`); `solo_en_debug` (`views.py:50-57`). Ver R-04: el compose lo enciende porque el demo depende de él. | Implementado; mitigado mientras exista el demo (R-04) |
| CFG-04 | S | Ataque por cabecera `Host`. | `ALLOWED_HOSTS` sale del entorno (`settings.py:27-29`); vacío y sin `DEBUG` rechaza todos los hosts. | Implementado |
| CFG-05 | T | Dependencia o imagen base comprometida. | Django acotado a `>=5.2,<5.3` (`requirements.txt:1`); `ruff` fijado (`ci.yml:24`); imagen base con etiqueta de versión (`python:3.13-slim`, `Dockerfile:2`), sin fijar por digest; `pip-audit` revisa CVE de las dependencias en cada PR (`ci.yml:39`). **Propuesta**: Dependabot y fijar la imagen por digest. | Parcial; implementado en CI |
| CFG-06 | E | El proceso del contenedor corre como root. | `useradd` y `USER app` (`Dockerfile:18,21`). | Implementado |
| CFG-07 | T | El workflow de CI obtiene permisos de más. | `permissions: contents: read` y sin secretos del repositorio (`ci.yml:8`). | Implementado |

### 4.6 Logs y observabilidad

| ID | Cat. | Amenaza | Control | Estado |
| --- | --- | --- | --- | --- |
| LOG-01 | I | Datos personales, contraseñas o tokens en los logs. | `LOGGING` estructurado en `settings.py` con formato JSON (`backend/apps/observability/logging.py`); el `500` se registra sin datos sensibles y no se registran cuerpos ni `Authorization` ([ADR 0015](adr/0015-observabilidad-minima-logging-y-request-id.md)). | Implementado (#95, #86) |
| LOG-02 | R | No se puede reconstruir quién hizo una petición. | `X-Request-ID` en cada respuesta y en los logs (`backend/apps/observability/middleware.py`) más el historial de estados (#98, BD-01). | Implementado (#95, #98) |
| LOG-03 | T | Inyección de líneas en el log mediante un `X-Request-ID` hostil. | El middleware acepta el id del cliente solo con un formato acotado y, si no, genera un UUID ([ADR 0015](adr/0015-observabilidad-minima-logging-y-request-id.md)). | Implementado (#95); `backend/apps/observability/tests.py` |
| LOG-04 | D | Los logs llenan el disco. | Salida a `stdout`; Docker gestiona el almacenamiento. Rotación y retención quedan fuera del incremento. | Aceptado con justificación (volumen bajo; se define en el despliegue) |
| LOG-05 | D | `/health/` no detecta una base caída y el orquestador sigue enviando tráfico. | `/health/` consulta la base y responde `503` si falla, sin filtrar el error (`backend/apps/health/views.py:9-24`). | Implementado (#95); `backend/apps/health/tests.py::HealthEndpointTests::test_health_returns_503_when_database_is_down` |

> Las filas de esta sección y de la §4 se re-midieron al cierre (2026-11-12). La matriz OWASP de §5 conserva el análisis de la fecha original; el estado real de cada control es el de las tablas STRIDE de §4.

## 5. OWASP Top 10 2021 mapeado a controles

| Categoría | Riesgo en este sistema | Controles implementados | Controles planificados | Amenazas |
| --- | --- | --- | --- | --- |
| **A01** Pérdida de control de acceso | Un actor ve o modifica prácticas ajenas; el rol lo declara el cliente. | `facade._visible` (`facade.py:49`); `403`/`401` por rol (`api.py:53-57`); `404` sin `DEBUG` (`views.py:50-57`); CSRF (`settings.py:49`). | Permisos por rol y por objeto, filtrado en repositorio (#79, [ADR 0004](adr/0004-autorizacion-rbac-y-filtrado-por-consulta.md)). | API-01, 05, 08, 09; BD-02; EVI-03 |
| **A02** Fallos criptográficos | Firmas con clave débil; datos personales sin TLS; contraseñas sin hash. | `django.core.signing` con `max_age` (`validaciones.py:26`); cookies `HttpOnly`/`SameSite`/`Secure` bajo HTTPS (`validaciones.py:36-37`); hash PBKDF2 de Django (RNF-03). | `SECRET_KEY` obligatoria (#76); TLS en el proxy del despliegue. **Propuesta**: `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` y HSTS cuando haya HTTPS. | AUT-04; CFG-01 (R-01) |
| **A03** Inyección | SQL, comandos o HTML inyectado. | Sin SQL hoy (datos en memoria); las plantillas escapan por defecto y no hay `|safe` ni `mark_safe` en `backend`; validación de entrada en `forms.py` y `validaciones.py:69-91`. | ORM parametrizado y serializers (#76, #78). | API-02; BD-04 |
| **A04** Diseño inseguro | Reglas de negocio saltables (Art. 341, cierre sin requisitos). | Reglas en el servidor: ayudantía de hasta 10 h (`forms.py:6,94-100`), cierre con guard `409` (`facade.py:153-164`), tabla de transiciones, rechazos sin efectos ([api.md §5](api.md)). Este modelo de amenazas. | Reglas en `domain/` con pruebas de dominio (#76, #80). | API-03; BD-01 |
| **A05** Configuración de seguridad incorrecta | `DEBUG` encendido, clave por defecto, hosts abiertos, contenedor root. | `DEBUG=False` por defecto (`settings.py:25`); `ALLOWED_HOSTS` por entorno (`:27-29`); compose exige secretos (`docker-compose.yml:8,29`); usuario no root (`Dockerfile:21`); la base no se publica. | Quitar `SECRET_KEY` por defecto (#76); `DEBUG` por defecto `False` en compose tras #79 (R-04). **Propuesta**: ejecutar `manage.py check --deploy` en CI. | CFG-01, 03, 04, 06; BD-05 |
| **A06** Componentes vulnerables y desactualizados | Django y dependencias con CVE conocidos. | `Django>=5.2,<5.3` recibe parches de seguridad (`requirements.txt:1`); herramientas de CI fijadas (`ci.yml:24`); `pip-audit` (`ci.yml:39`) y `bandit` (`ci.yml:37`) en cada PR. | **Propuesta**: Dependabot. | CFG-05 |
| **A07** Fallos de identificación y autenticación | Sin autenticación real; fuerza bruta; sesiones sin expiración. | Validadores de contraseña (`settings.py:90`); cookie de demo con expiración de 24 h. | Autenticación JWT con expiración y rotación (#79, [ADR 0011](adr/0011-metodo-de-autenticacion-de-la-api.md)); **propuesta**: `throttle` en el login. | API-01; AUT-01, 02, 05 (R-02) |
| **A08** Fallos de integridad de software y de datos | Estado de cliente manipulable; pipeline o imagen alterados; historial editable. | Estado de demo firmado (`validaciones.py:33`); el API no expone `DELETE`; CI con permisos de solo lectura (`ci.yml:8`). | Historial de solo inserción ([ADR 0003](adr/0003-historial-inalterable-con-django-simple-history.md), #76); el estado de cliente desaparece con la persistencia. | AUT-04; BD-01; EVI-04; CFG-07 |
| **A09** Fallos de registro y monitoreo | Un incidente no se puede reconstruir ni detectar. | Ninguno completo hoy: no hay `LOGGING` en `settings.py`. | Logging estructurado, `X-Request-ID`, `500` sin datos sensibles y `/health/` con `503` (#86, [ADR 0015](adr/0015-observabilidad-minima-logging-y-request-id.md)). | API-04; LOG-01 a 05 |
| **A10** Falsificación de petición del lado del servidor (SSRF) | El servidor pide URLs que controla el usuario. | No aplica hoy: el backend no hace peticiones salientes (`requests`, `urllib` y `httpx` no se importan en `backend`). | Si se integra el SIAAF (fuera de alcance), validar destinos con lista de permitidos. | — (aceptado: sin superficie) |

## 6. Cobertura por issue

| Issue | Controles que aporta |
| --- | --- |
| #76 (#98) | `SECRET_KEY` sin valor por defecto, PostgreSQL por `POSTGRES_*`, ORM, historial de solo inserción, filtrado por consulta, servicios de dominio |
| #77 (#100) | Exception handler: `500` sin trazas, envelope uniforme ([ADR 0012](adr/0012-contrato-universal-de-respuesta.md)), esquema OpenAPI |
| #78 (#101) | Serializers, validación de entrada y persistencia del reporte semanal; las evidencias PDF siguen pendientes |
| #79 (#102) | Autenticación JWT, permisos por rol y por objeto, revisión de CSRF, tokens fuera de logs, tope de intentos |
| #80 (#103) | Pruebas de seguridad y cobertura sobre pytest-django |
| #81 | Contenedor sin root, secretos por entorno, base no publicada |
| #82 (#107) | CI con permisos mínimos, `bandit` y `pip-audit`; **propuestas**: escaneo de secretos, `check --deploy` |
| #86 (#95) | Logging estructurado, `X-Request-ID`, `/health/` con `503` |

## 7. Pendientes para confirmar con el equipo

1. **Demo `X-Rol`:** sigue vivo en `/prototipo/api/v1/` con autenticación emulada. Su retiro exige un ADR que decida qué se conserva de las pantallas; hasta entonces `docker-compose.yml` mantiene `DJANGO_DEBUG=True` (R-04) y el `csrf_exempt` del `PATCH` de §6 (R-03) sigue vigente.
2. **Controles propuestos sin issue:** límite de cuerpo en el proxy, tope de archivos por reporte, restricción de `/admin/` por red, Dependabot, escaneo de secretos y `check --deploy` en CI, `SECURE_SSL_REDIRECT`/HSTS y cookies `Secure` cuando haya HTTPS.
3. **`runserver` sin TLS:** el despliegue de este incremento es local (Docker Compose en `127.0.0.1`), sin proxy TLS; los tokens JWT viajan en claro en ese escenario y por eso no hay entorno productivo.
4. **Refresh en el logout:** el logout revoca el refresh entregado, pero el access ya emitido sigue válido hasta vencer (≤ 15 minutos) y no existe lista de access revocados.
5. **Copia diaria de la base (RNF-06)** y retención de logs: dependen del despliegue institucional y quedan fuera de este incremento.
6. **Evidencias PDF (RNF-05):** no hay entidad de evidencia en la API real; sigue pendiente con su propio issue.
