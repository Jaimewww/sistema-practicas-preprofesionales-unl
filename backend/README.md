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
python -m pytest                                    # suite completa (tests/ + apps/ + config/)
python -m pytest -m unit                            # solo unitarias
python -m pytest -m integration                     # solo integración
python -m pytest -m security                        # autenticación/autorización y secretos
python -m pytest -m api                             # superficie HTTP de la API v1
python -m pytest tests/unit/test_practica.py   # 11 tests de la unidad   # archivo o caso puntual
python -m pytest --cov=apps                              # suite + reporte de cobertura
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
- **Cobertura:** `--cov` usa `source = apps` y muestra las líneas faltantes
  (`show_missing`). No hay umbral: el gate lo define CI (#82).

### Clave secreta y base de datos

- `DJANGO_SECRET_KEY` **no hace falta exportarla** para correr pytest: si falta,
  `backend/conftest.py` genera una clave efímera de proceso con
  `get_random_secret_key()` (contrato S4, la misma filosofía dev-only de
  `DEBUG=True`) y nunca la imprime ni la escribe. Si CI o el compose de #81 la
  exportan, se respeta ese valor.
- Sin `POSTGRES_*` el motor es el SQLite de `config/settings.py`, pero
  pytest-django crea una base de test **en memoria**: nunca toca el
  `backend/db.sqlite3` del desarrollador.
- **PostgreSQL real:** exportá `POSTGRES_HOST`/`POSTGRES_DB`/`POSTGRES_USER`/
  `POSTGRES_PASSWORD` (el compose de #81) y pytest-django crea una base de test
  aparte. La corrida real contra PostgreSQL no se hace en local en esta unidad:
  la sostienen el compose (#81) y CI (#82).
- El test que necesita PostgreSQL de verdad (`has_select_for_update`) se sigue
  omitiendo con el mismo `skipUnlessDBFeature` del runner retenido: bajo SQLite
  aparece como `1 skipped`, no como fallo.

### Comando para CI (#82)

```bash
cd backend && python -m pytest              # suite
cd backend && python -m pytest --cov=apps        # suite + cobertura
```

### El runner retenido

`python manage.py test` (o `make test` desde la raíz) sigue funcionando y
descubre la misma suite; sirve para contrastar que pytest y Django describen lo
mismo. Ojo: `make test` corre con `DEBUG` apagado y sin clave efímera, así que
necesita `DJANGO_SECRET_KEY` exportada (pytest no, porque el conftest la genera).
