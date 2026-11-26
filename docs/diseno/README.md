# Propuesta visual: prototipos de todos los roles

Prototipos HTML **navegables** del sistema de seguimiento de prácticas, con el estilo del SIAAF renovado (barra lateral azul marino con la mascota y el logo de la UNL, barra superior flotante, banner rectangular, tarjetas crema y Poppins). Son maquetas estáticas con datos de ejemplo tomados de `backend/apps/prototipo/sample_data.py`: no hablan con el backend ni guardan nada en servidor.

## Cómo abrirlos

Abra `system.html` en el navegador (doble clic o `xdg-open docs/diseno/system.html`). Es el tablero maestro: lista las 46 pantallas por rol y tiene un botón para entrar como cada uno. Dentro de cualquier pantalla, el menú de usuario (arriba a la derecha) permite **cambiar de rol** sin volver al tablero.

## Qué hay

| Carpeta | Contenido |
| --- | --- |
| `system.html` | Tablero maestro, sistema visual y fidelidad con el repositorio |
| `home-estudiante/`, `pantallas-estudiante/` | Estudiante: tablero y E1 a E6 (9 pantallas) |
| `prototipo-roles/` | `ta-` tutor académico (8) · `te-` tutor de la entidad (6) · `co-` coordinador (9) · `di-` director (4) · `se-` secretaría (3) · `an-` analista DVS (3) · `en-` entidad receptora, Rectorado/Decanato (4) |
| `assets/` | Fuente Poppins, logo de la UNL, mascota y foto del campus (se usan solo en la barra lateral y en los tableros) |

Los identificadores (E1, T2, C4, D1, S2, A1, N1…) son los de [`docs/mapa-pantallas.md`](../mapa-pantallas.md).

## Qué se puede probar

- Filtros que filtran las filas de las tablas (prácticas, pendientes, consolidados, catálogo).
- Contadores con botones − y +, que también admiten escribir el valor.
- Validaciones: devolver sin observación, motivo obligatorio al suspender o cancelar, evidencias que no son PDF o pesan más de 5 MB, ayudantía con más de 10 h (Art. 341).
- Estados vacíos y variantes de estado (en curso, en revisión final, suspendida, cancelada, cerrada).
- Descarga real de CSV (UTF-8, fechas ISO 8601) en el consolidado del coordinador y en la exportación del analista.
- Legalización de anexos de una sola vez, con autor y fecha.

## Traducción a la aplicación

`frontend/src/styles.css` y `frontend/src/app/layout/` traducen esta propuesta a variables CSS y al marco de la aplicación Angular. La pantalla E4 (`registrar-reporte`) es la primera que la usa.

## Notas

- Es material de consulta: las pantallas no se rigen por la lógica del backend. Algunos datos son inventados para mostrar un estado (por ejemplo, las actividades de ciertas semanas o las observaciones de devolución de ejemplo).
- La mascota y la foto del campus están pendientes de confirmar permisos de uso.
