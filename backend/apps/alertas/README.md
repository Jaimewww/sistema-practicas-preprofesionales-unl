# Alertas: política de rezago y modelo (HU-06, CU-03, T040–T042)

Dos piezas de RF-07: la regla matemática que decide si una práctica está
rezagada a una fecha (T040) y el modelo `Alerta` que persiste el aviso con su
causa activa única (T042). No hay generación, ejecución programada, consulta,
notificación ni autorización en esta unidad. Ver «Alcance» al final.

## Fórmula

```text
días transcurridos = acotar((fecha - fecha_inicio).días + 1, 0, días del período)
horas esperadas    = horas requeridas × (días transcurridos ÷ días del período)
horas mínimas      = horas esperadas × (umbral de rezago ÷ 100)
hay rezago         = horas validadas + horas en revisión < horas mínimas
```

- **Días inclusivos**, la misma convención que `Periodo.dias_totales`: el inicio
  y el fin cuentan, así que el día 56 del período son 56 días transcurridos.
- **Acotado al período**: antes del inicio son 0 días (0 h esperadas) y después
  del fin son todos los días (horas requeridas como esperadas).
- **Comparación estricta y exacta**: se usan `Fraction`, sin redondeo, y el
  rezago exige quedar *por debajo*. Con 96 h mínimas, 95 h es rezago y 96 h no.
- **Ambos saldos suman**: horas validadas + horas en revisión (`CU-03`); un
  reporte devuelto no entra en ninguno de los dos.

## Ejemplo concreto

240 h requeridas en un período de 16 semanas (112 días inclusivos), al cerrar la
semana 8 (día 56):

```text
horas esperadas = 240 × (56 ÷ 112) = 120
horas mínimas   = 120 × 80 %       = 96
```

Con 95 h entre validadas y en revisión hay rezago; con 96 h o más no lo hay.

## Entradas y salida

`apps.alertas.services.evaluar_rezago` es una función pura, todo por palabra
clave:

| Entrada | Significado |
| --- | --- |
| `horas_requeridas` | Horas de la práctica (las que copió la asignación) |
| `horas_validadas` | Suma de reportes validados |
| `horas_en_revision` | Suma de reportes en revisión |
| `fecha_inicio`, `fecha_fin` | Fechas del período, inclusivas |
| `fecha` | Fecha de evaluación inyectada; la función no lee el reloj |
| `umbral_rezago` | Porcentaje configurado; el 80 por defecto vive en `ConfiguracionCarrera.umbral_rezago`, no aquí |

Devuelve `EvaluacionRezago` (`NamedTuple`):

| Campo | Tipo | Significado |
| --- | --- | --- |
| `horas_esperadas` | `Fraction` | Horas esperadas a la fecha |
| `horas_minimas` | `Fraction` | Umbral aplicado a las horas esperadas |
| `en_rezago` | `bool` | Comparación estricta ya resuelta |

Un período con `fecha_fin` no posterior a `fecha_inicio` es inválido y se
rechaza con `ValueError` («La fecha de fin debe ser posterior a la fecha de
inicio.»), la misma regla que impone `Periodo`. No se valida nada más: la
función no toca la base de datos, no la consulta, no escribe y no conoce
configuración, roles ni rutas.

## Modelo `Alerta` (T042)

`apps.alertas.models.Alerta` es la fila que representa un aviso. La migración
`0001_initial` es **aditiva**: crea solo la tabla nueva y no cambia ninguna
tabla existente; la app se registra en `INSTALLED_APPS` para que Django cargue
el modelo.

| Campo | Tipo | Regla |
| --- | --- | --- |
| `practica` | FK a `Practica` | Obligatorio; `on_delete=PROTECT`, como las demás referencias a una práctica en el sistema |
| `tipo` | `CharField(choices)` | Exactamente los tres tipos del data-model |
| `fecha` | `DateField(auto_now_add)` | Django la asigna al crear la fila; un valor manual se ignora |
| `atendida` | `BooleanField(default=False)` | Nace falsa; el flujo de resolución no está en esta unidad |

Tipos declarados: `reporte_no_enviado`, `revision_pendiente` y `rezago`.
RF-18 (incumplimiento reportado por el tutor de entidad) **no** es una causa de
alerta aquí, y el campo no admite otros valores en `full_clean()`.

### Causa activa única (CU-03, 4b)

