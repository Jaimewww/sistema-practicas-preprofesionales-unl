# ACD 2 — Análisis HTTP y requisitos del sistema

Actividad grupal con evidencia individual. Este documento tiene dos partes: el **análisis grupal** de HTTP aplicado a nuestro sistema (sección 1) y la **evidencia individual** de cada integrante (sección 2). Cada integrante completa su propia sección con un commit de su autoría (rúbrica: participación verificable).

**Referencias**: [spec.md](../specs/001-seguimiento-practicas/spec.md) (RF, RNF, HU, casos de uso) · [plan.md](../specs/001-seguimiento-practicas/plan.md) (stack) · [research.md](../specs/001-seguimiento-practicas/research.md) (decisiones).

---

## 1. Análisis grupal: HTTP en nuestro sistema

Nuestro backend es Django 5.2 con frontend server-rendered (plantillas). Django funciona sobre HTTP: cada vista responde a una solicitud con un código de estado y cabeceras. Esta sección fija cómo usamos el protocolo.

### 1.1 Métodos HTTP y su uso en el sistema

| Método | Uso en el sistema | Ejemplo | Nota |
| --- | --- | --- | --- |
| `GET` | Consultas sin efectos: ver horas acumuladas (HU-04), estado de prácticas (HU-05), historial (HU-09) | `GET /practicas/25/horas/` | Seguro e idempotente |
| `POST` | Crear recursos: plan de actividades (HU-01), reporte semanal con evidencias (HU-02), alerta | `POST /practicas/25/reportes/` | No idempotente: dos envíos crean dos recursos |
| `PUT` | Reemplazo completo de un recurso propio | `PUT /planes/7` (reemplaza el plan con nueva versión) | Idempotente |
| `PATCH` | Cambio parcial: validar o devolver un reporte (HU-03), confirmar desde la entidad (HU-07) | `PATCH /reportes/31` `{"estado": "validado"}` | El cambio de estado es parcial: no reenvía todo el reporte |
| `DELETE` | **No se usa** | — | El sistema no borra: el historial es inalterable (RF-10) y las evidencias conservan versiones; se cancela o devuelve, nunca se elimina |

### 1.2 Códigos de estado del sistema

| Código | Cuándo lo responde nuestro sistema | Requisito asociado |
| --- | --- | --- |
| `200 OK` | Consultas exitosas: horas acumuladas, estado de prácticas, historial | RF-05, RF-06 |
| `201 Created` | Recurso creado: plan, reporte semanal, alerta | RF-01, RF-02 |
| `204 No Content` | Acción exitosa sin cuerpo de respuesta (p. ej. confirmar lectura de una alerta) | RF-07 |
| `400 Bad Request` | Solicitud malformada (JSON inválido, faltan campos) | — |
| `401 Unauthorized` | Acceso sin sesión iniciada (redirige al login en la UI) | RNF-01 |
| `403 Forbidden` | Acción fuera del rol del actor, sin alterar datos | RNF-02, RF-11 |
| `404 Not Found` | Recurso inexistente o práctica fuera del alcance del actor | RF-11 (aislamiento) |
| `409 Conflict` | Transición de estado inválida (p. ej. validar un reporte ya cerrado; cerrar sin horas) | RF-09, estados del spec |
| `422 Unprocessable Content` | Solicitud bien formada pero inválida: evidencia de más de 5 MB, reporte de ayudantía que supera el tope de 10 h, horas fuera de rango | RNF-05, RF-15 |
| `500 Internal Server Error` | Error no previsto; nunca debe exponer detalles internos | RNF-06 |

### 1.3 Anatomía de una solicitud/respuesta real

El backend ya tiene un endpoint de salud. Ejecutando el servidor (`make run`) y:

```bash
curl -v http://127.0.0.1:8000/health/
```

**Solicitud** (lo que envía el cliente):

```text
GET /health/ HTTP/1.1
Host: 127.0.0.1:8000
Accept: */*
User-Agent: curl/8.x
```

- **Método**: `GET` — consulta sin efectos.
- **Recurso**: `/health/` — estado del servicio.
- **Cabeceras**: `Host` indica el servidor destino (obligatoria en HTTP/1.1); `Accept` dice qué formatos acepta el cliente.

**Respuesta** (lo que devuelve Django):

```text
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 15

{"status": "ok"}
```

