# Catálogos base de prácticas

Dos catálogos del modelo de datos: entidades receptoras y períodos académicos.
Esta unidad solo agrega modelos y migraciones iniciales; no incluye endpoints,
API, autenticación ni datos de ejemplo.

## Ruta rápida

1. Modelos: `backend/apps/entidades/models.py` (`EntidadReceptora`) y `backend/apps/practicas/models.py` (`Periodo`).
2. Migraciones iniciales: `backend/apps/entidades/migrations/0001_initial.py` y `backend/apps/practicas/migrations/0001_initial.py`.
3. Pruebas: `backend/tests/unit/test_entidad_receptora.py` y `backend/tests/unit/test_periodo.py`.

Fuente: `specs/001-seguimiento-practicas/data-model.md` (apartados `Periodo` y
`EntidadReceptora`) y T014/T015 en `specs/001-seguimiento-practicas/tasks.md`.

## Campos y reglas

| Modelo | Campos obligatorios | Regla |
| --- | --- | --- |
| `EntidadReceptora` | `nombre` | Sin convenio, contacto ni vigencia; el nombre no es único |
| `Periodo` | `nombre`, `fecha_inicio`, `fecha_fin` | `fecha_fin` estrictamente posterior a `fecha_inicio` |
| `Periodo.dias_totales` | — | Propiedad derivada de solo lectura: `(fecha_fin - fecha_inicio).days + 1` |

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
- [ ] El conteo inclusivo del 1 al 7 de enero da 7 días.

## Siguiente paso

`Practica` y `AsignacionTutor` (resto de T015) y el registro en el admin (T020)
quedan fuera de esta unidad.
