# ACD 2 — Requisitos verificables y fundamentos de HTTP

## 1. Datos de Identificación del Estudiante y la Práctica

| Campo | Valor |
| --- | --- |
| Nombre del estudiante(s) | Jaime Landázuri, Ivett Zaragocín, Alejandro Padilla, Doménica Rojas, Melissa Contento |
| Asignatura | Desarrollo Basado en Plataformas |
| Ciclo | 5 A |
| Unidad | Unidad 1 |
| Práctica Nro. | 2 |
| Tipo | Grupal con evidencia individual |
| Título de la Práctica | Requisitos funcionales y no funcionales verificables, y análisis de solicitudes y respuestas HTTP: Sistema de gestión de prácticas preprofesionales |
| Nombre del Docente | Ing. Edison Coronel |
| Fecha | 18 de octubre de 2026 |

## 2. Punto de partida

La semana 1 dejó definidos el problema, los actores, el alcance y cinco preguntas de clarificación. Esta semana el equipo revisó ese trabajo contra el **Reglamento de Régimen Académico de la UNL** y lo convirtió en requisitos verificables. La especificación vigente es `specs/001-seguimiento-practicas/spec.md` (v0.3.0) del repositorio `Jaimewww/sistema-practicas-preprofesionales-unl`; este documento resume sus cambios y no la reemplaza.

| Elemento | Semana 1 (v0.1.0) | Semana 2 (v0.3.0) |
| --- | --- | --- |
| Requisitos funcionales | 13 | 19, auditados con cinco criterios de calidad |
| Requisitos no funcionales | 0 | 11, en las siete categorías pedidas |
| Historias de usuario | 9 | 13, con criterios Dado / Cuando / Entonces |
| Casos de uso | 0 | 3 |
| Base normativa | Caso de estudio | Artículos del reglamento citados en cada requisito |

## 3. Requisitos funcionales

Cada requisito cita su historia de usuario y el artículo del reglamento que lo respalda. Los dos sin artículo (RF-04 y RF-13) salen del problema delimitado: trazabilidad y prácticas interrumpidas.

| ID | El sistema debe… | Norma |
| --- | --- | :---: |
| RF-01 | Permitir al estudiante registrar su plan de actividades y enviarlo a revisión. | Art. 336 |
| RF-02 | Permitir al estudiante registrar actividades semanales con horas y adjuntar evidencias en los formatos y tamaño de RNF-05. | Art. 11 |
| RF-03 | Permitir al tutor académico validar o devolver planes y reportes; la devolución exige observación. | Art. 336 |
| RF-04 | Registrar en cada validación quién la realizó y en qué fecha. | — |
| RF-05 | Calcular las horas validadas de cada práctica y compararlas con las requeridas. | Art. 334, 339 |
| RF-06 | Mostrar al coordinador, por cada práctica de su carrera, estudiante, tipo, estado, horas validadas, en revisión y requeridas, alertas activas y tutor. | Art. 331, 335 |
| RF-07 | Generar alertas por reportes no enviados, revisiones pendientes, horas rezagadas e incumplimientos reportados. | Art. 336 |
| RF-08 | Permitir al tutor de la entidad receptora de una práctica laboral confirmar los reportes de sus practicantes y registrar su informe final. | Art. 337 |
| RF-09 | Permitir el cierre solo con el 100 % de las horas validadas, el informe del estudiante revisado, el informe externo y la evaluación final. | Art. 339 |
| RF-10 | Guardar un historial inalterable de los cambios de estado de cada práctica. | Art. 340 |
| RF-11 | Permitir a cada actor solo las acciones de la matriz de permisos rol × acción y rechazar cualquier otra. | Art. 335–337 |
| RF-12 | Configurar por carrera horas por modalidad, plazos de reporte y revisión, y umbral de rezago. | Art. 334 |
| RF-13 | Permitir al coordinador suspender, reanudar y cancelar una práctica, con motivo obligatorio. | — |
| RF-14 | Registrar tipo, subtipo laboral y proyecto de vinculación obligatorio en la comunitaria. | Art. 332, 338, 341, 347 |
| RF-15 | Rechazar los reportes de ayudantías que superen 10 horas semanales. | Art. 341 |
| RF-16 | Permitir al estudiante presentar su informe final y al tutor académico revisarlo o devolverlo. | Art. 336 |
| RF-17 | Registrar la evaluación final en porcentaje: «aprobada» desde 70 %, «no aprobada» por debajo. | Art. 339 |
| RF-18 | Permitir al tutor de la entidad reportar un incumplimiento al tutor académico. | Art. 337 |
| RF-19 | Generar el informe consolidado de cumplimiento de la carrera. | Art. 335, 340 |