- **Código**: `200 OK` — la consulta se resolvió.
- **Cabeceras de respuesta**: `Content-Type: application/json` declara el formato del cuerpo; `Content-Length` su tamaño.
- **Cuerpo**: JSON con el estado del servicio.

### 1.4 Ejemplo del dominio: crear un reporte semanal

**Solicitud** (estudiante reporta su semana, HU-02):

```text
POST /practicas/25/reportes/ HTTP/1.1
Content-Type: application/json
Authorization: Bearer <token-de-sesion>

{
  "semana": 8,
  "horas_reportadas": 20,
  "actividades": "Instalación del módulo de inventario",
  "evidencia_id": 104
}
```

**Respuesta**:

```text
HTTP/1.1 201 Created
Content-Type: application/json
Location: /practicas/25/reportes/58

{
  "id": 58,
  "semana": 8,
  "horas_reportadas": 20,
  "estado": "en_revision"
}
```

- `201 Created` (y no `200`): se **creó** un recurso nuevo.
- `Location`: la URL del recurso creado (`/practicas/25/reportes/58`), para consultarlo después.
- El reporte queda `en_revision`: sus horas **no cuentan** hasta la validación del tutor (S-04).

### 1.5 Cabeceras relevantes

| Cabecera | Quién la envía | Para qué en el sistema |
| --- | --- | --- |
| `Content-Type` | Ambos | Declara el formato del cuerpo (`application/json` en intercambios de datos; `multipart/form-data` al subir evidencias) |
| `Accept` | Cliente | Negociación: qué formatos acepta |
| `Authorization` | Cliente | Credenciales de la sesión; base de la autorización por rol (RF-11) |
| `Location` | Servidor | URL del recurso recién creado (respuesta a `POST`) |
| `ETag` | Servidor | Versión de un recurso; si dos actores editan el mismo reporte, el `ETag` viejo invalida la edición (control de concurrencia) |

### 1.6 CORS en nuestro proyecto

**Hoy no necesitamos CORS**: el frontend son plantillas servidas por el mismo Django, así que navegador y API comparten origen (mismo esquema, host y puerto) y la política de mismo origen no aplica restricciones entre ellos.

**Cuándo lo requeriríamos**: si migráramos el frontend a una SPA separada (Camino A del Tema 1 de [research.md](../specs/001-seguimiento-practicas/research.md)), el navegador bloquearía las respuestas entre orígenes distintos (por ejemplo `https://app.ejemplo.edu` llamando a `https://api.ejemplo.edu`). La solución sería una política CORS en el servidor (en Django, `django-cors-headers`): cabeceras `Access-Control-Allow-Origin` que autoricen explícitamente el origen del frontend. También aplicaría si el docente o la DVS consumieran datos desde otra aplicación web.

---

## 2. Evidencia individual

Cada integrante completa su sección con: **(a)** al menos dos requisitos revisados o mejorados con justificación, **(b)** su ejercicio de análisis HTTP, y **(c)** una observación de retroalimentación recibida y cómo la utilizó. Editar esta sección desde la propia cuenta de GitHub y abrir un PR hacia `develop`.

### 2.1 Jaime Landázuri (`Jaimewww`)

**(a) Requisitos corregidos**

| Requisito | Antes | Después | Justificación |
| --- | --- | --- | --- |
| RF-11 (COR-04) | «Restringir lo que cada actor puede ver y hacer según su rol.» | Matriz rol × acción con 4 actores y 13 acciones. | La frase era indecidible: no decía qué actor hace qué, así que ninguna prueba podía comprobarla. Con la matriz, cada celda se convierte en un caso de prueba y conecta con RNF-02 (responder 403 sin alterar datos). Es la corrección que sostiene el aislamiento de datos por consulta que exige `research.md` (Tema 4). |
| RF-06 (COR-05) | «Mostrar al coordinador el estado de todas las prácticas de su carrera.» | Por práctica muestra estudiante, tipo, estado, horas validadas, horas en revisión, horas requeridas, alertas activas y tutor académico. | «Estado» no definía qué datos aparecen: dos implementaciones distintas cumplirían el requisito y ninguna se podría objetar. Con la lista explícita se puede comprobar con una consulta (y es exactamente lo que pide el criterio de éxito CE-01: que el coordinador no tenga que pedir nada por correo). |

**(b) Ejercicio de análisis HTTP**

Interpretación de la solicitud de creación de un reporte semanal (ejemplo del §1.4, HU-02):