La causa de una alerta es el par **práctica/tipo**. Una `UniqueConstraint`
condicional sobre `(practica, tipo)` con `atendida=False` impone en la base que
exista **a lo sumo una alerta activa por causa**. La regla vale también para
`objects.create()` y `save()`, que no ejecutan `full_clean()`: la inserción
falla con `IntegrityError` y la fila original queda intacta. El mensaje de esa
excepción lo da el motor. Si se usa `full_clean()`, la validación de la
restricción presenta «Ya existe una alerta activa de este tipo para la práctica;
no se genera otra hasta que la vigente se marque como atendida.»

Lo que la restricción **sí** permite:

- causas distintas (tipos distintos) activas a la vez en la misma práctica;
- la misma causa activa en prácticas distintas;
- filas atendidas de la misma causa, incluso varias, que quedan como historial;
- una alerta atendida seguida de una nueva activa de la misma causa: el
  historial no bloquea el aviso vigente.

Lo que **no** permite es una segunda fila no atendida del mismo par. Por eso la
detección (T043) no necesita comprobar «¿ya existe?» antes de insertar: intenta
la inserción y trata solo el conflicto de unicidad de la causa activa como un
duplicado; otros errores de integridad deben propagarse.

### Destinatarios derivados del tipo

Los destinatarios **no se persisten**: no hay tabla, columna ni identidades
concretas de destinatarios. `Alerta.destinatarios` devuelve los **roles** que
corresponden a su tipo, según HU-06:

| Tipo | Roles destinatarios |
| --- | --- |
| `reporte_no_enviado` | estudiante, tutor académico y coordinador (HU-06 #1) |
| `revision_pendiente` | solo el tutor académico (HU-06 #2, CU-03 1b) |
| `rezago` | estudiante, tutor académico y coordinador (HU-06 #3) |

Es un mapeo de rol, no una autorización: esta unidad no decide quién puede leer
ni resolver la alerta, ni notifica a nadie. El tutor académico concreto sale de
`AsignacionTutor` y el coordinador de la carrera de la práctica; resolverlos es
trabajo de la vista de T045.

### Deduplicación a nivel de reporte: cuándo haría falta

Hoy la unicidad es por práctica/tipo, así que **varias semanas sin reporte de la
misma práctica producen una sola alerta activa** de `reporte_no_enviado`, y
varios documentos pendientes del mismo tutor una sola de `revision_pendiente`.
Eso es lo que CU-03 4b pide: no duplicar la causa. Si el producto quiere una
alerta por **reporte concreto** (por ejemplo, para mostrar «semana 3 sin
reporte» y cerrarla cuando se envía) habrá que anclar la alerta al reporte y
mover la unicidad a `(practica, tipo, reporte)`/`(reporte, tipo)`; con la
restricción actual esas alertas por reporte chocarían entre sí. Esa decisión no
se toma en T042: el anclaje a reportes y la resolución quedan para las tareas
siguientes.

## Alcance

La app queda registrada en `INSTALLED_APPS` y su migración inicial es aditiva.
Esta unidad no genera alertas, no notifica, no consulta, no autoriza, no expone
endpoints ni comandos y no modifica código ni tablas existentes.

No entregado aquí, y que las tareas siguientes (T043-T045) deben resolver:

- generación por plazos y rezago, con fecha inyectada y sin reloj.
- ejecución diaria y comando con fecha de prueba;
- vista/consulta de alertas y su estado general;
- alertas por plazos: reporte no enviado dentro del plazo de reporte y reporte
  sin revisar más allá del plazo de revisión (incluye días hábiles);
- anclaje de alertas a reportes concretos, resolución/cierre y permisos de
  lectura por destinatario;
- calendario de semanas y anclaje semana/fecha, y la noción de «antes de la
  fecha de fin del período» como disparo.

## Pruebas

`backend/tests/unit/test_regla_rezago.py` (`SimpleTestCase`, sin base de datos):
ejemplo canónico con 95/96 h y ambos saldos, umbral configurado distinto de 80,
acotado en el inicio y en el fin, primer día inclusivo, límite con horas mínimas
fraccionarias (sin redondeo) y período inválido.

`backend/tests/unit/test_alerta_modelo.py` (`TestCase`, SQLite): tipos exactos,
campos obligatorios, fecha automática, `atendida` falsa, mapeo exacto de roles
por tipo, y la unicidad de la causa activa mediante inserciones reales
(duplicado rechazado sin perder el original, causas y prácticas distintas,
historial atendido que no bloquea la siguiente activa).

Fuente: `specs/001-seguimiento-practicas/spec.md:146` (HU-06 #3), CU-03,
T040 y T042 en `specs/001-seguimiento-practicas/tasks.md`.
