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
| `422 Unprocessable Content` | Solicitud bien formada pero inválida: evidencia de más de 10 MB, horas fuera de rango | RNF-05 |
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

### 2.2 Ivett Zaragocín (`ivecanahi`) — pendiente

- **Requisitos corregidos**: pendiente.
- **Ejercicio de análisis HTTP**: pendiente.
- **Retroalimentación recibida y aplicada**: pendiente.

### 2.3 Alejandro Padilla (`AlejandroTatum`) — pendiente

- **Requisitos corregidos**: pendiente.
- **Ejercicio de análisis HTTP**: pendiente.
- **Retroalimentación recibida y aplicada**: pendiente.

### 2.4 Doménica Rojas (`dme-e`) — pendiente

- **Requisitos corregidos**: pendiente.
- **Ejercicio de análisis HTTP**: pendiente.
- **Retroalimentación recibida y aplicada**: pendiente.

### 2.5 Melissa Contento (`Kthiu666`) — pendiente

- **Requisitos corregidos**: pendiente.
- **Ejercicio de análisis HTTP**: pendiente.
- **Retroalimentación recibida y aplicada**: pendiente.

---

## Registro de correcciones del documento

| Fecha | Corrección | Origen |
| --- | --- | --- |
| 2026-10-12 | Versión inicial: análisis grupal y plantillas individuales. | Sesión ACD 2. |