## 4. Requisitos no funcionales

Cada requisito tiene una cifra o una prueba objetiva. Los valores son propuestas del equipo que se ajustarán al prototipar; lo que no cambia es que cada uno se pueda medir.

| ID | Categoría | El sistema debe… | Se verifica con |
| --- | --- | --- | --- |
| RNF-01 | Seguridad | Exigir sesión iniciada en toda página, salvo el inicio de sesión y `/health/`. | Pedir una página sin sesión: redirige al inicio de sesión. |
| RNF-02 | Seguridad | Responder 403 a toda acción fuera del rol, sin alterar datos. | Un tutor de entidad pide la práctica de otro practicante. |
| RNF-03 | Seguridad | Guardar contraseñas con hash y cerrar la sesión tras 30 min de inactividad. | Revisión de la base de datos y prueba de expiración. |
| RNF-04 | Rendimiento | Cargar el panel del coordinador en menos de 2 s con 150 prácticas activas. | Prueba con datos de la escala asumida en `plan.md`. |
| RNF-05 | Rendimiento | Aceptar evidencias PDF, JPG o PNG de hasta 10 MB y rechazar las demás. | Subir un archivo de 11 MB y uno `.exe`. |
| RNF-06 | Disponibilidad | Estar disponible el 99 % del período académico, con respaldo diario. | Registro de monitoreo y restauración de prueba. |
| RNF-07 | Usabilidad | Permitir que un estudiante nuevo registre su primer reporte sin ayuda en menos de 5 min. | Prueba cronometrada con estudiantes. |
| RNF-08 | Accesibilidad | Cumplir WCAG 2.1 nivel AA: contraste, uso con teclado y etiquetas en formularios. | Auditoría con Lighthouse o axe sin errores críticos. |
| RNF-09 | Mantenibilidad | Cubrir con pruebas al menos el 80 % de las reglas de negocio y pasar el linter sin errores. | Reporte de cobertura e integración continua en verde. |
| RNF-10 | Interoperabilidad | Exportar el consolidado a CSV UTF-8 con fechas ISO 8601. | Abrir el archivo en una hoja de cálculo. |
| RNF-11 | Interoperabilidad | Usar los identificadores institucionales (cédula y código de carrera). | Comparar los campos con los del sistema académico institucional. |

## 5. Revisión de calidad de los requisitos

El equipo revisó los 19 requisitos funcionales con cinco preguntas: ¿es **claro**?, ¿es **específico**?, ¿es **pertinente** al problema?, ¿es **verificable**?, ¿es **consistente con el alcance**? Los que fallaron se corrigieron:

| Requisito | Criterio que fallaba | Corrección |
| --- | --- | --- |
| RF-11 | Verificable | «Restringir lo que cada actor puede ver» no dice qué. Se reemplazó por una matriz rol × acción: cada celda es una prueba. |
| RF-06 | Específico | «El estado» no decía qué datos mostrar. Ahora enumera los campos por práctica. |
| RF-02 | Verificable | No decía qué evidencias se aceptan. Ahora remite a RNF-05 (formatos y 10 MB). |
| RF-15 | Consistente | Marcaba los reportes con más de 10 h, pero el reglamento fija ese tope como máximo. Ahora los rechaza. |
| Caso límite «horas razonables» | Verificable | No tenía número. Ahora: más de 40 h semanales en laboral o comunitaria se marca; más de 10 h en ayudantía se rechaza. |
| RF-09 | Pertinente | Cerraba con «horas e informe»; el reglamento exige 100 % de horas y 70 % de evaluación (Art. 339). |
| RF-08 | Consistente | Pedía informe al tutor de la entidad en toda práctica; el servicio comunitario no lo tiene (Art. 337). |

