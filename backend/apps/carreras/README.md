# Carreras: configuración por modalidad y su escritura (RF-12, C-17)

Dos piezas de RF-12 sobre el modelo de `apps/carreras`: el modelo de
`ConfiguracionCarrera` con sus dos `CheckConstraint` —horas requeridas > 0 y
umbral ≤ 100— y el endpoint que la escribe,
`PUT /api/v1/carreras/{codigo}/configuracion/`. La lectura de la configuración
vigente **no** vive aquí: la hacen `_configuracion_vigente` de
`apps/practicas/services.py` (asignar la práctica) y los servicios de alertas de
RF-07 con el mismo lookup `-vigente_desde, -pk`.

## Contrato

`PUT /api/v1/carreras/{codigo}/configuracion/` — una **sola** modalidad por
llamada (D1). El cuerpo es estricto: no es objeto, o trae una clave que no está
abajo, es un 400 en esa clave.

| Campo | Tipo | Regla |
| --- | --- | --- |
| `modalidad` | `laboral` \| `comunitaria` | Obligatorio |
| `horas_requeridas` | entero | Obligatorio y mayor que cero |
| `plazo_reporte_dias` | entero | Por defecto 3; no negativo |
| `plazo_revision_dias` | entero | Por defecto 5; no negativo |
| `umbral_rezago` | entero | Por defecto 80 %; entre 0 y 100 |
| `vigente_desde` | fecha `AAAA-MM-DD` | Obligatorio |

Respuesta 200: la fila guardada con `id`, `carrera` (el código), `modalidad`, los
cuatro números y `vigente_desde`.

Rechazos: `400` por campo (valores fuera de rango, claves ajenas, campos
ausentes), `401` sin cuenta vigente —el envelope de `apps.contrato`—, `403` para
un rol ajeno o para el coordinador de **otra** carrera, y `404` para un código de
carrera inexistente. El rol se comprueba antes de la carrera y del cuerpo.

## Decisiones

- **D1 — PUT por modalidad.** El modelo guarda una fila por
  `(carrera, modalidad, vigente_desde)`; los plazos y el umbral viven en esa fila.
- **D2 — Historial, no sobrescritura.** Editar con otra `vigente_desde` crea una
  fila nueva; la anterior no se borra ni se reescribe y el lector de la
  configuración vigente sigue mandando.
- **D3 — Idempotencia en el servicio.** Repetir el `PUT` con la misma
  `(carrera, modalidad, vigente_desde)` **actualiza** esa fila (buscar-y-actualizar
  bajo `select_for_update()`), sin duplicarla. El modelo **no** lleva
  `UniqueConstraint`: la spec (C-17, data-model) no la pide, el desempate
  `-vigente_desde, -pk` ya fijado por las pruebas de asignación y de alertas sigue
  teniendo sentido para filas heredadas, y una base de desarrollo con duplicados
  no bloquearía la migración. Coste asumido: dos `PUT` simultáneos podrían crear
  dos filas del mismo día, la misma tolerancia que ya existía.
- **D4 — Horas copiadas intocables.** El endpoint nunca toca
  `Practica.horas_requeridas`: las prácticas existentes conservan lo copiado al
  asignarse y solo las asignaciones nuevas leen la configuración nueva
  (data-model.md:51 y :216). Los plazos y el umbral **no** se copian: las alertas
  los leen de la fila vigente.
- **D5 — Alcance.** Solo el coordinador activo **de esa carrera**, decidido
  contra la fila guardada del actor (no contra el token ni el objeto del
  llamador). Cualquier otro actor recibe 403 sin escrituras.

## Piezas

- `models.py` — `ConfiguracionCarrera`, con las dos `CheckConstraint` (horas > 0,
  umbral ≤ 100). Sin restricción de unicidad por día (D3).
- `serializers.py` — `ConfiguracionCarreraEntradaSerializer` (estricto) y
  `ConfiguracionCarreraSerializer` (salida).
- `services.py` — `guardar_configuracion`, el upsert transaccional con el permiso
  por carrera; ahí vive la idempotencia del mismo día (D3).
- `api.py` — `ConfiguracionCarreraView`, adaptador fino: rol en `initial()`,
  carrera por `codigo` y traducción del `ValidationError` del dominio por claves.

## Alcance

Sin `GET` ni `DELETE`: C-17 solo escribe y la lectura la hacen RF-07 y la
asignación. Sin UI (el formulario actual del prototipo es el demo en cookie,
`apps/prototipo/views_coordinador.py:133`, y no usa esta ruta).
