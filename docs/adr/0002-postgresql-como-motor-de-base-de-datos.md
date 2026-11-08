# 0002. PostgreSQL como motor de base de datos

- **Estado**: Aceptada
- **Fecha**: 2026-10-11
- **Decisores**: equipo (fase 0 de la planificación)

## Contexto

El sistema debe aislar la información por carrera, administrar cuentas de usuarios externos y sostener las restricciones de integridad que protegen el historial. El lineamiento del proyecto real es PostgreSQL. Origen: [research.md, Tema 2](../../specs/001-seguimiento-practicas/research.md).

## Decisión

Usar **PostgreSQL** como motor del sistema. SQLite queda solo como comodidad del prototipo actual (`backend/config/settings.py` aún apunta a `db.sqlite3`); la configuración con PostgreSQL llega en #76 y la operativa en [0010](0010-adoptar-django-rest-framework-y-postgresql.md) y [0013](0013-contenerizacion-con-docker-compose.md).

## Alternativas consideradas

- **SQLite**: cómodo para pruebas locales, pero no reproduce la concurrencia, los tipos ni la integridad de PostgreSQL.
- **MySQL o MariaDB**: cumpliría lo básico, pero no aporta nada frente a PostgreSQL y agrega una divergencia con el lineamiento del proyecto real.

## Consecuencias

- **Positivas**: restricciones de integridad y tipos fieles al entorno real; el aislamiento por carrera se expresa directamente en las consultas.
- **Negativas o costos**: hace falta un servicio de base en desarrollo y CI (compose y servicio de GitHub Actions).
- **Pendiente**: migrar `settings.py` a las variables `POSTGRES_*` (#76).

## Referencias

- [research.md, Tema 2](../../specs/001-seguimiento-practicas/research.md)
- [data-model.md](../../specs/001-seguimiento-practicas/data-model.md)