## 6. Casos de uso

La especificación detalla tres casos de uso: **CU-01 Validar un reporte semanal**, **CU-02 Cerrar la práctica** y **CU-03 Generar alertas de rezago**. Se presenta el primero, que concentra la regla central del sistema: solo cuentan las horas validadas.

| Elemento | CU-01 · Validar un reporte semanal |
| --- | --- |
| Actor principal | Tutor académico |
| Precondiciones | Práctica `en curso`; reporte semanal en estado «en revisión». |
| Flujo principal | 1. El tutor abre sus reportes pendientes. 2. Revisa actividades, horas y evidencias. 3. Valida el reporte. 4. El sistema suma las horas al acumulado y registra autor y fecha. |
| Flujos alternativos | 3a. El tutor devuelve el reporte: debe escribir una observación y el reporte vuelve al estudiante. 3b. El plazo de revisión venció: el sistema ya generó una alerta al tutor. |
| Postcondiciones | Horas acumuladas actualizadas y validación trazable. |
| Requisitos relacionados | RF-03, RF-04, RF-05, RF-07 |

## 7. Historias de usuario y criterios de aceptación

Las 13 historias están en la especificación. Se muestran tres criterios que cambiaron esta semana, porque cada uno se puede convertir directamente en una prueba:

| Historia | Dado | Cuando | Entonces |
| --- | --- | --- | --- |
| HU-02 #3 | una práctica de subtipo ayudantía | el estudiante reporta más de 10 h en una semana | el reporte se rechaza indicando el límite del Art. 341 |
| HU-08 #2 | una práctica sin el 100 % de horas, sin informes o sin evaluación | se intenta cerrar | el cierre se rechaza indicando qué falta |
| HU-11 #1–2 | una práctica con informes registrados | el tutor registra 70 % o más / menos de 70 % | la evaluación queda «aprobada» / «no aprobada», con autor y fecha |

## 8. Fundamentos de HTTP aplicados al proyecto

### 8.1 Anatomía de una solicitud y una respuesta

HTTP es el protocolo de texto con el que un cliente (el navegador) pide algo a un servidor (Django). Toda comunicación del sistema se reduce a un par solicitud–respuesta:

| Parte | Solicitud | Respuesta |
| --- | --- | --- |
| Primera línea | **Método** y **URL**: `POST /api/v1/practicas/42/reportes/` | **Código de estado**: `201 Created` |
| Cabeceras | Metadatos de la petición: `Content-Type`, `Accept`, `Authorization` | Metadatos de la respuesta: `Content-Type`, `Location`, `ETag` |
| Cuerpo | Los datos que se envían (opcional; `GET` no lleva) | La representación del recurso o del error (opcional; `204` no lleva) |

### 8.2 Métodos

| Método | Para qué | Seguro | Idempotente | Uso en el sistema |
| --- | --- | :---: | :---: | --- |
| GET | Leer un recurso | Sí | Sí | Consultar horas o el estado de las prácticas |
| POST | Crear un recurso subordinado | No | No | Registrar un reporte semanal |
| PUT | Reemplazar un recurso completo | No | Sí | Reemplazar la configuración de una carrera |
| PATCH | Modificar parte de un recurso | No | No | Cambiar el estado de una práctica |
| DELETE | Eliminar un recurso | No | Sí | Casi no se usa: el historial es inalterable (RF-10) |

*Seguro* significa que no cambia nada en el servidor. *Idempotente* significa que repetir la misma solicitud deja el mismo resultado que hacerla una vez: enviar dos veces el mismo `PUT` deja la misma configuración, pero enviar dos veces el mismo `POST` crea dos reportes. Por eso `PUT` y `PATCH` no son intercambiables: `PUT` exige enviar el recurso entero y `PATCH` solo el cambio.

### 8.3 Códigos de estado, ligados a requisitos

