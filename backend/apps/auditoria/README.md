# Auditoría: historial de estados de la práctica

`HistorialEstado` guarda cada cambio de estado de una `Practica` (RF-10, HU-09) con
estado anterior, nuevo, autor, fecha automática y motivo. Es **de solo inserción** en
el borde del ORM de la aplicación. Es T016: **no** cierra T017 (servicio de
transiciones) ni la integración de `django-simple-history` ya elegida (T002 pendiente).

Modelo `backend/apps/auditoria/models.py`, migración `0001_initial.py` y pruebas
`backend/tests/unit/test_historial_estado.py` (T009).

## Reglas

`estado_anterior` es nulo solo en el registro inicial y `motivo` es obligatorio al
suspender y cancelar (RF-13); reanudar (`suspendida` → `en_curso`) no lo exige y,
si se da, se conserva. Ambos los aplica
`full_clean()` de este modelo; `save()` y `objects.create()` no lo llaman, así que una
fila creada sin validar queda tal cual, y un estado con tipo inválido (lista, dict)
produce `ValidationError`, no `TypeError`.

## Frontera de inserción

Se admite el alta fila a fila con `full_clean()` + `save()`. Se rechazan con
`ValidationError`: `save()` de una fila existente (con o sin `update_fields` /
`force_update`), `save()` con `pk` ya usado, `Model.delete()`, `QuerySet.update()`,
`QuerySet.delete()`, el gestor inverso (`practica.historial_estados.add/set/delete`),
`bulk_update()`, `bulk_create()` y su modo `update_conflicts`. `update_or_create()` se
rechaza solo cuando actualizaría una fila existente; con un `pk` nuevo inserta. Tras
un rechazo no cambian filas, conteo, autor, fecha ni estado.

## Límites

`objects` es también el gestor base (`base_manager_name`) porque el gestor inverso
reasigna con el gestor base. La protección es del ORM de la aplicación: SQL en crudo,
migraciones de datos, cliente de base, DBA, `QuerySet._raw_delete()` y las cascadas del
colector de Django **no** están bloqueados; no hay triggers ni permisos de base. El
`SELECT` extra que descarta un `pk` ya usado ocurre solo si la instancia trae `pk`
explícito, no en un alta normal. Probado en SQLite en memoria: la concurrencia es de
T017 y PostgreSQL no se ejecutó.