```text
POST /practicas/25/reportes/ HTTP/1.1
Content-Type: application/json
Authorization: Bearer <token-de-sesion>

{
  "semana": 8,
  "horas_reportadas": 20,
  "actividades": "Instalación del módulo de inventario",
  "evidencia_id": 104
}
```

```text
HTTP/1.1 201 Created
Content-Type: application/json
Location: /practicas/25/reportes/58

{
  "id": 58,
  "semana": 8,
  "horas_reportadas": 20,
  "estado": "en_revision"
}
```

- **Operación**: el estudiante registra la semana 8 de su práctica 25 con horas y evidencia (HU-02).
- **Método y recurso**: `POST` sobre la colección `/practicas/25/reportes/`; el servidor elige el identificador (58) y lo devuelve.
- **Cabeceras relevantes**: `Content-Type: application/json` declara el formato del cuerpo; `Authorization: Bearer` acredita la sesión y es la entrada del control de acceso por rol (RF-11): si el token no es del estudiante de la práctica 25, la respuesta sería `403`, no `201`.
- **Cuerpo**: los datos del reporte. La cabecera dice JSON y el cuerpo lo es: si faltara `Content-Type`, Django no lo interpretaría como JSON.
- **Código de estado**: `201 Created` y no `200 OK` porque la operación **creó** un recurso nuevo con identidad propia; el cuerpo devuelve el recurso con su `id` y `Location` su URL para consultarlo.
- **Significado del estado `en_revision`**: la respuesta ya dice la regla de negocio clave — las 20 horas **todavía no cuentan** para el acumulado; solo cuentan cuando el tutor valida (S-04). El cliente no necesita una segunda consulta para saberlo.
- **Qué habría pasado con entradas inválidas**: JSON malformado → `400`; JSON válido con una evidencia de 12 MB → `422` (RNF-05, solo PDF hasta 5 MB); intento de duplicar la semana 8 ya reportada → `409` (conflicto de estado).

**(c) Retroalimentación recibida y aplicada**

En la revisión del alcance, Ivett observó que el sistema no debe planificarse como un producto aislado sino como un **módulo del sistema académico de la UNL** (O4). La aplicamos como corrección COR-09: nació el RNF-11 (identificar personas y carreras con los identificadores institucionales, sin crear IDs propios) y quedó registrada la restricción de integración institucional. El efecto práctico es que cualquier modelo de datos que use identificadores propios violaría un requisito — la observación cambió una decisión de diseño, no solo la redacción.

### 2.2 Ivett Zaragocín (`ivecanahi`)

**(a) Requisitos corregidos**

| Requisito | Antes | Después | Justificación |
| --- | --- | --- | --- |
| RF-15 (COR-08) | «Marcar para revisión los reportes de ayudantías que superen 10 horas semanales.» | «Rechazar los reportes de ayudantías que superen 10 horas semanales, indicando el límite del Art. 341.» HU-02 (criterio 3) y el caso límite siguen el mismo criterio. | En la revisión de calidad (§9 del spec) falló en *pertinencia*: las 10 h son un máximo del Art. 341, no una sospecha. Marcar el reporte lo dejaba entrar, y un tutor apurado podía validar horas que el reglamento no permite. Rechazarlo hace cumplir la norma y se prueba directo: un reporte de 11 h en una ayudantía no se crea. |
| Caso límite «horas razonables» (COR-07) | «El reporte se identifica para revisión» cuando hay «más horas de lo razonable». | Más de 40 h semanales en práctica laboral o comunitaria se identifica para revisión; en ayudantías, más de 10 h se rechaza. | «Razonable» no se podía medir ni probar. Ahora cada subtipo tiene un umbral numérico: 40 h señala un caso a revisar sin bloquearlo, y 10 h en ayudantía es el tope legal de RF-15. |

**(b) Ejercicio de análisis HTTP**

Solicitud de ejemplo derivada de RF-15; el sistema aún no está implementado. Se escribe como API JSON bajo `/api/v1/`, igual que en el entregable de ACD 2.

*Solicitud*: un estudiante reporta 11 horas en una ayudantía de docencia.

```text
POST /api/v1/practicas/57/reportes/ HTTP/1.1
Content-Type: application/json
Accept: application/json
Authorization: Bearer <token del estudiante>

{
  "semana": "2026-W42",
  "horas": 11,
  "actividades": "Apoyo en la organización de prácticas de laboratorio"
}
```

