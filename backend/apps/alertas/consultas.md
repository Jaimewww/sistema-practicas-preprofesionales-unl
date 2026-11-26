# Alertas: consulta de alertas activas por destinatario (T17, base de T045)

`backend/apps/alertas/consultas.py` expone una única función de **solo
lectura**, `alertas_visibles_para(usuario)`, que devuelve las alertas activas que
le corresponden a un usuario según dos reglas ya existentes: el alcance de filas
de prácticas (T019) y el mapeo de destinatarios por tipo de alerta (HU-06).

Este corte no agrega endpoint, vista, plantilla, comando, notificación ni cambio
al prototipo. Es la base de dominio que T045 podrá consumir después.

## Ruta rápida

1. Implementación: `backend/apps/alertas/consultas.py`.
2. Alcance de filas reutilizado: `apps.usuarios.permissions.practicas_visibles_para`.
3. Mapeo de destinatarios: `apps.alertas.models.DESTINATARIOS_POR_TIPO`.
4. Rol persistido: misma regla que `practicas_visibles_para` y
   `apps.seguridad.permissions.rol_guardado` (lectura por `pk` de la fila activa,
   sin depender de la capa HTTP).
5. Pruebas: `backend/tests/unit/test_consulta_alertas.py`.

## Contrato

```python
alertas_visibles_para(usuario) -> QuerySet[Alerta]
```

Devuelve un `QuerySet` de `Alerta` con:

- `atendida=False`;
- `tipo` entre los tipos cuyo `DESTINATARIOS_POR_TIPO` incluye el rol guardado
  del usuario;
- `practica` dentro de `practicas_visibles_para(usuario)`;
- orden `-fecha`, `-pk` (la más reciente primero; el `pk` desempata porque
  `fecha` es un `DateField`).

No escribe, no cambia `atendida`, no crea alertas, no resuelve el historial
atendido, no lee el reloj, no interpreta encabezados del prototipo y no depende
de la petición HTTP.

## Matriz de visibilidad

| Rol guardado | Prácticas en alcance | Tipos visibles |
| --- | --- | --- |
| `estudiante` | Las propias (`estudiante_id`) | `reporte_no_enviado`, `rezago` |
| `tutor_academico` | Solo la asignación **vigente** (`hasta` nulo) | Los tres |
| `coordinador` | Las de su carrera | `reporte_no_enviado`, `rezago` |
| `director`, `secretaria` | Las de su carrera (alcance de filas) | Ninguno |
| `tutor_entidad` | Laborales vinculadas (alcance de filas) | Ninguno |
| Rol desconocido, sin carrera cuando corresponde, inactivo, borrado o sin fila | Ninguna | Ninguno |

La asignación vigente es la única que da acceso al tutor académico: cerrar la
asignación (`hasta`) y abrir otra retira el acceso al tutor anterior aunque la
alerta siga activa. `director`, `secretaria` y `tutor_entidad` pueden tener
prácticas dentro de su alcance de filas, pero no son destinatarios de ningún tipo
de alerta, así que la consulta devuelve vacío.

## Cierre por defecto

El rol y el estado se releen de la fila guardada, nunca del objeto del llamador:

- anónimo, objeto no guardado, fila borrada o fila inactiva → vacío;
- rol cambiado en la base después de cargar el objeto → manda la fila guardada;
- rol fuera de `Usuario.Rol` o sin destinatario → vacío;
- `is_staff` e `is_superuser` no abren el alcance;
- una alerta `atendida=True` no aparece, aunque la fila se conserve como
  historial.

## Fuera de este corte

Resolver o cerrar alertas, listar el historial atendido, notificar, generar
alertas en lote, exponer una ruta HTTP, crear la vista y la plantilla de T045,
filtrar por encabezados del prototipo y cambiar los datos de ejemplo.
