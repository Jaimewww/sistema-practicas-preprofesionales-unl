# Alertas: política de rezago por horas (HU-06, CU-03, T040)

Solo la regla matemática de RF-07: a una fecha dada, cuántas horas se esperan de
una práctica y si las horas acumuladas quedan por debajo del umbral de rezago.
No hay modelo, persistencia, ejecución programada, consulta ni notificación en
esta unidad. Ver «Alcance» al final.

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

## Alcance

`backend/apps/alertas/` es un paquete **sin registrar** en `INSTALLED_APPS`: esta
unidad no define modelos ni migraciones, así que no necesita registrarse.
Tampoco crea alertas ni notifica a nadie, no se llama desde ningún endpoint ni
comando y no modifica código existente.

No entregado aquí, y que las tareas siguientes (T042-T045) deben resolver:

- modelo `Alerta`, persistencia idempotente y deduplicación por causa activa;
- destinatarios (estudiante, tutor académico y coordinador);
- ejecución diaria y comando con fecha de prueba;
- vista/consulta de alertas y su estado general;
- alertas por plazos: reporte no enviado dentro del plazo de reporte y reporte
  sin revisar más allá del plazo de revisión (incluye días hábiles);
- calendario de semanas y anclaje semana/fecha, y la noción de «antes de la
  fecha de fin del período» como disparo.

## Pruebas

`backend/tests/unit/test_regla_rezago.py` (`SimpleTestCase`, sin base de datos):
ejemplo canónico con 95/96 h y ambos saldos, umbral configurado distinto de 80,
acotado en el inicio y en el fin, primer día inclusivo, límite con horas mínimas
fraccionarias (sin redondeo) y período inválido.

Fuente: `specs/001-seguimiento-practicas/spec.md:146` (HU-06 #3), CU-03 y
T040 en `specs/001-seguimiento-practicas/tasks.md`.
