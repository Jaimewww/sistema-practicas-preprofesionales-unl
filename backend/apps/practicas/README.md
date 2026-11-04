# Prácticas: catálogos y práctica asignada

Dos catálogos y la práctica asignada del modelo de datos: entidades receptoras,
períodos académicos y `Practica` (RF-14). Solo modelos y migraciones; no incluye
endpoints, API, autenticación ni datos de ejemplo.

## Ruta rápida

1. Modelos: `backend/apps/entidades/models.py` (`EntidadReceptora`) y `backend/apps/practicas/models.py` (`Periodo`).
2. Migraciones: `backend/apps/entidades/migrations/0001_initial.py`, `backend/apps/practicas/migrations/0001_initial.py` (períodos) y `0002_practica.py`.
3. Pruebas: `backend/tests/unit/test_entidad_receptora.py`, `test_periodo.py` y `test_practica.py`.

Fuente: `specs/001-seguimiento-practicas/data-model.md` (apartados `Periodo`,
`EntidadReceptora` y `Practica`) y T014/T015 en `specs/001-seguimiento-practicas/tasks.md`.

## Campos y reglas

| Modelo | Campos obligatorios | Regla |
| --- | --- | --- |
| `EntidadReceptora` | `nombre` | Sin convenio, contacto ni vigencia; el nombre no es único |
| `Periodo` | `nombre`, `fecha_inicio`, `fecha_fin` | `fecha_fin` estrictamente posterior a `fecha_inicio` |
| `Periodo.dias_totales` | — | Propiedad derivada de solo lectura: `(fecha_fin - fecha_inicio).days + 1` |
| `Practica` | `estudiante`, `carrera`, `periodo`, `tipo`, `horas_requeridas` | Reglas condicionales por tipo; ver la sección siguiente |

## Practica asignada

`entidad` es opcional salvo en laboral; `subtipo` es obligatorio en laboral y debe
quedar vacío en comunitaria; `proyecto_vinculacion` (texto de 200) es obligatorio
en comunitaria. Las cuatro claves foráneas usan `PROTECT`.

| Campo | Valores |
| --- | --- |
| `tipo` | `laboral`, `comunitaria` |
| `subtipo` | `practica`, `pasantia`, `ayudantia_docencia`, `ayudantia_investigacion` |
| `estado` | `asignada` (inicial), `en_curso`, `en_revision_final`, `cerrada`, `suspendida`, `cancelada` |
| `motivo_suspension`, `motivo_cancelacion` | Texto opcional, vacío por defecto |

`full_clean()` aplica las reglas condicionales y reporta: «La entidad receptora es
obligatoria para las prácticas laborales.», «El subtipo es obligatorio para las
prácticas laborales.», «El subtipo solo aplica a las prácticas laborales.» y «El
proyecto de vinculación es obligatorio para las prácticas comunitarias.».

`horas_requeridas` no tiene valor por defecto ni FK a la configuración: quien asigna
aporta el valor (p. ej. 240) y queda guardado. Cambiar la configuración después no
modifica la práctica; la copia automática es T018 y no está implementada. Las
transiciones y los motivos obligatorios son T017.

## Conteo inclusivo de días

Del 1 al 7 de enero son 7 días, no 6:

```python
>>> from datetime import date
>>> from apps.practicas.models import Periodo
>>> periodo = Periodo(
...     nombre="2026-1", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 1, 7)
... )
>>> periodo.dias_totales
7
```

Dos fechas adyacentes (1 y 2 de marzo) dan 2 días. Un período de un solo día o
con las fechas invertidas es inválido.

## Límite de validación

Estos modelos se validan con `full_clean()`: `save()` y `objects.create()` no la
ejecutan, como en cualquier modelo de Django. Por eso los tests llaman a
`full_clean()` antes de guardar y una fila creada sin validar queda tal cual en
la base. El error de fechas se reporta en el campo `fecha_fin` con el mensaje
«La fecha de fin debe ser posterior a la fecha de inicio.».

`dias_totales` no se almacena: se calcula desde las fechas y no devuelve 0 días
cuando las fechas están incompletas o son inválidas.

## Checklist

- [ ] `apps.entidades` y `apps.practicas` figuran en `INSTALLED_APPS`.
- [ ] `full_clean()` rechaza un nombre vacío y fechas no posteriores al inicio.
- [ ] `full_clean()` rechaza una laboral sin entidad o sin subtipo y una comunitaria sin proyecto.
- [ ] Las horas guardadas no cambian al actualizar la configuración de la carrera.

## Siguiente paso

`AsignacionTutor` (resto de T015), las transiciones de T017, la copia automática de
T018 y el admin de T020 quedan fuera de esta unidad.