| Código | Significado | Cuándo aparece en el sistema |
| --- | --- | --- |
| 200 OK | La solicitud funcionó y hay cuerpo | Consultar el avance de horas (RF-05) |
| 201 Created | Se creó un recurso; `Location` indica dónde | Registrar un reporte semanal (RF-02) |
| 204 No Content | Funcionó y no hay nada que devolver | Reemplazar la configuración de la carrera (RF-12) |
| 400 Bad Request | La solicitud está mal formada | JSON con sintaxis inválida |
| 401 Unauthorized | No se sabe quién es el usuario | Solicitud sin sesión ni token (RNF-01) |
| 403 Forbidden | Se sabe quién es, pero no tiene permiso | Tutor de entidad que pide un practicante ajeno (RF-11) |
| 404 Not Found | El recurso no existe | Práctica con un identificador inexistente |
| 409 Conflict | Choca con el estado actual del recurso | Cerrar una práctica ya cerrada (RF-09) |
| 422 Unprocessable Content | Bien formada, pero viola una regla | Reporte de 11 h en una ayudantía (RF-15) |
| 500 Internal Server Error | Falla del servidor, no del cliente | Error no controlado; nunca debe ser parte del diseño |

La diferencia más útil para diseñar es **400 frente a 422**: 400 dice «no te entiendo», 422 dice «te entiendo, pero no se puede». Y **401 frente a 403**: 401 dice «identificate», 403 dice «ya sé quién sos y no te corresponde».

### 8.4 Cabeceras relevantes

| Cabecera | Va en | Para qué |
| --- | --- | --- |
| `Content-Type` | Solicitud y respuesta | Declara el formato del cuerpo, por ejemplo `application/json`. |
| `Accept` | Solicitud | El cliente indica qué formatos acepta como respuesta. |
| `Authorization` | Solicitud | Lleva la credencial, por ejemplo `Bearer <token>`. |
| `Location` | Respuesta | Indica la URL del recurso recién creado (201) o el destino de una redirección (302). |
| `ETag` | Respuesta | Identifica una versión del recurso; el cliente la reenvía en `If-None-Match` y, si no cambió, recibe `304 Not Modified` sin cuerpo. |

### 8.5 Plantillas de Django frente a una API JSON

La constitución del proyecto eligió **plantillas de Django renderizadas en el servidor** y descartó Django REST Framework para el MVP. En el sistema real, un formulario envía `application/x-www-form-urlencoded` y, si sale bien, responde `302 Found` con `Location` hacia la página siguiente; el resultado se ve en HTML, no en JSON. La actividad pide analizar JSON, así que los ejercicios individuales se escriben **como si cada recurso se expusiera en una API JSON** bajo `/api/v1/`. Las reglas de negocio y los códigos de estado son los mismos en los dos mundos; cambia el formato del cuerpo.

### 8.6 CORS

El navegador aplica la **política de mismo origen**: un script cargado desde un origen (esquema + dominio + puerto) no puede leer respuestas de otro origen salvo que el servidor lo autorice con cabeceras como `Access-Control-Allow-Origin`. Para solicitudes no simples, por ejemplo un `PATCH` con JSON, el navegador primero envía una solicitud previa `OPTIONS` (*preflight*).

**Hoy el sistema no necesita CORS**: las páginas y los datos salen del mismo servidor Django, así que todo ocurre en el mismo origen. Lo necesitaría si el equipo separa el frontend (por ejemplo, una aplicación en `app.practicas.unl.edu.ec` que consuma una API en `api.practicas.unl.edu.ec`) o si otro sistema web de la universidad consulta los datos desde el navegador. En ese caso se autorizarían solo los orígenes conocidos, nunca `*`, porque las respuestas contienen datos personales de estudiantes.

## 9. Evidencia individual

Cada integrante presenta dos requisitos corregidos, un ejercicio HTTP y una retroalimentación recibida. Las solicitudes diseñadas se marcan como tales: **el sistema aún no está implementado**, y cada una se deriva de un requisito de la especificación. La única captura real es la del endpoint `/health/`, que ya existe en el backend.

### 9.1 Alejandro Padilla

