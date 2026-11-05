# Prototipo: la demo y la semilla de datos

`apps.prototipo` es la capa de demostración del proyecto: guarda los datos de
ejemplo (`sample_data.py`), las vistas del prototipo que los muestran y las
validaciones de la demo. No tiene modelos propios ni migraciones: todo lo que
muestra sale de diccionarios o de los modelos reales de las demás apps.

## Ruta rápida

1. Datos de ejemplo: `backend/apps/prototipo/sample_data.py`.
2. Vistas y adaptadores de la demo: `views*.py`, `api.py`, `facade.py`, `dto.py`.
3. Semilla: `backend/apps/prototipo/management/commands/seed.py`.
4. Pruebas de la semilla: `backend/tests/unit/test_seed_command.py`.

## Comando `seed`

Carga los datos de demostración en los modelos reales —carreras, períodos,
entidades, usuarios, prácticas, tutores, planes y validaciones— para tener una
base de trabajo sin escribir a mano. El requisito de #76 es que
`python manage.py seed` cargue los datos de demo; el guion `sample_data.py` se
queda como fuente, no como base de datos.

```sh
cd backend
DJANGO_SECRET_KEY=<clave> python manage.py seed
```

`DJANGO_SECRET_KEY` es obligatoria: `config/settings.py` no tiene valor por
defecto y falla cerrado sin ella (contrato de entorno de #76). La misma variable
hace falta en cualquier ejecución local o de pruebas.

Qué hace:

- Siembra la carrera del coordinador con sus dos configuraciones de horas
  (laboral y comunitaria), las dos carreras ajenas del catálogo, el período del
  demo, las entidades receptoras y una cuenta por persona del guion. Las cuentas
  no tienen contraseña usable: son actores de la demo, no usuarios de acceso.
- Reutiliza los servicios internos: `asignar_practica` crea la práctica con las
  horas de la configuración vigente y el historial inicial, y
  `cambiar_estado_practica` la lleva al estado del guion, así que el diario de
  estados queda coherente con la tabla de transiciones.
- Crea el plan de cada práctica y registra la validación del tutor donde el guion
  dice que el plan está aprobado.
- Es todo o nada: corre en una transacción y, si ya hay datos de demostración en
  la base, se rechaza con un error explícito en vez de duplicarlos. Para volver a
  sembrar, use una base vacía.
- Imprime un resumen con el conteo de lo cargado.

El mapeo fino (códigos de carrera, fechas del período, roles de cada persona,
qué datos del guion no tienen equivalente en el modelo) está documentado en el
docstring del comando, porque es donde vive la decisión.

## Nota sobre DRF

`djangorestframework` está en `backend/requirements.txt` como dependencia del
issue #77, que es donde también entra en `INSTALLED_APPS` y llega la API. Hasta
entonces no se importa desde el código: el entorno de desarrollo actual puede no
tenerlo instalado y las vistas del prototipo siguen respondiendo igual.
