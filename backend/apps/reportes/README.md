# Reportes: registro del reporte semanal y las dos lecturas de prácticas (#78)

`ReporteSemanal` (HU-02/RF-02) y el endpoint que lo registra, más las dos rutas de
lectura de prácticas que lo acompañan en el contrato de #78. No incluye evidencias
(RNF-05), la validación del tutor (HU-03), rezago, alertas, confirmación de entidad
ni informe final.

## Ruta rápida

1. Modelo: `backend/apps/reportes/models.py` (`ReporteSemanal`, `MENSAJE_AYUDANTIA`).
2. Serializer y endpoint: `backend/apps/reportes/serializers.py` (`ReporteSemanalSerializer`)
   y `backend/apps/reportes/api.py` (`ReportePracticaView`).
3. Lecturas de prácticas: `backend/apps/practicas/api.py` (`PracticaCardSerializer`,
   `PracticasListaView`, `PracticaDetalleView`).
4. Rutas: `backend/config/urls.py` (las tres van **antes** del demo del prototipo).
5. Migraciones: `backend/apps/reportes/migrations/0001_reportesemanal.py`,
   `0002_requiere_revision_y_tope_semanal.py` y
   `backend/apps/actividades/migrations/0003_validacion_reporte.py` (más la fusión
   `0004_merge_...` con la 0003 de #98).
6. Pruebas: `backend/tests/unit/test_reportes.py` (modelo y migración) y
   `backend/tests/integration/test_reportes_flujo.py` (flujo completo con `APIClient`).

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

No hay `contenido` ni `version`: el data-model no los define para un reporte y esta
unidad no los inventa. La devolución con versión nueva es de la validación del tutor.
`UniqueConstraint` sobre `(practica, semana)` impone «una sola versión activa por semana»
también en la base, así que `objects.create()` duplicado falla con `IntegrityError`.
La semana es un entero libre: el calendario del período no se recalcula aquí (el
prototipo muestra `Semana n (dd/mm - dd/mm)`; esa derivación queda fuera de la unidad).

## Endpoints

| Método y ruta | Alcance | Respuesta |
| --- | --- | --- |
| `GET /api/v1/practicas/` | `practicas_visibles_para` (T019) del actor | 200 con la lista de tarjetas |
| `GET /api/v1/practicas/{id}/` | La misma consulta acotada | 200 con la tarjeta, 404 fuera de alcance |
| `POST /api/v1/practicas/{id}/reportes/` | Solo el estudiante dueño, práctica «en curso» | 201 con el reporte; 400, 401, 403, 404, 409 |

La tarjeta (`PracticaCardSerializer`) expone `id`, `estudiante_id`, `tipo`, `subtipo`,
`estado` y `horas_requeridas`: lo mínimo para listar sin filtrar motivos ni proyecto.
El envelope (`success`, `message`, `data`, `errors`, `meta`) es el de #77 y no se
reimplementa aquí. El cuerpo del POST es exactamente `semana` y `horas_reportadas`;
cualquier otro campo —`contenido` incluido— se rechaza con 400 en su clave.

Desde #79 las tres rutas exigen JWT (`Authorization: Bearer`): sin credenciales
responden 401, el rol sin permiso recibe 403 y el POST del reporte solo admite al
estudiante dueño —ver `backend/apps/seguridad/README.md`—; los 400/404 de abajo siguen
siendo la validación de negocio ya autenticada.

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
**Pendiente (RNF-05)**: la subida de evidencias PDF (≤ 5 MB) no existe todavía.

## Validación sobre reportes (S7)

`Validacion` gana `reporte_id` opcional junto a `plan_id` y la `CheckConstraint`
`actividades_validacion_plan_o_reporte` impone «exactamente uno de los dos»; `full_clean()`
repite la regla en `reporte`. La aprobación de un plan (T024) no cambia: sigue escribiendo
la validación con `plan` y sin `reporte`.

## Límite

Las pruebas corren sobre SQLite en memoria; la unicidad y la restricción «exactamente uno»
se verifican en esa base. `select_for_update` no bloquea en SQLite: el bloqueo real solo
existe en PostgreSQL (la suite también corre contra `postgres:16`). Los servicios de T024 no eligen reportes
todavía: validar un reporte llega con HU-03.

## Checklist

- [ ] `apps.reportes` figura en `INSTALLED_APPS`.
- [ ] El reporte nace `en_revision`, con fecha automática y una sola fila por semana.
- [ ] El estudiante dueño registra su reporte; sin actor 401, otro rol 403 y práctica ajena o inexistente 404 idéntico.
- [ ] Solo una práctica `en_curso` acepta reportes (409 `practica_no_en_curso` en las demás).
- [ ] La ayudantía de 11 h se rechaza con el Art. 341 y la de 10 h se acepta; 169 h se rechazan.
- [ ] Más de 40 h se aceptan con `requiere_revision = true`.
- [ ] Un rechazo no cambia filas ni contadores.
- [ ] El endpoint aparece en Swagger con 201, 400, 401, 403, 404 y 409.
- [ ] `Validacion` acepta plan o reporte, nunca ambos ni ninguno.
