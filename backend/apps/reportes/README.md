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
5. Migraciones: `backend/apps/reportes/migrations/0001_reportesemanal.py` y
   `backend/apps/actividades/migrations/0003_validacion_reporte.py`.
6. Pruebas: `backend/tests/unit/test_reportes.py` (modelo y migración) y
   `backend/tests/integration/test_reportes_flujo.py` (flujo completo con `APIClient`).

Fuente: `specs/001-seguimiento-practicas/data-model.md` (`ReporteSemanal`,
`Validacion`), RF-02/RF-15 y T026-T027 en `specs/001-seguimiento-practicas/tasks.md`.

## Campos y reglas

| Campo | Tipo | Regla |
| --- | --- | --- |
| `practica` | FK a `practicas.Practica` | Obligatorio; `PROTECT`; `practica.reportes` |
| `semana` | entero positivo | Desde 1; una sola versión activa por semana |
| `horas_reportadas` | entero positivo | Desde 1; `PositiveIntegerField` admite 0, el validador no |
| `fecha_registro` | fecha y hora | Automática al insertar (`auto_now_add`) |
| `estado` | `en_revision`, `validado` o `devuelto` | Inicia `en_revision` |

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
| `POST /api/v1/practicas/{id}/reportes/` | Solo el estudiante dueño | 201 con el reporte, 400, 404 |

La tarjeta (`PracticaCardSerializer`) expone `id`, `estudiante_id`, `tipo`, `subtipo`,
`estado` y `horas_requeridas`: lo mínimo para listar sin filtrar motivos ni proyecto.
El envelope (`success`, `message`, `data`, `errors`, `meta`) es el de #77 y no se
reimplementa aquí. El cuerpo del POST es exactamente `semana` y `horas_reportadas`;
cualquier otro campo —`contenido` incluido— se rechaza con 400 en su clave.

## Reglas del POST (S5, S3)

Decide en este orden y no escribe hasta el final: la práctica debe existir (404); el
actor debe ser el estudiante **guardado** y activo de la propia práctica (400 en
`actor`; un tutor valida en otra unidad, no registra aquí); la práctica no puede estar
`cerrada` ni `cancelada` (400 con el mensaje de T017); después valida el serializer.

| Caso | Resultado |
| --- | --- |
| Ayudantía (docencia o investigación) con más de 10 h | Rechazo con el mensaje del Art. 341 (RF-15) |
| Ayudantía con 10 h o menos | Aceptado |
| Laboral o comunitaria con más de 40 h | **Aceptado**: el data-model dice «se identifica para revisión del tutor» |
| Semana ya reportada en esa práctica | 400 en `semana`; la restricción de la base es la última red |

El señalamiento de las horas altas y la marca de revisión **no** se construyen en esta
unidad: no hay campo, alerta ni cola que los represente (mecanismo pendiente). Las horas
del reporte tampoco cuentan para el acumulado hasta que el tutor las valide: aquí solo
nacen `en_revision`.

## Validación sobre reportes (S7)

`Validacion` gana `reporte_id` opcional junto a `plan_id` y la `CheckConstraint`
`actividades_validacion_plan_o_reporte` impone «exactamente uno de los dos»; `full_clean()`
repite la regla en `reporte`. La aprobación de un plan (T024) no cambia: sigue escribiendo
la validación con `plan` y sin `reporte`.

## Límite

Las pruebas corren sobre SQLite en memoria; la unicidad y la restricción «exactamente uno»
se verifican en esa base, no en PostgreSQL. Los servicios de T024 no eligen reportes
todavía: validar un reporte llega con HU-03.

## Checklist

- [ ] `apps.reportes` figura en `INSTALLED_APPS`.
- [ ] El reporte nace `en_revision`, con fecha automática y una sola fila por semana.
- [ ] El estudiante dueño registra su reporte; cualquier otro actor recibe 400 en `actor`.
- [ ] Una práctica `cerrada` o `cancelada` no acepta reportes.
- [ ] La ayudantía de 11 h se rechaza con el Art. 341 y la de 10 h se acepta.
- [ ] Un rechazo no cambia filas ni contadores.
- [ ] El endpoint aparece en Swagger con 201, 400 y 404.
- [ ] `Validacion` acepta plan o reporte, nunca ambos ni ninguno.
