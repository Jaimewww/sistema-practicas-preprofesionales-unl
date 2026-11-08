# Análisis del proceso: reporte semanal de actividades

| Campo | Valor |
| --- | --- |
| **Proceso** | Reporte semanal de actividades de una práctica preprofesional |
| **Diagrama** | [`proceso-reporte-semanal.bpmn`](proceso-reporte-semanal.bpmn) (BPMN 2.0.2, vista operativa) |
| **Fuentes** | [`spec.md`](../../specs/001-seguimiento-practicas/spec.md) (HU-02 a HU-04, HU-06 a HU-08, RF-01 a RF-19, CU-01, CU-03, Clarifications), [`api.md`](../api.md), `backend/apps/prototipo/` (`forms.py`, `facade.py`, `validaciones.py`) |
| **Estado** | Análisis previo al diagrama (Sumativa 1, issue #83) |

> [!NOTE]
> Este análisis se escribe **antes** del diagrama y cubre los siete elementos del modelado: participantes, eventos, actividades, decisiones, flujos, datos y excepciones. Cada regla cita su RF, HU o artículo; lo que el prototipo todavía no implementa se marca como **pendiente**. Nada del modelo se inventa fuera de esas fuentes.

## Alcance

**Inicia** cuando cierra la semana de práctica y el estudiante debe reportarla. **Termina** cuando el reporte queda validado (con las horas sumadas al acumulado), devuelto al estudiante o rechazado, y cuando el acumulado de horas validadas alcanza el total requerido y la práctica pasa a `en revisión final`.

**Queda fuera:** el plan de actividades (RF-01), el informe final, la evaluación y el cierre (RF-09, CU-02), la suspensión o cancelación (RF-13) y el informe consolidado (RF-19). El cierre se menciona solo como destino del último gateway.

## 1. Participantes

| Participante | Tipo | Rol en el proceso | Fuente |
| --- | --- | --- | --- |
| **Estudiante** | Pool | Registra el reporte semanal, corrige lo rechazado o devuelto, consulta sus horas y recibe alertas. | HU-02, HU-04, HU-06 |
| **Sistema de seguimiento de prácticas** | Pool con 2 lanes | Verifica reglas, registra, notifica, acumula horas y genera alertas. | RF-02 a RF-05, RF-07 |
| ↳ Lane **Gestión de reportes** | Lane | Recepción, verificación, validación y acumulado de horas; incluye el registro de la confirmación de la entidad. | RF-02, RF-03, RF-04, RF-05, RF-08 |
| ↳ Lane **Control de atrasos** | Lane | Verificación diaria de plazos y rezago. | RF-07, RF-12, CU-03 |
| **Tutor académico** | Pool | Revisa el reporte y lo valida o lo devuelve con observación; atiende alertas. | RF-03, HU-03, CU-01 |
| **Tutor de la entidad receptora** | Pool | Confirma el reporte semanal (solo práctica laboral). | RF-08, HU-07, Art. 337 |
| **Coordinador de prácticas** | Pool colapsado (caja negra) | Recibe la alerta de atraso. Su otra acción, cerrar la práctica (RF-09), es otro proceso. | RF-06, RF-07, HU-06 |

La **Secretaría** y el **director** no intervienen: la matriz de permisos de RF-11 no les asigna acciones sobre el reporte semanal. El sistema se modela como pool propio porque las reglas, las notificaciones y las alertas las ejecuta él, no una persona.

## 2. Eventos

### Inicio

| ID | Evento | Tipo | Motivo |
| --- | --- | --- | --- |
| `E_s0` | Cierra la semana de práctica | Inicio con temporizador (ciclo semanal `R/P1W`) | Reporte semanal (S-03, HU-02). |
| `A1` | Reporte semanal recibido | Inicio por mensaje | El estudiante envía el reporte (`POST …/reportes/`). |
| `B1` | Confirmación de la entidad recibida | Inicio por mensaje | El tutor de la entidad confirma (HU-07, criterio 2). |
| `C0` | Llega la verificación diaria | Inicio con temporizador (ciclo diario `R/P1D`) | CU-03: el sistema revisa «al menos una vez al día». |
| `N_s0`, `T_s0` | Reporte por confirmar / pendiente de revisión recibido | Inicio por mensaje | Notificaciones del sistema. |
| `E_s1`, `T_s1` | Alerta de atraso / alerta recibida | Inicio por mensaje | HU-06. |

### Intermedios

| ID | Evento | Tipo | Motivo |
| --- | --- | --- | --- |
| `E_c1` | Rechazo recibido | Captura de mensaje (tras gateway basado en eventos) | El sistema rechazó el reporte (403, 409 o 422). |
| `E_c2` | Devolución recibida | Captura de mensaje | El tutor devolvió el reporte (HU-03, criterio 2). |
| `E_c3` | Validación recibida | Captura de mensaje | El tutor validó el reporte (HU-03, criterio 1). |
| `A8b` | Vence plazo de revisión (5 días hábiles) | **Temporizador de frontera no interruptor** sobre «Esperar decisión del tutor académico» (`P5D`) | HU-06 criterio 2: revisión sin hacer más allá del plazo. El plazo es configurable por carrera (RF-12). No interrumpe la espera: la alerta se emite y el sistema sigue esperando la decisión. |

El **plazo de reporte** (3 días tras cerrar la semana, configurable) y el **umbral de rezago** (80 %, configurable) no son temporizadores de frontera: los evalúa el sistema en la verificación diaria `C0`, que es la forma en que CU-03 los define.

### Fin

| ID | Evento | Tipo | Resultado |
| --- | --- | --- | --- |
| `A3e` | Reporte rechazado | **Fin con error** (`REPORTE_RECHAZADO`) | Excepción: el reporte no se registra. |
| `A11e`, `T_e2` | Reporte devuelto | Fin | El reporte vuelve al estudiante. |
| `A16e` | Semana validada, horas pendientes | Fin | Las horas suman, pero faltan para el total. |
| `A15e` | Práctica en revisión final | Fin | Horas completas; el cierre sigue en CU-02. |
| `A9e` | Alerta de revisión emitida | Fin | RF-07. |
| `C4e`, `C5e`, `C6e` | Alerta de atraso emitida / Sin atraso / Alerta ya vigente | Fin | CU-03 (flujos principal, 4a y 4b). |
| `B3`, `N_e1`, `T_e1`, `E_e1`, `E_e2`, `T_e3` | Confirmación registrada / enviada, reporte validado, semana reportada y validada, atraso conocido, alerta atendida | Fin | Cierres de los demás carriles. |

## 3. Actividades

Todas las tareas siguen la convención **verbo en infinitivo + complemento**. El tipo BPMN indica quién las ejecuta.

| ID | Actividad | Tipo | Participante |
| --- | --- | --- | --- |
| `E_t1` | Registrar reporte semanal | Usuario | Estudiante |
| `E_t4` | Corregir datos del reporte | Usuario | Estudiante |
| `E_t2` | Revisar observaciones del tutor | Usuario | Estudiante |
| `E_t5` | Consultar horas validadas acumuladas | Usuario | Estudiante |
| `E_t6` | Revisar alerta de atraso | Usuario | Estudiante |
| `A2` | Verificar reglas del reporte | Servicio | Sistema |
| `A3` | Rechazar reporte con mensaje de error | Envío | Sistema |
| `A4` | Registrar reporte en revisión | Servicio | Sistema |
| `A5` | Marcar reporte para revisión del tutor | Servicio | Sistema |
| `A7` | Notificar reporte al tutor de la entidad | Envío | Sistema |
| `A6` | Notificar reporte al tutor académico | Envío | Sistema |
| `A8` | Esperar decisión del tutor académico | Recepción | Sistema |
| `A9` | Emitir alerta de revisión pendiente | Envío | Sistema |
| `A10` | Registrar devolución con observación | Servicio | Sistema |
| `A11` | Devolver reporte al estudiante | Envío | Sistema |
| `A12` | Registrar validación con autor y fecha | Servicio | Sistema |
| `A13` | Sumar horas al acumulado validado | Servicio | Sistema |
| `A14` | Notificar validación al estudiante | Envío | Sistema |
| `A15` | Pasar práctica a revisión final | Servicio | Sistema |
| `B2` | Registrar confirmación de la entidad | Servicio | Sistema |
| `C2` | Calcular horas esperadas a la fecha | Servicio | Sistema |
| `C3` | Verificar reportes vencidos y horas rezagadas | Servicio | Sistema |
| `C4` | Notificar alerta de atraso | Envío | Sistema |
| `T_t1` | Revisar actividades, horas y evidencias | Usuario | Tutor académico |
| `T_t2` | Validar horas reportadas | Usuario | Tutor académico |
| `T_t3` | Devolver reporte con observaciones | Usuario | Tutor académico |
| `T_t4` | Atender alerta del sistema | Usuario | Tutor académico |
| `N_t1` | Confirmar reporte semanal | Usuario | Tutor de la entidad |

## 4. Decisiones (gateways)

Todos los gateways son **exclusivos**, salvo el primero del estudiante, que es **basado en eventos**. Los gateways sin nombre (`E_m1`, `GA2m`, `GA3m`) solo reúnen flujos.

| Gateway | Pregunta | Condiciones | Fuente |
| --- | --- | --- | --- |
| `E_g1` (por eventos) | ¿Qué responde el sistema? | Gana el primer mensaje: rechazo, devolución o validación. | HU-02, HU-03 |
| `GA1` | ¿Reporte cumple las reglas? | **Sí:** práctica `en_curso`, plan validado, semana libre, horas ≥ 1, ayudantía ≤ 10 h, evidencias PDF ≤ 5 MB, práctica propia. **No:** se rechaza. | RF-02, RF-11, RF-15, RNF-05 |
| `GA2` | ¿Supera 40 horas sin ser ayudantía? | **Sí:** horas > 40 en práctica laboral no ayudantía o en comunitaria → se marca para revisión del tutor. **No:** sigue. | HU-02 criterio 4, COR-07 |
| `GA3` | ¿Práctica laboral con tutor de entidad? | **Sí:** se notifica también al tutor de la entidad. **No** (comunitaria): solo el tutor académico. | RF-08, Art. 337 |
| `GA4` | ¿Decisión del tutor académico? | **Validado** (`aprobado`) o **Devuelto** (`devuelto` con observación). | RF-03 |
| `GA5` | ¿Horas validadas alcanzan el total requerido? | **Sí:** `horas_validadas >= horas_requeridas` → pasa a `en revisión final`. **No:** la práctica sigue `en curso`. Solo cuentan horas validadas (S-04); no se acreditan fracciones (Art. 339). | RF-05, RF-09, HU-08 |
| `T_g1` | ¿Reporte cumple lo reportado? | Decisión humana del tutor tras revisar actividades, horas y evidencias. | CU-01 paso 4 |
| `GC1` | ¿Hay atraso? | **Sí:** reporte sin enviar tras el plazo, o horas validadas + en revisión < 80 % de las esperadas. | RF-07, HU-06, CU-03 |
| `GC2` | ¿Existe alerta activa por la misma causa? | **Sí:** no se genera otra (CU-03, 4b). **No:** se notifica. | CU-03 |

## 5. Flujos

### Flujos de secuencia (resumen por carril)

| Carril | Recorrido principal |
| --- | --- |
| **Estudiante** | Cierra la semana → Registrar reporte semanal → espera la respuesta → (rechazo → Corregir datos → vuelve a registrar) o (devolución → Revisar observaciones → vuelve a registrar) o (validación → Consultar horas → fin). |
| **Sistema, reporte** | Recibir → Verificar reglas → (cumple) Registrar en revisión → ¿> 40 h? → ¿laboral? → Notificar al tutor académico → Esperar decisión → (devuelto) Registrar devolución → Devolver al estudiante, o (validado) Registrar validación → Sumar horas → Notificar al estudiante → ¿horas completas? → Pasar a revisión final. |
| **Sistema, confirmación** | Confirmación de la entidad recibida → Registrar confirmación → fin. Es independiente de la validación del tutor académico: la especificación no exige confirmar antes de validar. |
| **Sistema, atrasos** | Verificación diaria → Calcular horas esperadas → Verificar reportes vencidos y horas rezagadas → ¿atraso? → ¿alerta activa? → Notificar alerta. |
| **Tutor académico** | Reporte recibido → Revisar → ¿cumple? → Validar o Devolver con observaciones. |
| **Tutor de la entidad** | Reporte por confirmar → Confirmar reporte semanal. |

Los **bucles de corrección** del estudiante vuelven al gateway de unión antes de «Registrar reporte semanal»: es el reenvío de una semana `devuelta` (docs/api.md §5, «Reenvío»).

### Flujos de mensaje (13)

| ID | De → A | Mensaje |
| --- | --- | --- |
| `MF_01` | Estudiante → Sistema | Reporte semanal enviado |
| `MF_02` | Sistema → Estudiante | Rechazo con mensaje de error |
| `MF_03` | Sistema → Estudiante | Reporte devuelto con observaciones |
| `MF_04` | Sistema → Estudiante | Validación notificada |
| `MF_05` | Sistema → Tutor académico | Reporte pendiente de revisión |
| `MF_06` | Sistema → Tutor de la entidad | Reporte por confirmar |
| `MF_07` | Tutor de la entidad → Sistema | Confirmación del reporte |
| `MF_08` | Tutor académico → Sistema | Decisión: validado |
| `MF_09` | Tutor académico → Sistema | Decisión: devuelto con observación |
| `MF_10` | Sistema → Tutor académico | Alerta de revisión pendiente |
| `MF_11` | Sistema → Tutor académico | Alerta de atraso |
| `MF_12` | Sistema → Estudiante | Alerta de atraso |
| `MF_13` | Sistema → Coordinador | Alerta de atraso |

## 6. Datos

| Elemento | Tipo BPMN | Contenido | Fuente |
| --- | --- | --- | --- |
| Reporte semanal | Objeto de datos (salida de «Registrar reporte semanal») | `semana`, `actividades` (una por línea), `horas`, `evidencias` (PDF). | docs/api.md §5 |
| Observación de devolución | Objeto de datos (salida de «Devolver reporte con observaciones») | Texto obligatorio, hasta 500 caracteres. | `validaciones.py` (`LIMITE_OBSERVACION`), RF-03 |
| Registro de prácticas, reportes y horas | Almacén de datos (3 referencias) | Estado del reporte (`en_revision`, `validado`, `devuelto`), `validado_por`, `validado_el`, versiones con observación, `horas_validadas`, `horas_en_revision`, `horas_requeridas`, alertas. | RF-04, RF-05, RF-10 |

> [!IMPORTANT]
> En el prototipo actual **no hay base de datos** para este flujo: los reportes viven en la sesión del cliente y las decisiones del tutor en una cookie firmada (docs/api.md §5 y §6). El almacén del diagrama representa el modelo objetivo; la persistencia compartida es **pendiente #78**.

## 7. Excepciones

| Excepción | Dónde se detecta | Tratamiento | Respuesta del API / fuente |
| --- | --- | --- | --- |
| **Reporte devuelto** | `GA4` → «Registrar devolución con observación» | La observación es obligatoria; el reporte pasa a `devuelto`, las horas no cuentan y el estudiante lo corrige y reenvía; cada versión se conserva (RF-10). | `PATCH …/pendientes/<clave>/` con `devuelto` sin observación → `422`; documento ya revisado → `409`. |
| **Archivo inválido** | `GA1` (en «Verificar reglas del reporte») | Fin con error `Reporte rechazado`; no cambia ningún dato; el estudiante corrige y reenvía. | `422 dato_invalido` con `error.campos`: archivo no PDF o de más de 5 MB (RNF-05). |
| **Exceso de horas** | `GA1` (ayudantía) y `GA2` (laboral/comunitaria) | Ayudantía con más de 10 h semanales: se **rechaza** e indica el Art. 341 (10 h se aceptan). Más de 40 h en otra práctica: se **registra** y se marca para revisión del tutor. Horas < 1: se rechaza. | `422` (RF-15); la marca de > 40 h es **pendiente** (no está en el código). |
| **Práctica ajena** | `GA1` y decisión del tutor | El sistema responde 403 y no cambia nada (RNF-02). | `403 fuera_de_rol`: otro estudiante, otro tutor o un rol distinto. |
| **Práctica o semana no admite el reporte** | `GA1` | Práctica que no está `en_curso`, sin plan aprobado o semana ya enviada. | `409 transicion_invalida`. |
| **Atraso** | `A8b` (revisión) y `GC1` (reporte y horas) | Se alerta sin interrumpir la espera ni duplicar alertas activas (CU-03, 4b). Las prácticas suspendidas, canceladas o cerradas no se evalúan. | `GET /prototipo/api/v1/alertas/`. |
| **Decisión del tutor repetida** | «Esperar decisión del tutor académico» | Un documento ya decidido no se vuelve a decidir. | `409 transicion_invalida`. |

## 8. Trazabilidad: actividad → requisito → endpoint o código

«Existente» significa que lo cubre el prototipo con datos sintéticos (solo `DEBUG=True`, docs/api.md). «Pendiente #78» marca lo que el prototipo no implementa o solo simula, y que depende de la persistencia real.

| Actividad | RF / HU | Endpoint o código | Estado |
| --- | --- | --- | --- |
| Registrar reporte semanal | RF-02, RF-15, RNF-05 · HU-02 | `POST /api/v1/practicas/<id>/reportes/` · `facade.registrar_reporte` · pantalla E4 | Existente |
| Corregir datos del reporte | RF-02 · HU-02 | El mismo `POST` (reenvío de la semana `devuelta`) | Existente |
| Revisar observaciones del tutor | RF-03 · HU-03 (2) | `GET /api/v1/practicas/<id>/` (reporte con `observacion` y `versiones`) | Existente |
| Consultar horas validadas acumuladas | RF-05 · HU-04 | `GET /api/v1/practicas/<id>/` (`horas_validadas`, `horas_en_revision`, `horas_requeridas`) | Existente |
| Revisar alerta de atraso | RF-07 · HU-06 | `GET /prototipo/api/v1/alertas/` | Existente |
| Verificar reglas del reporte | RF-02, RF-11, RF-15, RNF-05 · HU-02 | `facade.registrar_reporte` · `forms.ReporteSemanalForm` (`clean_horas`, `clean_evidencias`) | Existente |
| Rechazar reporte con mensaje de error | RNF-02, RNF-05, RF-15 | Contrato de errores 403 / 409 / 422 (docs/api.md §2 y §5) | Existente |
| Registrar reporte en revisión | RF-02 · HU-02 (1, 2) | Respuesta `201` del mismo `POST` (estado `en_revision`) | Existente |
| Marcar reporte para revisión del tutor | HU-02 (4), COR-07 | Sin código (ninguna regla de 40 h en `forms.py` ni `facade.py`) | Pendiente #78 |
| Notificar reporte al tutor académico | RF-03 · HU-03 | Bandeja T1 `/prototipo/tutor/pendientes/`; sin endpoint API de listado | Existente (pantalla) · API pendiente #78 |
| Notificar reporte al tutor de la entidad | RF-08 · HU-07 | `/prototipo/entidad/reportes/` (pantalla) | Existente (pantalla) · API pendiente #78 |
| Esperar decisión del tutor académico | RF-03 · HU-03 | `PATCH /prototipo/api/v1/pendientes/<clave>/` | Existente |
| Emitir alerta de revisión pendiente | RF-07 · HU-06 (2) | `GET /prototipo/api/v1/alertas/` (se calcula al consultar; sin proceso periódico) | Existente (lectura) · generación periódica pendiente #78 |
| Registrar devolución con observación | RF-03, RF-04 · HU-03 (2) | `PATCH …/pendientes/<clave>/` `{"decision": "devuelto", "observacion": …}` · `validaciones._decision_valida` | Existente |
| Devolver reporte al estudiante | HU-03 (2) | Visible en `GET /api/v1/practicas/<id>/`; sin notificación activa | Existente (consulta) |
| Registrar validación con autor y fecha | RF-04 · HU-03 (1), CE-02 | `PATCH …/pendientes/<clave>/` `{"decision": "aprobado"}` (`validado_por`, `validado_el`) | Existente |
| Sumar horas al acumulado validado | RF-05 · HU-04 | Proyección de `horas_validadas` en `GET /api/v1/practicas/<id>/` | Existente (simulado en cookie) |
| Notificar validación al estudiante | HU-04 (1) | Se consulta en `GET /api/v1/practicas/<id>/` | Existente (consulta) |
| Pasar práctica a revisión final | Estados de la práctica · RF-09 · HU-08 | Sin código (el cierre lo exige desde `en_revision_final`, pero nada la alcanza) | Pendiente #78 |
| Registrar confirmación de la entidad | RF-08 · HU-07 (2) | `/prototipo/entidad/practicas/<id>/reportes/<semana>/` (pantalla, `views.confirmar_reporte`) | Existente (pantalla) · API pendiente #78 |
| Calcular horas esperadas a la fecha | RF-07, RF-12 · CU-03 | Regla de rezago detrás de `GET /prototipo/api/v1/alertas/` | Existente (lectura) |
| Verificar reportes vencidos y horas rezagadas | RF-07, RF-12 · HU-06 · CU-03 | `GET /prototipo/api/v1/alertas/` (plazo de reporte 3 días, revisión 5 días hábiles, umbral 80 %) | Existente (lectura) |
| Notificar alerta de atraso | RF-07 · HU-06 · CU-03 | `GET /prototipo/api/v1/alertas/` por rol: estudiante, tutor académico y coordinador | Existente (lectura) · notificación activa pendiente #78 |
| Revisar actividades, horas y evidencias | HU-03 · CU-01 | `GET /api/v1/practicas/<id>/` · pantalla T2 `/prototipo/tutor/pendientes/<clave>/` | Existente |
| Validar horas reportadas | RF-03, RF-04 · HU-03 (1) | `PATCH …/pendientes/<clave>/` `aprobado` | Existente |
| Devolver reporte con observaciones | RF-03 · HU-03 (2) | `PATCH …/pendientes/<clave>/` `devuelto` | Existente |
| Atender alerta del sistema | RF-07 · HU-06 | `GET /prototipo/api/v1/alertas/` | Existente |
| Confirmar reporte semanal | RF-08 · HU-07 (2) | Pantalla de confirmación de la entidad | Existente (pantalla) · API pendiente #78 |

> [!NOTE]
> «#78» es el marcador acordado en el plan de la Sumativa 1 para lo que el prototipo solo simula o no tiene todavía. Confirmar el alcance exacto de ese issue antes de citarlo en el portal.

## 9. Cobertura de los siete elementos

| Elemento | Sección | En el diagrama |
| --- | --- | --- |
| Participantes | §1 | 5 pools, 2 lanes |
| Eventos | §2 | 8 de inicio, 3 intermedios + 1 de frontera, 15 de fin |
| Actividades | §3 | 28 tareas con nombre verbo + complemento |
| Decisiones | §4 | 11 gateways exclusivos y 1 basado en eventos |
| Flujos | §5 | 62 flujos de secuencia y 13 de mensaje |
| Datos | §6 | 2 objetos de datos y 1 almacén (3 referencias) |
| Excepciones | §7 | Fin con error, bucles de corrección y alertas |