- **Método**: `POST`, se intenta crear un reporte semanal; no es idempotente: dos envíos válidos crearían dos reportes.
- **Recurso**: `/api/v1/practicas/57/reportes/`, la colección de reportes de la práctica 57, una ayudantía de docencia.
- **Cabeceras**: `Content-Type: application/json` declara que el cuerpo es JSON; `Accept` pide la respuesta en JSON; `Authorization` identifica al estudiante dueño de la práctica.
- **Cuerpo**: la semana ISO, las horas y la descripción de actividades.

*Respuesta*:

```text
HTTP/1.1 422 Unprocessable Content
Content-Type: application/json

{"horas": ["Las ayudantías admiten hasta 10 horas semanales (Art. 341)."]}
```

- **Código**: `422 Unprocessable Content`.
- **Cabeceras**: `Content-Type: application/json`; no hay `Location` porque no se creó ningún recurso.
- **Cuerpo**: el error asociado al campo que falló (`horas`), con el límite y el artículo, para que el estudiante sepa qué corregir.
- **Significado**: el JSON está bien formado y el estudiante tiene permiso, pero las 11 h violan una regla del negocio (RF-15): el reporte no se crea. Si el cuerpo fuera `{"horas": 11` (sin cerrar), la respuesta sería `400 Bad Request`, porque el servidor ni siquiera podría leerlo. Y si quien envía no fuera el dueño de la práctica, sería `403 Forbidden` (RNF-02).
- **Observación**: la tabla del §1.2 asocia `422` solo a «evidencia de más de 10 MB», pero RNF-05 ya fija el máximo en 5 MB (COR-11) y RF-15 es otro caso de `422`. La tabla debe alinearse con los requisitos.

**(c) Retroalimentación recibida y aplicada**

- **Observación**: Doménica Rojas señaló que las ayudantías tienen un máximo de 10 horas semanales (observación O3).
- **Cómo la apliqué**: revisé RF-15 y el caso límite de horas contra el Art. 341. El requisito solo marcaba esos reportes para revisión, así que lo cambié a rechazo con mensaje que cita el límite, y llevé el mismo criterio a HU-02 (criterio 3) y al caso límite (COR-07 y COR-08). La observación también mostró que un tope del reglamento no puede tratarse como una alerta: tiene que bloquear la acción.



### 2.3 Alejandro Padilla (`AlejandroTatum`)

**(a) Requisitos corregidos**

| Requisito | Antes | Después | Justificación |
| --- | --- | --- | --- |
| RF-09 (COR-02) | «Permitir el cierre solo si la práctica cumple horas e informe final.» | Cierre solo con el 100 % de las horas requeridas validadas, el informe final del estudiante revisado, el informe externo registrado y la evaluación final; el cierre conserva el resultado. | «Cumple horas» no decía cuántas ni en qué estado, y omitía el informe externo y la evaluación. El Art. 339 exige el 100 % de las horas y los informes, y ahora el requisito se puede probar: en una práctica laboral presencial (240 h, Art. 334), con 239 h validadas el cierre se rechaza. |
| RF-08 (COR-03) | RF-08 sin norma; HU-07 se aplicaba a cualquier práctica. | RF-08 con el Art. 337 y limitado a la práctica laboral; HU-07 solo para práctica laboral, y el servicio comunitario funciona sin tutor de la entidad. | El tutor de la entidad receptora solo existe en la práctica laboral. Exigir su confirmación en el servicio comunitario dejaría esas prácticas bloqueadas sin poder cerrarse. |

**(b) Ejercicio de análisis HTTP**

Captura real del endpoint de salud: [`evidencias/http-health-curl.txt`](../evidencias/http-health-curl.txt).

*Solicitud 1*: `curl -v -H "Accept: application/json" http://127.0.0.1:8765/health/`

```text
GET /health/ HTTP/1.1
Host: 127.0.0.1:8765
Accept: application/json
```

- **Método**: `GET`, consulta segura que no modifica nada en el servidor.
- **Recurso**: `/health/`, el estado del servicio.
- **Cabeceras**: `Host` identifica el servidor destino; `Accept: application/json` pide la respuesta en JSON.
- **Cuerpo**: ninguno; un `GET` no envía datos en el cuerpo.

*Respuesta 1*:

```text
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 16
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: same-origin
Cross-Origin-Opener-Policy: same-origin

{"status": "ok"}
```

