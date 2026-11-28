# Reportes: registro, evidencias, validación y horas acumuladas (#78, #122, #124, #126, #157)

`ReporteSemanal` (HU-02/RF-02) y el endpoint que lo registra, más las dos rutas de
lectura de prácticas que lo acompañan en el contrato de #78, la validación del
tutor (#122/#124), las horas acumuladas (#126) y, desde C-03 (#157), las
actividades de la semana con evidencias PDF privadas y versionadas (RNF-05). No
incluye rezago, alertas ni informe final.

## Ruta rápida

1. Modelo: `backend/apps/reportes/models.py` (`ReporteSemanal`, `EvidenciaReporte`,
   `MENSAJE_AYUDANTIA`).
2. Serializers y endpoints: `backend/apps/reportes/serializers.py` (`ReporteSemanalSerializer`,
   `ReporteConEvidenciasSerializer`, `ReenvioConEvidenciasSerializer`) y
   `backend/apps/reportes/api.py` (`ReportePracticaView`, `ReporteDetalleView`,
   `DescargaEvidenciaView`, `HorasPracticaView`).
3. Servicios: `backend/apps/reportes/services.py` (`validar_reporte`,
   `devolver_reporte`, `reenviar_reporte`, `horas_practica`, `guardar_evidencias`,
   `evidencias_atomicas`, `version_actual`, `devoluciones_de`).
4. Lecturas de prácticas: `backend/apps/practicas/api.py` (`PracticaCardSerializer`,
   `PracticasListaView`, `PracticaDetalleView`).
5. Rutas: `backend/config/urls.py` (van **antes** del demo del prototipo).
6. Migraciones: `backend/apps/reportes/migrations/0001_reportesemanal.py`,
   `0002_requiere_revision_y_tope_semanal.py`, `0003_ingreso_revision_en.py` y
   `0004_evidencias_y_actividades.py`
   (más
   `backend/apps/actividades/migrations/0003_validacion_reporte.py` y la fusión
   `0004_merge_...` con la 0003 de #98).
7. Pruebas: `backend/tests/unit/test_reportes.py` (modelo y migración),
   `backend/tests/integration/test_reportes_flujo.py` (flujo completo con `APIClient`)
   , `backend/tests/integration/test_horas_acumuladas.py` (fórmula y alcance) y
   `backend/tests/integration/test_evidencias_reporte.py` (C-03: multipart, reenvío
   con PDFs, lista, detalle ampliado, descarga y OpenAPI).

Fuente: `specs/001-seguimiento-practicas/data-model.md` (`ReporteSemanal`,
`Validacion`), RF-02/RF-15 y T026-T027 en `specs/001-seguimiento-practicas/tasks.md`.

## Campos y reglas

| Campo | Tipo | Regla |
| --- | --- | --- |
| `practica` | FK a `practicas.Practica` | Obligatorio; `PROTECT`; `practica.reportes` |
| `semana` | entero positivo | Desde 1; una sola versión activa por semana |
| `horas_reportadas` | entero positivo | De 1 a 168 (una semana no tiene más horas); `PositiveIntegerField` admite 0, el validador no |
| `fecha_registro` | fecha y hora | Automática al insertar (`auto_now_add`) |
| `estado` | `en_revision`, `validado` o `devuelto` | Inicia `en_revision` |
| `requiere_revision` | booleano, no editable | `True` si `horas_reportadas` > 40; lo calcula `save()` |
| `ingreso_revision_en` | fecha y hora nullable, no editable | Ingreso a revisión fijado por el servidor; `NULL` si se desconoce |
| `actividades` | texto, vacío por defecto | Obligatorio y no vacío en el alta multipart (C-03); el alta JSON lo deja vacío |

No hay `contenido` ni `version`: el data-model no los define para un reporte y esta
unidad no los inventa. La versión de cada entrega vive en `EvidenciaReporte.version`
(ver «Evidencias PDF»).
`UniqueConstraint` sobre `(practica, semana)` impone «una sola versión activa por semana»
también en la base, así que `objects.create()` duplicado falla con `IntegrityError`.
La semana es un entero libre: el calendario del período no se recalcula aquí (el
prototipo muestra `Semana n (dd/mm - dd/mm)`; esa derivación queda fuera de la unidad).

## Endpoints

| Método y ruta | Alcance | Respuesta |
| --- | --- | --- |
| `GET /api/v1/practicas/` | `practicas_visibles_para` (T019) del actor | 200 con la lista de tarjetas |
| `GET /api/v1/practicas/{id}/` | La misma consulta acotada | 200 con la tarjeta, 404 fuera de alcance |
| `GET /api/v1/practicas/{id}/reportes/` | `practicas_visibles_para` (T019) del actor | 200 con la lista de detalles ampliados por semana; 401, 404 |
| `POST /api/v1/practicas/{id}/reportes/` | Solo el estudiante dueño, práctica «en curso» | 201 con el reporte; 400, 401, 403, 404, 409. JSON legado o multipart con evidencias |
| `POST /api/v1/reportes/{id}/reenviar/` | Solo el estudiante dueño, reporte «devuelto» | 200 con la tarjeta; 400 (multipart), 401, 403, 404, 409. Sin cuerpo o multipart con PDFs nuevos |
| `GET /api/v1/reportes/{id}/` | `practicas_visibles_para` (T019) del actor | 200 con el reporte, la devolución y el detalle ampliado; 401, 404 |
| `GET /api/v1/reportes/{id}/evidencias/{evidencia_id}/` | `practicas_visibles_para` (T019) del actor | 200 `application/pdf` adjunto; 401, 404 |
| `GET /api/v1/practicas/{id}/horas/` | `practicas_visibles_para` (T019) del actor | 200 con las horas acumuladas; 401, 404 |

La tarjeta (`PracticaCardSerializer`) expone `id`, `estudiante_id`, `tipo`, `subtipo`,
`estado` y `horas_requeridas`: lo mínimo para listar sin filtrar motivos ni proyecto.
El envelope (`success`, `message`, `data`, `errors`, `meta`) es el de #77 y no se
reimplementa aquí. El cuerpo del POST es exactamente `semana` y `horas_reportadas`;
cualquier otro campo —`contenido` incluido— se rechaza con 400 en su clave.

Desde #79 las tres rutas exigen JWT (`Authorization: Bearer`): sin credenciales
responden 401, el rol sin permiso recibe 403 y el POST del reporte solo admite al
estudiante dueño —ver `backend/apps/seguridad/README.md`—; los 400/404 de abajo siguen
siendo la validación de negocio ya autenticada.

## Ingreso a revisión (T8, RF-07)

`ingreso_revision_en` es un dato **interno** con el que el servidor registra cuándo
entró la fila a revisión, para que el plazo de revisión (HU-06/CU-03) tenga un ancla
real:

| Momento | Quién lo fija |
| --- | --- |
| Alta del reporte (`POST /api/v1/practicas/{id}/reportes/`) | `ReportePracticaView`, con `timezone.now()` dentro de la misma escritura atómica que crea la fila |
| Reenvío (`POST /api/v1/reportes/{id}/reenviar/`) | `reenviar_reporte`, con el reloj del servidor después de los chequeos de actor y estado, bajo el bloqueo de la fila, y se guarda junto con `estado` (`update_fields`) |

No entra ni sale en el contrato: el serializer no lo declara, así que enviarlo en el
cuerpo es un 400 en su clave y la respuesta de 201/200 no lo incluye; Swagger no lo
lista. `fecha_registro` no cambia (sigue siendo `auto_now_add`), la auditoría
(`Validacion`) no cambia y validar/devolver no lo tocan. Las filas creadas por otra
vía y las anteriores a la migración `0003_ingreso_revision_en` quedan en `NULL`: la
migración es un solo `AddField` nullable, sin valor por defecto ni backfill, porque
`fecha_registro` no distingue un alta inicial de un reenvío histórico.

## Reglas del POST (S5, S3)

Decide en este orden y no escribe hasta el final: sin actor guardado y activo, 401;
actor que no es estudiante, 403; la práctica se busca **dentro de `transaction.atomic()`
con `select_for_update`** y solo entre las del propio estudiante (inexistente y ajena
dan el mismo 404, sin fuga de existencia); solo una práctica `en_curso` acepta reportes
(409 `practica_no_en_curso`: asignada, suspendida, revisión final y finales se
rechazan); después valida el cuerpo (400) y la semana repetida (409 `semana_duplicada`).
Todos los errores llevan `errors.code` (envelope de #77).

| Caso | Resultado |
| --- | --- |
| Cuerpo que no es objeto (lista, texto, número) | 400 en `non_field_errors` |
| Campo fuera de `semana` y `horas_reportadas` (o uno que fija el servidor) | 400 en su clave |
| Más de 168 horas en la semana | 400 en `horas_reportadas` |
| Ayudantía (docencia o investigación) con más de 10 h | 400 con el mensaje del Art. 341 (RF-15) |
| Ayudantía con 10 h o menos | Aceptado, sin marca de revisión |
| Laboral o comunitaria con más de 40 h | **Aceptado** con `requiere_revision = true` (escenario S5) |
| Semana ya reportada en esa práctica | 409 `semana_duplicada`; la restricción de la base es la última red |

Solo el `IntegrityError` de la restricción `reportes_reporte_semana_unica` se traduce a
409; cualquier otro se relanza (500 genérico). `requiere_revision` es la marca que el
tutor verá al revisar; la cola de revisión del tutor llega con HU-03. Las horas tampoco
cuentan para el acumulado hasta que el tutor las valide: aquí solo nacen `en_revision`.
Las evidencias PDF (RNF-05) llegan por el alta multipart: ver «Evidencias PDF».

## Evidencias PDF (C-03, #157)

`EvidenciaReporte` guarda cada PDF privado de una entrega del reporte: `reporte` (FK
`PROTECT`, `reporte.evidencias`), `version`, `archivo` en
`reportes_evidencias/practica-<id>/<uuid>.pdf` (el nombre del cliente no llega al
disco), `nombre` original, `tamano_bytes` y `subida_en`. La API nunca actualiza ni
borra estas filas.

| Momento | Cuerpo | Efecto |
| --- | --- | --- |
| Alta JSON legada | `semana`, `horas_reportadas` | Igual que antes: mismos campos, errores y 201; sin evidencias |
| Alta multipart | `semana`, `horas_reportadas`, `actividades`, `evidencias` (uno o más) | Reporte con sus actividades y los PDFs como versión 1; 201 con el cuerpo legado |
| Reenvío legado | Sin cuerpo | Igual que antes: «devuelto» -> «en revisión», sin evidencias nuevas |
| Reenvío multipart | `evidencias` (uno o más) | Además guarda los PDFs como la versión siguiente (`version_actual + 1`); las anteriores y la `Validacion` de la devolución se conservan |

Cada archivo debe ser PDF (extensión `.pdf` y firma `%PDF-`) de hasta 5 MB
(`validar_archivo_informe`, ADR 0005): 5 MB exactos se aceptan y un byte más se
rechaza. Faltar `evidencias` responde 400 «Adjunte al menos un archivo PDF.» y
`actividades` ausente o en blanco 400 en su clave. Todos los PDF se validan antes de
escribir; si una escritura posterior falla, `evidencias_atomicas` borra los archivos
ya guardados y la transacción revierte las filas: un rechazo no deja filas ni
archivos.

La versión vigente de un reporte (`version_actual`) es la mayor de sus evidencias, o
1 si no tiene ninguna. El detalle y la lista publican `actividades`, `version`,
`evidencias` (`id`, `version`, `nombre`, `tamano_bytes`, `subida_en`, `descarga`) y
`devoluciones` (todas las devoluciones, de la más antigua a la última), además de
los campos legados. `descarga` es la ruta autenticada de la API; no hay `MEDIA_URL`
ni URL pública del archivo. La descarga busca la evidencia acotada a su reporte y al
alcance de filas: la de una práctica ajena, la de otro reporte y una inexistente
responden el mismo 404. El almacenamiento privado en Docker lo coordina Jaime (S5).

En OpenAPI el alta documenta `application/json` (legado) y `multipart/form-data` con
`evidencias` como lista de binarios, el reenvío documenta el multipart opcional y la
descarga responde `application/pdf` binario.

## Validación sobre reportes (S7)

`Validacion` gana `reporte_id` opcional junto a `plan_id` y la `CheckConstraint`
`actividades_validacion_plan_reporte_o_informe` impone «exactamente uno de los tres»
(plan, reporte o informe final del estudiante; ver el README de `apps.actividades`).
La aprobación de un plan (T024) no cambia: sigue escribiendo la validación con `plan`
y sin `reporte`.

## Límite

Las pruebas corren sobre SQLite en memoria; la unicidad y la restricción «exactamente uno»
se verifican en esa base. `select_for_update` no bloquea en SQLite: el bloqueo real solo
existe en PostgreSQL (la suite también corre contra `postgres:16`). Los servicios de T024 no eligen reportes
todavía: validar un reporte llega con HU-03. El plazo de revisión (T6/HU-06) todavía no
consume `ingreso_revision_en`: esta unidad solo lo registra, sin job, política ni zona
horaria propias.

## Checklist

- [ ] `apps.reportes` figura en `INSTALLED_APPS`.
- [ ] El reporte nace `en_revision`, con fecha automática y una sola fila por semana.
- [ ] El estudiante dueño registra su reporte; sin actor 401, otro rol 403 y práctica ajena o inexistente 404 idéntico.
- [ ] Solo una práctica `en_curso` acepta reportes (409 `practica_no_en_curso` en las demás).
- [ ] La ayudantía de 11 h se rechaza con el Art. 341 y la de 10 h se acepta; 169 h se rechazan.
- [ ] Más de 40 h se aceptan con `requiere_revision = true`.
- [ ] Un rechazo no cambia filas ni contadores.
- [ ] El endpoint aparece en Swagger con 201, 400, 401, 403, 404 y 409.
- [ ] `ingreso_revision_en` se fija en el alta y en el reenvío, es `NULL` en filas heredadas y ningún rechazo lo toca.
- [ ] `Validacion` acepta plan o reporte, nunca ambos ni ninguno.

## Validación del tutor académico (RF-03, #122/#124)

El ciclo de validación del estudiante (plan → reporte → validación → horas cuentan):

- `GET /api/v1/pendientes/` — la cola del tutor: reportes `en_revision` de sus prácticas asignadas (via `AsignacionTutor` con `hasta` nulo) que están `en_curso`; las suspendidas, canceladas o cerradas no aparecen (CU-01 2b). Desde RF-16 la cola suma los **informes finales del estudiante** en revisión: las tarjetas de reporte conservan sus cinco campos (`id`, `practica_id`, `semana`, `horas_reportadas`, `estado`) y cada informe llega con su clave `informe-<id>` y los campos `id`, `practica_id`, `version`, `estado` (ver el README de `apps.actividades`).
- `GET /api/v1/reportes/{id}/` — lectura del reporte individual con la **observación de su última devolución** (`S6`): cierra el bucle de corrección de HU-03.
- `POST /api/v1/reportes/{id}/validar/` — marca `validado` y registra la `Validacion(decision=aprobado)`; las horas del reporte ya cuentan para el acumulado.
- `POST /api/v1/reportes/{id}/devolver/` — marca `devuelto` con `observacion` obligatoria y registra la `Validacion(decision=devuelto)`; el estudiante corrige y reenvía.
- Reenvío del estudiante: `reenviar_reporte` cambia el estado de la fila existente de `devuelto` a `en_revision` (state-only, sin campo version — el data-model no lo define para reportes): con la práctica fuera de `en_curso` responde 409 `practica_no_en_curso` y con el reporte fuera de `devuelto`, 409 `reporte_no_devuelto`. Vuelve a fijar `ingreso_revision_en` con el reloj del servidor (ver «Ingreso a revisión»); `fecha_registro` no se renueva.

Fail-closed: solo el tutor académico activo de la práctica (otros roles 403); la práctica ajena y la inexistente dan el mismo 404 (sin oracle); práctica que no está `en_curso` 409 (`practica_no_en_curso`, CU-01 2b `spec.md:497`: con la práctica suspendida, cancelada o cerrada no se valida, no se devuelve ni se reenvía), comprobado después del permiso y antes del estado del reporte; reporte fuera de `en_revision` 409 (`reporte_no_en_revision`); devolución sin observación o con un cuerpo que no es objeto JSON 400. Un rechazo no escribe nada. Los servicios reutilizan el patrón de `_registrar_validacion`/`_exigir_tutor` de actividades con `reporte=` en el constructor.

## Reporte devuelto: la lectura que cierra la corrección (RF-03, S6)

`GET /api/v1/reportes/{id}/` es la lectura multirrol que faltaba: el estudiante dueño
recupera la observación con la que el tutor devolvió su reporte, y el tutor, los roles
con carrera y el alcance de filas de T019 leen el mismo reporte.

| Campo | Cuándo sale |
| --- | --- |
| `id`, `semana`, `horas_reportadas`, `estado`, `fecha_registro` | Siempre |
| `devolucion` (`observacion`, `autor_id`, `fecha`) | Solo con `estado = devuelto`: la última `Validacion` de devolución, por `fecha` y, en empate, por `pk` |
| `devolucion = null` | En `en_revision` y en `validado`, y también después de un reenvío (la observación anterior ya no describe el estado) |

La consulta se acota al `pk` pedido **y** a `practicas_visibles_para`, así que un
reporte de una práctica ajena responde el mismo 404 que uno inexistente. La vista no
escribe nada y sin token responde 401 con el envelope universal. Las pruebas están en
`backend/tests/integration/test_reporte_detalle.py`.

## Horas acumuladas (RF-20, #126)
## Horas acumuladas (RF-05, HU-04, #126)

`GET /api/v1/practicas/{id}/horas/` proyecta lo ya guardado en los reportes de la
práctica, sin escribir ni acumular contadores aparte:

| Campo | Cálculo |
| --- | --- |
| `horas_validadas` | `Sum(horas_reportadas)` de los reportes en `validado` |
| `horas_en_revision` | `Sum(horas_reportadas)` de los reportes en `en_revision` |
| `horas_requeridas` | `Practica.horas_requeridas` (el valor copiado al asignar, T018) |
| `horas_faltantes` | `max(0, horas_requeridas - horas_validadas)` |
| `semana_en_revision` | `True` si algún reporte **no devuelto** supera `UMBRAL_REVISION_HORAS` (40); 40 exactas no lo encienden |

Un reporte `devuelto` no suma en `horas_validadas` ni en `horas_en_revision`, y
sus horas tampoco dejan la señal de revisión. La señal se calcula con
`horas_reportadas`, no con la columna `requiere_revision`, para que la lectura no
dependa de que esa marca esté sincronizada.

Es una lectura multirrol: no exige un rol concreto, sino que la práctica esté en
`practicas_visibles_para` (T019). El estudiante solo alcanza la suya, el tutor
académico las asignadas con `hasta` nulo, el tutor de entidad las laborales con su
FK y coordinador/director/secretaría las de su carrera. Una práctica ajena responde
el mismo 404 que una inexistente, sin oráculo de existencia, y el envelope es el de
#77. Las pruebas están en `backend/tests/integration/test_horas_acumuladas.py`.
