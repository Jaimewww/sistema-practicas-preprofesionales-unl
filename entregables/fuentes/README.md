# Fuentes de los entregables

Esta carpeta contiene lo necesario para regenerar los entregables que se redactan en Markdown.

| Archivo | Contenido |
| --- | --- |
| `acd2-requisitos-http.md` | Texto fuente del ACD 2 (requisitos verificables y fundamentos de HTTP). |
| `render_pdf.py` | Convierte un archivo Markdown en PDF (A4) con el formato de los entregables: encabezado con logo y «FEIRNNR - Carrera de Computación», secciones numeradas, tablas con rejilla, bloques de código en caja gris y numeración al pie. |
| `unl-logo.png` | Logo de la UNL usado en el encabezado, extraído de `../acd1-sintesis.pdf`. |

## Regenerar el PDF

Se necesita `uv` y el Chromium de Playwright (`playwright install chromium`). Desde la raíz del repositorio:

```bash
uv run -q --no-project --with markdown --with "playwright==1.*" python -I entregables/fuentes/render_pdf.py entregables/fuentes/acd2-requisitos-http.md entregables/acd2-requisitos-http.pdf
```

El comando sobrescribe `entregables/acd2-requisitos-http.pdf`. El contenido se edita solo en el `.md`; el PDF es el archivo que se entrega.