- **Código**: `200 OK`, el servicio responde.
- **Cabeceras**: `Content-Type` coincide con lo pedido en `Accept`. Las otras cuatro las agrega el middleware de seguridad de Django sin código nuestro: `X-Frame-Options: DENY` impide mostrar la página dentro de un `<iframe>` (*clickjacking*), `nosniff` obliga al navegador a respetar el `Content-Type`, y `Referrer-Policy` / `Cross-Origin-Opener-Policy` limitan qué se comparte con otros orígenes.
- **Cuerpo**: JSON `{"status": "ok"}`.

*Solicitud 2*: `curl -v -X POST http://127.0.0.1:8765/health/` responde `HTTP/1.1 403 Forbidden` con `Content-Type: text/html`.

- **Significado**: la vista no restringe métodos, pero el `CsrfViewMiddleware` de Django rechaza todo `POST` que no trae token CSRF, antes de llegar a la vista. En el sistema esto protege los formularios de reportes y validaciones (RF-11): una página ajena no puede enviar un reporte en nombre del estudiante.
- **Observación**: el `403` lo da la protección CSRF, no el diseño del endpoint. Lo correcto para `/health/` sería limitarlo a `GET` (`@require_GET`), para que otro método responda `405 Method Not Allowed`, el código que corresponde a «método no admitido» y que hoy falta en la tabla del §1.2.

**(c) Retroalimentación recibida y aplicada**

- **Observación**: se cuestionó si el cierre de la práctica debía exigir obligatoriamente el 100 % de las horas o si bastaba con un porcentaje menor.
- **Cómo la apliqué**: contrasté RF-09 con el reglamento. El Art. 339 exige el 100 % de las horas requeridas, así que confirmé el requisito y lo dejé explícito en la redacción («100 % de las horas requeridas validadas»). La duda también mostró que el porcentaje debía quedar escrito en el requisito y no darse por sobreentendido.

### 2.4 Doménica Rojas (`dme-e`) — pendiente

- **Requisitos corregidos**: pendiente.
- **Ejercicio de análisis HTTP**: pendiente.
- **Retroalimentación recibida y aplicada**: pendiente.

### 2.5 Melissa Contento (`Kthiu666`)

**(a) Requisitos corregidos**

| Requisito | Antes | Después | Justificación |
| --- | --- | --- | --- |
| RNF-01 (Seguridad) | «Exigir inicio de sesión en todas las páginas, excepto el inicio de sesión y `/health/`.» (verificación: todas las páginas redirigen al inicio de sesión, salvo las dos excepciones). | «Exigir inicio de sesión en todas las rutas protegidas (páginas HTML y endpoints), excepto la ruta de inicio de sesión (`/login/`) y el endpoint de salud (`/health/`), el cual debe responder `200 OK` sin autenticación.» (verificación: sin sesión, las rutas protegidas redirigen a `/login/`; `/login/` y `/health/` responden `200 OK`). | La redacción con «páginas» es ambigua y no cubre endpoints. En nuestro backend existe `GET /health/` sin sesión (y RNF-06 exige consultas periódicas a `/health/` para el monitoreo de disponibilidad). Nombrar explícitamente `/login/` hace el requisito comprobable, tal como exige su verificación. |
| RNF-05 (Integridad de datos) | «Aceptar evidencias en PDF, JPG y PNG de hasta 10 MB, y rechazar cualquier otro formato o tamaño.» (categoría Rendimiento; verificación con 10 MB). | «Aceptar evidencias solo en formato PDF, de hasta 5 MB, y rechazar cualquier otro formato o tamaño con mensaje.» (categoría Integridad de datos; verificación: un PDF de 5 MB se acepta; un PDF de 5,1 MB y cualquier otro formato se rechazan con mensaje). | Hay contradicción con el plan: `research.md` (Tema 5), `data-model.md` («Solo PDF, máximo 5 MB») y `tasks.md` T027 fijan PDF y 5 MB. RNF-05 fue añadido en el PR #38 sin contrastar con esa decisión. RF-02 delega formatos/tamaño a RNF-05, por lo que es necesario alinear el requisito con lo acordado en fase *plan*. Limitar formato y tamaño es una restricción de integridad de datos, no de rendimiento. |

---

## Registro de correcciones del documento

| Fecha | Corrección | Origen |
| --- | --- | --- |
| 2026-10-12 | Versión inicial: análisis grupal y plantillas individuales. | Sesión ACD 2. |
| 2026-10-19 | Sección 2.3 completada (Alejandro Padilla). | Issue #40. |
| 2026-10-12 | Sección 2.2 completada (Ivett Zaragocín). | Issue #39. |
