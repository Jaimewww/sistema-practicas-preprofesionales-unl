# Backend — notas propias

La guía general del proyecto está en el [README raíz](../README.md). Este
archivo cubre solo lo que se corre desde `backend/`.

## Cómo correr las pruebas

La suite corre con **pytest + pytest-django** desde `backend/`; la configuración
(`backend/pytest.ini`) se descubre sola porque el comando se ejecuta en ese
directorio. Las dependencias de desarrollo ya traen el runner:

```bash
make install-dev        # desde la raíz: runtime + stubs + pytest/pytest-django/pytest-cov
```

```bash
cd backend
export DJANGO_DEBUG=True                            # desarrollo local: habilita el SQLite de respaldo
python -m pytest                                    # suite completa (tests/ + apps/ + config/)
python -m pytest -m unit                            # solo unitarias
python -m pytest -m integration                     # solo integración
python -m pytest -m security                        # autenticación/autorización y secretos
python -m pytest -m api                             # superficie HTTP de la API v1
python -m pytest tests/unit/test_practica.py        # un archivo o un caso puntual
python -m pytest --cov                              # suite + cobertura de apps y config
```

- **Descubrimiento:** es el mismo del runner retenido (`manage.py test`):
  `test*.py` bajo `tests/`, `apps/` y `config/`. Correr pytest en otro
  directorio, o con rutas fuera de `backend/`, rompe el descubrimiento y la
  configuración: no lo hagas.
- **Marcadores** (`unit`, `integration`, `api`, `security`): los asigna
  `backend/conftest.py` por ruta/nombre de módulo, sin decoradores por prueba
  (el mapeo exacto está en el docstring del conftest). `pytest.ini` corre con
  `--strict-markers`: un marcador no registrado es error, nunca se ignora en
  silencio.
- **Cobertura:** la configuración vive en `backend/.coveragerc` (pytest-cov no
  lee las secciones `[coverage:*]` de `pytest.ini`): `source = apps, config`,
  sin migraciones ni archivos de test, y `show_missing`. `--cov` va **sin valor**:
  con `--cov=apps` se pisaría `source` y `config/` quedaría sin medir. No hay
  umbral: el gate lo define CI (#82).

### Clave secreta y base de datos

- `DJANGO_SECRET_KEY` **no hace falta exportarla** para correr pytest: si falta,
  `backend/conftest.py` genera una clave efímera de proceso con
  `get_random_secret_key()` (contrato S4, la misma filosofía dev-only de
  `DEBUG=True`) y nunca la imprime ni la escribe. Si CI o el compose de #81 la
  exportan, se respeta ese valor.
- Sin `POSTGRES_*` el motor es el SQLite de `config/settings.py`, y solo existe
  con `DJANGO_DEBUG=True`: con `DEBUG` apagado y sin `POSTGRES_*` los settings
  fallan cerrado (`ImproperlyConfigured`). pytest-django crea una base de test
  **en memoria**: nunca toca el `backend/db.sqlite3` del desarrollador.
- **PostgreSQL real:** exportá `POSTGRES_HOST`/`POSTGRES_DB`/`POSTGRES_USER`/
  `POSTGRES_PASSWORD` (el compose de #81) y pytest-django crea una base de test
  aparte. Verificado con `postgres:16` (ver `docs/revisiones/cadena-jaime.md`,
  sección de #103); CI levanta `postgres:17-alpine`.
- El test que necesita PostgreSQL de verdad (`has_select_for_update`) se sigue
  omitiendo con el mismo `skipUnlessDBFeature` del runner retenido: bajo SQLite
  aparece como `1 skipped`, no como fallo.

### Comando para CI (#82)

Con las variables de CI (`DJANGO_SECRET_KEY`, `POSTGRES_*`; `DJANGO_DEBUG=False`):

```bash
cd backend && python -m pytest --cov --cov-report=xml:coverage.xml --cov-report=term-missing
```

Escribe `backend/coverage.xml` (lo lee Sonar y lo sube el artefacto de CI) y
muestra las líneas faltantes de `apps/` y `config/`. Es el mismo comando que
corre `.github/workflows/ci.yml`. `coverage.xml` y `.coverage` son artefactos
de la corrida: están en `.gitignore` y no se commitean.

### El runner retenido

`python manage.py test` (o `make test` desde la raíz) sigue funcionando y
descubre la misma suite; sirve para contrastar que pytest y Django describen lo
mismo. `make test` lo corre con `DJANGO_DEBUG=True`; sin `DEBUG` hace falta
`DJANGO_SECRET_KEY` exportada (pytest no, porque el conftest la genera). Los
tests de `tests/unit/test_pytest_config.py` son `SimpleTestCase` y corren con
ambos runners.
