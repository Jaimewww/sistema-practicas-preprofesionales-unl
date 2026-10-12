# Evidencias — APE-001

Acá se suben las capturas que respaldan la rúbrica. Cada archivo lleva una descripción en el nombre o en una fila de `docs/contribuciones.md`.

## Capturas requeridas (pendientes de subir)

| Evidencia | Qué debe mostrar | Cómo obtenerla |
| --- | --- | --- |
| `ramas.png` | Listado de ramas remotas del repositorio (durante el desarrollo y/o el estado final solo `main`/`develop`). | `git ls-remote --heads origin` o la página *Branches* de GitHub. |
| `prs.png` | Los Pull Requests del repositorio (#1 a #6) con su estado. | Página *Pull requests* en GitHub. |
| `proteccion-main.png` | Reglas de protección de `main`: requiere PR, 1 aprobación, sin force-push ni borrado. | *Settings → Branches* en GitHub. |
| `proteccion-develop.png` | Reglas de protección de `develop`: sin force-push ni borrado. | *Settings → Branches* en GitHub. |
| `auto-delete.png` | Configuración "Automatically delete head branches" activada. | *Settings → General → Pull Requests* en GitHub. |
| `release-tag.png` | Tag `v0.1.0` sobre `main` y su historial de releases. | Página *Releases* de GitHub. |
| `prueba-cruzada.png` | Captura de la prueba cruzada: una persona distinta del autor siguió el README y dejó constancia. | La persona que prueba captura el resultado. |

## Convención

- Nombre descriptivo (`ramas-desarrollo.png`, `proteccion-main.png`, …).
- Un archivo por evidencia; si hacen falta varias, numerar (`prs-1.png`, `prs-2.png`).
- Referenciar cada captura en la fila correspondiente de `docs/contribuciones.md`.