# 0014. Integración continua con GitHub Actions

- **Estado**: Aceptada
- **Fecha**: 2026-11-03
- **Decisores**: equipo (issue #82)

## Contexto

El repositorio ya vive en GitHub y la constitución exige PRs chicos y revisados (principios I y II), código con pruebas y linter sin errores (RNF-09). Hasta ahora esa verificación dependía de que cada autor corriera las pruebas a mano.

## Decisión

Un workflow de **GitHub Actions** (`.github/workflows/ci.yml`) corre en cada PR y en los push a `develop` y `main`, y **falla si fallan lint o pruebas**. Jobs:

1. **Lint** con `ruff` (configuración en `pyproject.toml`).
2. **Pruebas con cobertura** contra un servicio **PostgreSQL** del job; el reporte de `coverage` queda en el log y como artefacto `coverage.xml`.
3. **Build de la imagen Docker** ([0013](0013-contenerizacion-con-docker-compose.md)).
4. **Render de Quarto** del portal, cuando exista (#85).

El workflow usa `permissions: contents: read`, valores de CI que no son secretos y no recibe secretos del repositorio. Un badge en el README muestra el estado.

## Alternativas consideradas

- **GitLab CI o Jenkins**: el repositorio y las revisiones ya están en GitHub; un servidor propio sumaría mantenimiento.
- **Solo hooks locales (`pre-commit`)**: son evitables y no dejan registro ni bloquean el merge.
- **Verificación manual en la revisión de PR**: no escala y depende de la memoria del revisor.

## Consecuencias

- **Positivas**: regresiones detectadas antes del merge; la cobertura y el build quedan auditables; las pruebas corren sobre PostgreSQL como el entorno real.
- **Negativas o costos**: minutos de CI consumidos en cada push; hay que mantener fijas las versiones de acciones y herramientas.
- **Pendiente**: exigir el check como requisito de merge en la protección de ramas de GitHub (configuración del repositorio, no verificada aquí); pasar de `manage.py test` a `pytest --cov` con #80; añadir el paso de Quarto con #85; escaneo de dependencias (ver [seguridad.md](../seguridad.md), A06).

## Referencias

- Issue #82, `.github/workflows/ci.yml`
- [docs/constitution.md](../constitution.md)
