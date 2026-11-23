# SIAAF design system (prototype)

Synced from `backend/static/css/siaaf.css` (the only app stylesheet). The deck themes under
`odd/expo-avances/.../themes/` style presentation slides, not the product, and are excluded.
Every value below appears in that source; nothing is invented.

## Colors

| Token | Value | Usage | Source |
| --- | --- | --- | --- |
| `--brand` | `#1880c9` | Sidebar brand block (Académico module) | `backend/static/css/siaaf.css` |
| `--navy` | `#00509e` | Primary button, active tab, links, focus ring, validated hours | `backend/static/css/siaaf.css` |
| `--navy-dark` | `#003d7a` | Hover of navy elements | `backend/static/css/siaaf.css` |
| `--bg` | `#eaeef3` | Page background | `backend/static/css/siaaf.css` |
| `--surface` | `#ffffff` | Cards, panels, topbar, sidebar | `backend/static/css/siaaf.css` |
| `--text` | `#212121` | Body text | `backend/static/css/siaaf.css` |
| `--muted` | `#5a6068` | Secondary text, filter labels | `backend/static/css/siaaf.css` |
| `--menu` | `#444444` | Sidebar items, icon buttons | `backend/static/css/siaaf.css` |
| `--title` | `#666666` | Page title (light 300) | `backend/static/css/siaaf.css` |
| `--panel-title` | `#3a405b` | Panel titles | `backend/static/css/siaaf.css` |
| `--head` | `#d7dde4` | Detail card header band | `backend/static/css/siaaf.css` |
| `--head-text` | `#333333` | Detail card title, tab text | `backend/static/css/siaaf.css` |
| `--strip` | `#d5d6da` | Tab strip | `backend/static/css/siaaf.css` |
| `--line` | `#dee2e6` | Row separators | `backend/static/css/siaaf.css` |
| `--line-strong` | `#c8ccd2` | Table head rule, notice border | `backend/static/css/siaaf.css` |
| `--dotted` | `#c3c8ce` | Panel title dotted rule | `backend/static/css/siaaf.css` |
| `--pill` | `#e5e5e9` | Breadcrumb pill | `backend/static/css/siaaf.css` |
| `--field-border` | `#7b838c` | Form field border (3:1) | `backend/static/css/siaaf.css` |
| `--footer` | `#222c3c` | Footer | `backend/static/css/siaaf.css` |
| `--footer-top` | `#1c262f` | Back-to-top button | `backend/static/css/siaaf.css` |
| `--ok` | `#2e7d32` | OK badge, success notice | `backend/static/css/siaaf.css` |
| `--warn` | `#f9c851` | Warn badge (dark text on it) | `backend/static/css/siaaf.css` |
| `--bad` | `#b71c1c` | Bad badge, errors | `backend/static/css/siaaf.css` |
| `--neutral` | `#5a6068` | Neutral badge | `backend/static/css/siaaf.css` |
| `--teal` | `#008192` | Pill button (create action) | `backend/static/css/siaaf.css` |
| `--teal-dark` | `#00697a` | Pill button hover | `backend/static/css/siaaf.css` |
| `--required` | `#b71c1c` | Required marker | `backend/static/css/siaaf.css` |

Literal component colors (not tokens, used in the same file): in-review hours `#7fa9d3`, progress track
`#e3e7ec`, active sub-item `#eef4fa`, hover `#f3f6f9`, error summary bg `#fdecea`, ok notice bg `#edf6ee`,
warn notice bg `#fff8e1` with border `#a87700`, selection `#b9d6ef`, footer link `#8cc4f4`.

## Typography

| Token | Value | Usage | Source |
| --- | --- | --- | --- |
| `font-family` | `"Poppins", system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif` | Everything (weights 300/400/500/600) | `backend/static/css/siaaf.css` |
| `body` | `0.875rem / 1.55` | Body text | `backend/static/css/siaaf.css` |
| `.page-title` | `1.6rem / 300` | Page title, color `--title` | `backend/static/css/siaaf.css` |
| `.panel__title` | `1.15rem / 600` | Panel title | `backend/static/css/siaaf.css` |
| `.detail-card__title` | `1.1rem / 400` | Card header title | `backend/static/css/siaaf.css` |
| `.badge` | `0.68rem / 600 uppercase, 0.03em` | Status tags | `backend/static/css/siaaf.css` |
| numbers | `font-variant-numeric: tabular-nums` | Tables, legends | `backend/static/css/siaaf.css` |

## Spacing and layout

| Token | Value | Usage | Source |
| --- | --- | --- | --- |
| `--sidebar-w` | `14.7rem` | Sidebar width | `backend/static/css/siaaf.css` |
| `--topbar-h` | `3.75rem` | Topbar and brand height | `backend/static/css/siaaf.css` |
| content padding | `1.25rem` (`0.75rem` under 48em) | Main column | `backend/static/css/siaaf.css` |
| card gap | `1.25rem` | Between cards | `backend/static/css/siaaf.css` |
| card body | `1rem` | Detail card body | `backend/static/css/siaaf.css` |

## Radius and shadows

| Token | Value | Usage | Source |
| --- | --- | --- | --- |
| `--radius` | `4px` | Fields, buttons, notices | `backend/static/css/siaaf.css` |
| `--shadow` | `0 1px 4px rgba(0, 0, 0, 0.14)` | Cards and panels | `backend/static/css/siaaf.css` |
| `--ease` | `cubic-bezier(0.16, 1, 0.3, 1)` | Sidebar, chevrons | `backend/static/css/siaaf.css` |
| pill | `999px` / `1.25rem` | Pill button, breadcrumb | `backend/static/css/siaaf.css` |

## Component rules

- Shell: white sidebar with `--brand` block on top, sticky white topbar with shadow, `--bg` content, dark `--footer`.
- Detail card: `--head` header band with title left and status badges or a teal pill action right; white body.
- Badges carry meaning in the label; color only reinforces (`ok`, `warn`, `bad`, `info` navy, `neutral`).
- Primary button navy, secondary `#e1e5ec` with navy text; create actions use the teal pill button.
- Hours progress: navy = validated, `#7fa9d3` = in review, a 3px `--text` tick = expected to date.
- Focus: `3px solid --navy` outline, 2px offset. Breakpoints: sidebar overlay ≤ 62em, stacked tables ≤ 48em.
- Motion only via `--ease`; `prefers-reduced-motion` disables it.
