"""Renderiza un documento Markdown a PDF (A4) con el formato de los entregables.

Uso: python render_pdf.py entrada.md salida.pdf
Requiere: markdown y playwright (con Chromium instalado).
"""
import base64
import re
import sys
from pathlib import Path

import markdown
from playwright.sync_api import sync_playwright

TEAL = "#14506b"
LOGO = Path(__file__).with_name("unl-logo.png")

src, out = Path(sys.argv[1]), Path(sys.argv[2])
md = src.read_text(encoding="utf-8")

# Título principal: se extrae para mostrarlo solo en la primera página.
m = re.match(r"# (.+)\n", md)
title = m.group(1).strip()
md = md[m.end():]

body = markdown.markdown(md, extensions=["tables", "fenced_code"])

# La tabla de identificación no lleva fila de encabezado (Campo | Valor).
body = re.sub(
    r"<thead>\s*<tr>\s*<th>Campo</th>\s*<th>Valor</th>\s*</tr>\s*</thead>\s*", "", body, count=1
)


def mark_small_tables(match):
    html = match.group(0)
    rows = html.count("<tr>")
    return html.replace("<table>", '<table class="keep">', 1) if rows <= 7 else html


body = re.sub(r"<table>.*?</table>", mark_small_tables, body, flags=re.S)



def nowrap_short_cells(match):
    text = re.sub(r"<[^>]+>", "", match.group(3)).strip()
    if len(text) <= 14:
        return f'<{match.group(1)} class="nw"{match.group(2) or ""}>{match.group(3)}</{match.group(1)}>'
    return match.group(0)


# Celdas cortas (IDs como RF-01, «Seguro») no se parten.
body = re.sub(r"<(t[dh])(\s[^>]*)?>(.*?)</\1>", nowrap_short_cells, body, flags=re.S)

# El párrafo que introduce una tabla no se queda solo al final de una página.
body = re.sub(r"<p>((?:(?!</p>).)*)</p>(\s*<table)", r'<p class="lead">\1</p>\2', body, flags=re.S)

# La bibliografía se mantiene en una sola página.
# (bibliografía libre para no forzar una página propia)

# Párrafos que solo contienen negrita (p. ej. «Requisitos corregidos») no se separan de lo siguiente.
body = re.sub(r"<p>(<strong>[^<]*</strong>)</p>", r'<p class="lead">\1</p>', body)

css = f"""
@page {{ size: A4; }}
* {{ box-sizing: border-box; }}
body {{ font-family: 'Montserrat','DejaVu Sans',sans-serif; font-size: 9pt; line-height: 1.4;
       color: #111; margin: 0; text-align: justify; hyphens: manual; }}
h1 {{ font-family: 'Nimbus Sans','Liberation Sans',Arial,sans-serif; font-weight: 400; font-size: 24pt;
      line-height: 1.2; text-align: center; margin: 6mm 0 8mm; }}
h2, h3 {{ color: {TEAL}; font-weight: 700; text-align: left; break-after: avoid; }}
h2 {{ font-size: 12.5pt; margin: 6mm 0 2.5mm; }}
h3 {{ font-size: 10.5pt; margin: 4.5mm 0 2mm; }}
p {{ margin: 2mm 0; overflow-wrap: break-word; }}
p.lead {{ break-after: avoid; margin-top: 4mm; }}
ul, ol {{ margin: 2mm 0; padding-left: 6mm; }}
table {{ border-collapse: collapse; width: 100%; margin: 2.5mm 0 3mm; font-size: 8pt;
         line-height: 1.35; text-align: left; table-layout: auto; }}
table.keep {{ break-inside: avoid; }}
thead {{ display: table-header-group; }}
tr {{ break-inside: avoid; }}
th, td {{ border: 0.6pt solid #9aa5ad; padding: 1.1mm 2mm; vertical-align: top;
          overflow-wrap: break-word; }}
td.nw, th.nw {{ white-space: nowrap; }}
.keep {{ break-inside: avoid; }}
th {{ background: #eef2f5; font-weight: 700; }}
pre {{ background: #f1f2f4; border: 0.6pt solid #d3d7db; border-radius: 2px; padding: 2.5mm;
       margin: 3mm 0; break-inside: avoid; white-space: pre-wrap; overflow-wrap: anywhere;
       font-size: 7.4pt; line-height: 1.35; text-align: left; }}
code {{ font-family: 'Liberation Mono','DejaVu Sans Mono',monospace; font-size: .92em; overflow-wrap: break-word; }}
pre code {{ font-size: inherit; }}
"""
doc = (
    f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>{title}</title>'
    f"<style>{css}</style></head><body><h1>{title}</h1>{body}</body></html>"
)

logo = base64.b64encode(LOGO.read_bytes()).decode()
header = f"""<div style="width:100%;margin:0 18mm;font-family:Montserrat,sans-serif;font-size:8pt;color:#222;">
<div style="display:flex;justify-content:space-between;align-items:center;padding-bottom:2mm;border-bottom:0.6pt solid #222;">
<img src="data:image/png;base64,{logo}" style="height:12mm;">
<span>FEIRNNR - Carrera de Computación</span></div></div>"""
footer = """<div style="width:100%;text-align:center;font-family:Montserrat,sans-serif;font-size:8pt;color:#222;">
<span class="pageNumber"></span></div>"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_content(doc, wait_until="load")
    page.pdf(
        path=str(out),
        format="A4",
        print_background=True,
        display_header_footer=True,
        header_template=header,
        footer_template=footer,
        margin={"top": "27mm", "bottom": "16mm", "left": "20mm", "right": "20mm"},
    )
    browser.close()
print(f"ok: {out}")
