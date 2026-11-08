# 0013. Contenerización con Docker Compose

- **Estado**: Aceptada
- **Fecha**: 2026-11-03
- **Decisores**: equipo (issue #81)

## Contexto

La constitución (principio VI) exige un entorno reproducible desde el README, y la sumativa pide que `docker compose up` levante API y base y que `/health/` responda `200`. Hasta ahora el backend se ejecutaba con un entorno virtual local y `make run`, con SQLite. [0002](0002-postgresql-como-motor-de-base-de-datos.md) fija PostgreSQL como motor, que no existe en la máquina de cada integrante.

## Decisión

Empaquetar el backend en una imagen y orquestarlo con **Docker Compose** (`Dockerfile`, `docker-compose.yml`, `docker/entrypoint.sh`):

- Servicio `api`: imagen `python:3.13-slim`, usuario sin privilegios (`uid 1000`), healthcheck sobre `/health/` y entrypoint que espera a PostgreSQL, ejecuta `migrate` y carga el `seed` cuando exista (#76).
- Servicio `db`: `postgres:17-alpine` con volumen `pgdata` y `pg_isready` como healthcheck; `api` espera a que esté sano.
- **Sin secretos en el repositorio**: `DJANGO_SECRET_KEY` y `POSTGRES_PASSWORD` no tienen valor por defecto y compose falla si faltan; se pasan por entorno o por un `.env` ignorado por Git. Las variables siguen el contrato compartido (`DJANGO_*`, `POSTGRES_*`).
- Las pruebas se ejecutan dentro del contenedor con `docker compose run`.

## Alternativas consideradas

- **Entorno virtual local con `make run`** (estado previo): cero dependencias externas, pero no reproduce PostgreSQL y depende de la versión de Python de cada máquina.
- **Dev container o Vagrant**: atan el flujo a un editor o a una máquina virtual pesada.
- **Un solo contenedor con SQLite**: contradice [0002](0002-postgresql-como-motor-de-base-de-datos.md).

## Consecuencias

- **Positivas**: entorno idéntico para el equipo y CI; PostgreSQL disponible con un comando; `DEBUG` y secretos controlados por entorno.
- **Negativas o costos**: Docker pasa a ser requisito de desarrollo; el compose actual usa `runserver` y `DJANGO_DEBUG=True` por defecto, aptos para desarrollo y no para producción.
- **Pendiente**: servidor de aplicaciones de producción (por ejemplo gunicorn) y TLS fuera del alcance de este incremento; `settings.py` adopta `POSTGRES_*` en #76 (mientras tanto el contenedor usa SQLite). El README indica Python 3.12+, la imagen usa 3.13: alinear la versión mínima.

## Referencias

- Issue #81, `Dockerfile`, `docker-compose.yml`, `docker/entrypoint.sh`
- [seguridad.md](../seguridad.md)