**Requisitos corregidos**

| Requisito | Antes | Después | Justificación |
| --- | --- | --- | --- |
| RF-09 | Permitir el cierre solo si la práctica cumple horas e informe final. | Cierre solo con 100 % de horas validadas, informe del estudiante revisado, informe externo y evaluación final; el cierre conserva el resultado. | El Art. 339 exige 100 % de horas y al menos 70 % de evaluación; la versión anterior permitía «cerrar bien» una práctica reprobada. |
| RF-08 | El tutor de la entidad confirma reportes y registra su informe final. | Lo mismo, solo en prácticas laborales. | El Art. 337 no exige tutor institucional en el servicio comunitario; sin esta corrección, esas prácticas nunca podían cerrarse. |

**Ejercicio HTTP (captura real, `evidencias/http-health-curl.txt`)**

```http
GET /health/ HTTP/1.1
Host: 127.0.0.1:8765
Accept: application/json

HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 16
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: same-origin

{"status": "ok"}
```

| Elemento | Interpretación |
| --- | --- |
| Método | `GET`: lectura segura e idempotente; no modifica nada. |
| Recurso | `/health/`, el chequeo de vida del servicio. |
| Cabeceras relevantes | `Accept: application/json` pide JSON y `Content-Type: application/json` confirma que el servidor lo entregó. `X-Content-Type-Options`, `X-Frame-Options` y `Referrer-Policy` las agrega Django por seguridad. |
| Cuerpo | La solicitud no tiene cuerpo; la respuesta trae 16 bytes de JSON. |
| Código de estado | `200 OK`: la solicitud funcionó y hay contenido. |
| Significado | El servidor está vivo y responde; es lo que consultaría un monitor para medir RNF-06. |

La respuesta **no trae `ETag`** porque el proyecto no activa `ConditionalGetMiddleware`. Con él, Django calcularía un `ETag` del contenido y un segundo `GET` con `If-None-Match` recibiría `304 Not Modified`, sin cuerpo. Además, la misma URL con `POST` respondió **403 Forbidden**: el middleware CSRF de Django rechaza formularios sin token antiforgery. Es un 403 real que protege a todo el sistema antes de que exista una sola regla de negocio.

**Retroalimentación recibida**

| Quién | Qué observó | Qué se cambió | Dónde se ve |
| --- | --- | --- | --- |
| Melissa Contento | Trajo el compendio actualizado del reglamento y pidió alinear la documentación. | La especificación pasó a v0.2.0: regla del Art. 339, informe del estudiante, subtipos laborales, RF-14 a RF-19. | PR #36 |

### 9.2 Jaime Landázuri

**Requisitos corregidos**

| Requisito | Antes | Después | Justificación |
| --- | --- | --- | --- |
| RF-11 | Restringir lo que cada actor puede ver y hacer según su rol. | Permitir a cada actor solo las acciones de la matriz de permisos rol × acción y rechazar cualquier otra. | «Restringir» no era verificable; cada celda de la matriz es ahora un caso de prueba (permitido o 403). |
| RNF-11 (nuevo) | — | Usar los identificadores institucionales (cédula y código de carrera). | El sistema es un módulo del sistema académico de la UNL; con los mismos identificadores, una integración futura no exige migrar datos. |

**Ejercicio HTTP (solicitud de ejemplo derivada de RF-11 y RNF-01; el sistema aún no está implementado)**

```http
GET /api/v1/practicas/42/ HTTP/1.1
Accept: application/json
Authorization: Bearer <token del tutor de la entidad B>

HTTP/1.1 403 Forbidden
Content-Type: application/json

{"detail": "No tiene permiso para ver esta práctica."}
```

```http
GET /api/v1/practicas/42/ HTTP/1.1
Accept: application/json

HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer
Content-Type: application/json

{"detail": "Debe iniciar sesión."}
```

| Elemento | Interpretación |
| --- | --- |
| Método | `GET`: se intenta leer una práctica. |
| Recurso | `/api/v1/practicas/42/`, la práctica 42, cuyo practicante pertenece a la entidad A. |
| Cabeceras relevantes | `Authorization` lleva el token que identifica al usuario; en la segunda solicitud falta, y el servidor responde con `WWW-Authenticate` para indicar cómo autenticarse. |
| Cuerpo | Ninguna solicitud lleva cuerpo; las respuestas explican el error en JSON. |
| Código de estado | `403` en la primera y `401` en la segunda. |
| Significado | Con token, el servidor sabe que es un tutor de la entidad B y le niega una práctica ajena (HU-07 #3). Sin token, ni siquiera sabe quién es. Devolver 404 en lugar de 403 sería una alternativa para no revelar que la práctica existe. |

**Retroalimentación recibida**

| Quién | Qué observó | Qué se cambió | Dónde se ve |
| --- | --- | --- | --- |
| Ivett Zaragocín | El sistema es un módulo del sistema académico que ya existe; hay que revisarlo para contrastar el diseño al prototipar. | Restricción «Integración institucional» y RNF-11; la integración técnica con el SIAAF sigue fuera del alcance. | `spec.md` v0.3.0, Restricciones y RNF-11 |

### 9.3 Ivett Zaragocín

**Requisitos corregidos**

| Requisito | Antes | Después | Justificación |
| --- | --- | --- | --- |
| RF-15 | Marcar para revisión los reportes de ayudantías que superen 10 h semanales. | Rechazar esos reportes, indicando el límite del Art. 341. | Las 10 h son un máximo legal, no una sospecha: marcar dejaba que un tutor apurado validara horas que el reglamento no permite. |
| Caso límite «horas razonables» | «El reporte se identifica para revisión», sin cifra. | Más de 40 h en una semana se marca en laboral o comunitaria; más de 10 h se rechaza en ayudantía. | Sin número no se puede probar; ahora el caso tiene un umbral para cada subtipo. |

**Ejercicio HTTP (solicitud de ejemplo derivada de RF-15; el sistema aún no está implementado)**

```http
POST /api/v1/practicas/57/reportes/ HTTP/1.1
Content-Type: application/json
Accept: application/json
Authorization: Bearer <token del estudiante>

{
  "semana": "2026-W42",
  "horas": 11,
  "actividades": "Apoyo en la organización de prácticas de laboratorio"
}

HTTP/1.1 422 Unprocessable Content
Content-Type: application/json

{"horas": ["Las ayudantías admiten hasta 10 horas semanales (Art. 341)."]}
```

| Elemento | Interpretación |
| --- | --- |
| Método | `POST`: se intenta crear un reporte semanal. |
| Recurso | `/api/v1/practicas/57/reportes/`, la colección de reportes de la práctica 57, una ayudantía de docencia. |
| Cabeceras relevantes | `Content-Type` declara que el cuerpo es JSON; `Authorization` identifica al estudiante dueño de la práctica. |
| Cuerpo | La semana ISO, las horas y la descripción de actividades. |
| Código de estado | `422 Unprocessable Content`. |
| Significado | El JSON está bien formado y el estudiante tiene permiso, pero las 11 h violan una regla del negocio; el reporte no se crea y el cuerpo dice qué campo falló. Si el cuerpo fuera `{"horas": 11` (sin cerrar), la respuesta sería **400**: el servidor ni siquiera podría leerlo. |

**Retroalimentación recibida**

| Quién | Qué observó | Qué se cambió | Dónde se ve |
| --- | --- | --- | --- |
| Doménica Rojas | Las ayudantías tienen un máximo de 10 h semanales. | El equipo decidió que el sistema rechace más de 10 h (RF-15 y HU-02 #3). | `spec.md` v0.3.0, RF-15 |

### 9.4 Melissa Contento

**Requisitos corregidos**

| Requisito | Antes | Después | Justificación |
| --- | --- | --- | --- |
| Tabla de actores | «Tutor de la entidad» y «coordinador» con descripciones generales. | Cada actor con su nombre en el reglamento: tutor institucional (Art. 337), docente responsable de prácticas (Art. 335) y tutor académico (Art. 336), con sus funciones. | Los nombres y funciones deben coincidir con la norma; así se notó que el tutor institucional no existe en el servicio comunitario. |
| RF-06 | Mostrar al coordinador el estado de todas las prácticas de su carrera. | Mostrar por práctica estudiante, tipo, estado, horas validadas, en revisión y requeridas, alertas activas y tutor. | «El estado» era ambiguo; ahora se puede comprobar campo por campo. |

**Ejercicio HTTP (solicitud de ejemplo derivada de RF-02; el sistema aún no está implementado)**

```http
POST /api/v1/practicas/42/reportes/ HTTP/1.1
Content-Type: application/json
Accept: application/json
Authorization: Bearer <token del estudiante>

{
  "semana": "2026-W42",
  "horas": 8,
  "actividades": "Levantamiento de requisitos con el área de sistemas"
}

HTTP/1.1 201 Created
Content-Type: application/json
Location: /api/v1/practicas/42/reportes/7/

{"id": 7, "semana": "2026-W42", "horas": 8, "estado": "en_revision"}
```

| Elemento | Interpretación |
| --- | --- |
| Método | `POST`: se crea un recurso nuevo dentro de una colección. |
| Recurso | `/api/v1/practicas/42/reportes/`, los reportes de la práctica 42. |
| Cabeceras relevantes | `Content-Type` y `Accept` acuerdan JSON en los dos sentidos; `Authorization` identifica al estudiante. |
| Cuerpo | Semana, horas y actividades; la respuesta devuelve el reporte creado. |
| Código de estado | `201 Created`: más preciso que 200, porque indica que se creó algo. |
| Significado | El reporte existe y queda «en revisión»: sus horas todavía no cuentan (HU-02 #2). `Location` da la URL del nuevo reporte, para que el cliente lo consulte sin adivinar su identificador. |

**Retroalimentación recibida**

| Quién | Qué observó | Qué se cambió | Dónde se ve |
| --- | --- | --- | --- |
| Alejandro Padilla y Jaime Landázuri | Había que definir bien cada actor. | El equipo analizó el reglamento, discutió cada actor y lo contrastó con los requisitos; la tabla de actores quedó con nombres y artículos del reglamento. | `spec.md`, sección 2 (PR #36) |

### 9.5 Doménica Rojas

**Requisitos corregidos**

| Requisito | Antes | Después | Justificación |
| --- | --- | --- | --- |
| RF-07 | Alertas por reportes no enviados, revisiones pendientes y horas rezagadas. | Se suman los incumplimientos reportados por el tutor de la entidad (RF-18). | El Art. 337 obliga al tutor institucional a reportar incumplimientos; sin alerta, el aviso se perdía por teléfono o correo. |
| RF-02 | Registrar actividades con horas y adjuntar evidencias. | Las evidencias siguen los formatos y el tamaño de RNF-05 (PDF, JPG o PNG hasta 10 MB). | «Adjuntar evidencias» no permitía probar qué se acepta y qué se rechaza. |

**Ejercicio HTTP (solicitudes de ejemplo derivadas de RF-09 y RF-12; el sistema aún no está implementado)**

```http
PATCH /api/v1/practicas/42/ HTTP/1.1
Content-Type: application/json
Authorization: Bearer <token del coordinador>

{"estado": "cerrada"}

HTTP/1.1 409 Conflict
Content-Type: application/json

{"detail": "La práctica ya está cerrada y no admite cambios."}
```

```http
PUT /api/v1/carreras/computacion/configuracion/ HTTP/1.1
Content-Type: application/json
Authorization: Bearer <token del coordinador>

{
  "horas_laborales": 240,
  "horas_comunitarias": 120,
  "plazo_reporte_dias": 3,
  "plazo_revision_dias_habiles": 5,
  "umbral_rezago": 0.8
}

HTTP/1.1 204 No Content
```

| Elemento | Interpretación |
| --- | --- |
| Método | `PATCH` modifica solo el estado de la práctica; `PUT` reemplaza la configuración completa de la carrera. |
| Recurso | La práctica 42 y la configuración de la carrera de Computación. |
| Cabeceras relevantes | `Content-Type: application/json` en ambas; `Authorization` identifica al coordinador, único rol que puede hacerlo. |
| Cuerpo | En el `PATCH`, solo el campo que cambia; en el `PUT`, todos los campos, porque reemplaza el recurso entero. |
| Código de estado | `409 Conflict` y `204 No Content`. |
| Significado | La práctica 42 ya está `cerrada`: la solicitud es válida, pero choca con el estado actual, y por eso es 409 y no 422. La configuración se guardó y no hay nada que devolver, por eso es 204 sin cuerpo. Repetir el mismo `PUT` deja la misma configuración, porque es idempotente. |

**Retroalimentación recibida**

| Quién | Qué observó | Qué se cambió | Dónde se ve |
| --- | --- | --- | --- |
| Alejandro Padilla y Jaime Landázuri | Había que definir bien cada actor. | Al contrastar los actores con los requisitos apareció la obligación del tutor institucional de reportar incumplimientos, que hoy está en RF-07 y RF-18. | `spec.md`, RF-07 y RF-18 (PR #36) |

## 10. Retroalimentación recibida y ajustes

| # | Retroalimentación | Quién la dio | Ajuste realizado | Evidencia |
| :---: | --- | --- | --- | --- |
| O1 | Definir bien cada actor. | Alejandro Padilla y Jaime Landázuri | Análisis del reglamento actor por actor y contraste con los requisitos; tabla de actores con artículos. | PR #36 |
| O2 | El reglamento cambió; actualizar la documentación. | Melissa Contento | Especificación v0.2.0 alineada con el reglamento. | PR #36 |
| O3 | Las ayudantías tienen un máximo de 10 h semanales. | Doménica Rojas | Se discutió y se decidió que el sistema rechace más de 10 h. | `spec.md` v0.3.0, RF-15 |
| O4 | El sistema es un módulo del sistema académico existente. | Ivett Zaragocín | Restricción de integración institucional y RNF-11. | `spec.md` v0.3.0 |

## 11. Distribución de aportes

| Integrante | Aporte principal | Evidencia |
| --- | --- | --- |
| Jaime Landázuri | Observación sobre actores y análisis del reglamento actor por actor. | Sección 9.2 |
| Ivett Zaragocín | Observación sobre el sistema académico existente. | Sección 9.3 |
| Alejandro Padilla | Observación sobre actores; actualización de la especificación y captura HTTP real. | Sección 9.1, PR #36 |
| Doménica Rojas | Observación sobre el tope de 10 h en ayudantías. | Sección 9.5 |
| Melissa Contento | Compendio del reglamento y actualización de la documentación. | Sección 9.4, PR #36 |

## 12. Declaración de uso de IA

| Integrante | Herramienta | Uso | Revisión humana |
| --- | --- | --- | --- |
| Jaime Landázuri | NotebookLM | Consulta del reglamento cargado como fuente para analizar las funciones de cada actor. | El equipo discutió cada actor y decidió los cambios. |
| Alejandro Padilla | Claude (Anthropic), asistente en terminal | Borrador de los requisitos no funcionales, de la revisión de calidad y de este documento a partir de las decisiones del equipo. | Revisión y aprobación del contenido; cada integrante revisa su sección individual. |

El detalle está en `docs/declaracion-ia.md` del repositorio.

## Bibliografía / Referencias

[1] R. Fielding, M. Nottingham, and J. Reschke, "HTTP Semantics," RFC 9110, IETF, Jun. 2022. doi: 10.17487/RFC9110

[2] ISO/IEC/IEEE 29148:2018, *Systems and software engineering — Life cycle processes — Requirements engineering*, 2018.

[3] W3C, "Web Content Accessibility Guidelines (WCAG) 2.1," W3C Recommendation, 2018.

[4] WHATWG, "Fetch Standard — CORS protocol," Living Standard. https://fetch.spec.whatwg.org/

[5] Universidad Nacional de Loja, *Reglamento de Régimen Académico*, Consejo Superior Universitario, 2021.

[6] Django Software Foundation, "Cross Site Request Forgery protection," Django 5.2 documentation. https://docs.djangoproject.com/en/5.2/ref/csrf/
