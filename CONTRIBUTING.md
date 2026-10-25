# Guía de contribución — GitFlow

Este repositorio usa **GitFlow** (modelo de Vincent Driessen, edición AVH). La idea central es que `main` es producción y `develop` es integración: nadie trabaja directamente sobre ellas, todo pasa por ramas cortas y Pull Requests.

## Requisitos

Tener instalada la extensión `git-flow` (no viene con Git). Verificá con:

```bash
git flow version
```

Si no aparece, instalala:

- **EndeavourOS / Arch:** `yay -S gitflow-avh`
- **Debian / Ubuntu:** `sudo apt install git-flow`
- **macOS:** `brew install git-flow-avh`

## Ramas del modelo

| Rama | Propósito | Se alimenta de | Se fusiona en |
| --- | --- | --- | --- |
| `main` | Código estable / entregable | `release/`, `hotfix/` | — |
| `develop` | Integración del próximo release | `feature/`, `release/`, `hotfix/` | `release/` |
| `feature/*` | Una funcionalidad nueva | `develop` | `develop` |
| `bugfix/*` | Corrección de un bug no urgente | `develop` | `develop` |
| `release/*` | Preparar una versión (solo ajustes) | `develop` | `main` y `develop` |
| `hotfix/*` | Corregir algo urgente en producción | `main` | `main` y `develop` |

Rama por defecto del repo en GitHub: `develop`.

## Flujo diario

### 1. Empezar una funcionalidad

```bash
git checkout develop
git pull
git flow feature start mi-funcionalidad
# ... trabajás y commiteás ...
git flow feature finish mi-funcionalidad
```

Al terminar, `feature finish` la fusiona en `develop` y borra la rama local.

### 2. Publicar la rama para revisión (Pull Request)

Si querés que el equipo revise antes de fusionar:

```bash
git flow feature publish mi-funcionalidad
```

Eso la sube a GitHub. Ahí abrí el Pull Request **hacia `develop`**.

### 3. Corrección no urgente

```bash
git flow bugfix start arreglar-validacion-horas
git flow bugfix finish arreglar-validacion-horas
```

### 4. Preparar una entrega / release

```bash
git flow release start v1.0.0
# ajustes finales, versión, changelog...
git flow release finish v1.0.0
```

`release finish` fusiona en `main` y en `develop`, y crea el tag. Requiere un Pull Request aprobado para entrar a `main`.

### 5. Hotfix urgente en producción

```bash
git flow hotfix start corregir-error-critico
git flow hotfix finish corregir-error-critico
```

## Reglas del repositorio

- **`main` está protegida:** no acepta push directo, exige Pull Request con **1 aprobación** y no permite force-push ni borrado.
- **`develop` está protegida:** sin push forzado ni borrado. Es la rama de integración.
- **Convención de commits (Conventional Commits):**

  ```text
  feat: nueva funcionalidad
  fix: corrección de bug
  docs: cambios en documentación
  refactor: refactor sin cambio de comportamiento
  test: tests
  chore: tareas de mantenimiento
  ```

  Ejemplo: `feat: agregar registro de asistencia con horas`

- **Un Pull Request = un tema.** Mantenelo chico y revisable.

## Comandos útiles

```bash
git flow config          # ver la configuración actual de gitflow
git flow feature          # listar ramas de feature
git branch -a            # ver todas las ramas
```

## Seguimiento del prototipado por actor (PR #47 / #48)

El prototipo cubre a todos los actores de la [§3 del README](README.md#3-actores). El estudiante ya está hecho (PR #48, pantallas E1–E6 con el shell SIAAF). El resto se reparte **en el orden de la tabla**: cada prototipo usa el shell y los patrones del anterior, así que no se arranca a ciegas. Cada integrante **marca su fila** al abrir el PR y la re-marca al mergear.

| Orden | Integrante | Actores asignados | Pantallas | Depende de | PR abierto | Mergeado |
| :---: | --- | --- | --- | --- | :---: | :---: |
| 0 (base) | Alejandro (`AlejandroTatum`) | Estudiante | E1–E6 + shell, `siaaf.css`, includes y `sample_data` | — | ✅ #48 | ✅ #48 |
| 1 | Ivett (`ivecanahi`) | Tutor académico · Tutor de la entidad | T1–T5 · R1–R5 (ver [mapa](docs/mapa-pantallas.md)) | Base (E2/E5/E4 como referencia de detalle y formulario) | ✅ #56 · #57 | ✅ #56 · #57 |
| 2 | Melissa (`Kthiu666`) | Coordinador · Analista de prácticas (DVS) | C1–C7 · A1–A2 (analista: nuevo, patrón de lista con exportación) | Orden 1 (el estado que ve el coordinador resulta de las validaciones del tutor) | ✅ #66 | ⬜ |
| 3 | Doménica (`dme-e`) | Director de carrera · Secretaría de carrera | D1–D2 (director: consulta del cierre) · S1 (secretaría: legalización de anexos; ambos nuevos, patrón de detalle) | Orden 2 (el cierre que consultan lo ejecuta el coordinador) | ✅ #68 | ⬜ |
| 4 | Jaime (`Jaimewww`) | Entidad receptora · Rectorado/Decanato | N1 (catálogo de entidades) · N2 (convenios, **fuera del MVP**: proyecto R; solo consulta) | — (catálogo consultivo, independiente) | ⬜ | ⬜ |

**Reglas del prototipado** (verificar contra [spec.md](specs/001-seguimiento-practicas/spec.md) antes de abrir el PR):

- Reusar el shell y los patrones del PR #48: `backend/templates/base.html`, `backend/static/css/siaaf.css`, los includes (`form_field`, `estado_badge`, `icon`) y el estilo de `sample_data.py`; nada de frameworks nuevos.
- Cada pantalla del [mapa](docs/mapa-pantallas.md) tiene su historia y su requisito: la pantalla debe mostrarlos tal cual (estados, vacíos, errores de la §4 del mapa).
- No inventar flujos fuera del alcance: lo que el spec deja fuera (postulación, convenios como proyecto R, certificado, encuesta) va etiquetado «fuera del MVP» o no se prototipa.
- Cada prototipo lleva tests de sus vistas y datos con `sample_data`, igual que el PR #48.
- Pantallas nuevas (las que el mapa no define): respetar el patrón del SIAAF de [docs/referencia-siaaf.md](docs/referencia-siaaf.md) y anotar la decisión en el PR.

## Seguimiento del API base v1 ([docs/api.md](docs/api.md))

Cada aporte entrega **una funcionalidad nueva**: endpoint, tests (test-first) y su incorporación en las pantallas (creando las vistas que falten con el estilo del sistema). El orden marca las dependencias: una validación no se puede exponer sin el recurso de prácticas que consulta.

| Orden | Integrante | Funcionalidad nueva | Endpoints | Pantallas | Depende de | PR abierto | Mergeado |
| :---: | --- | --- | --- | --- | --- | :---: | :---: |
| 1 | Jaime (`Jaimewww`) | API base (contrato de errores JSON, DTO y fachada) + consulta de prácticas, estado y horas por rol (HU-04, HU-05) | `GET /api/v1/practicas/` · `GET /api/v1/practicas/<id>/` | Índice `/prototipo/` (nuevo, con sección API v1) | — | ✅ #65 | ✅ #65 |
| 2 | Ivett (`ivecanahi`) | Validar o devolver planes, reportes e informes con observación (RF-03, RF-04) | `PATCH /api/v1/pendientes/<clave>/` | T2 (Revisar) | Orden 1 | ✅ #69 | ✅ #69 |
| 3 | Melissa (`Kthiu666`) | Alertas activas del actor (RF-07) y cierre con guard (RF-09, CE-05) | `GET /api/v1/alertas/` · `POST /api/v1/practicas/<id>/cierre/` | C2 (Alertas) · C4 (Cerrar) | Orden 2 | ⬜ | ⬜ |
| 4 | Doménica (`dme-e`) | Historial inalterable (RF-10, HU-09) y legalización de anexos (RF-04), #62 | `GET /api/v1/practicas/<id>/historial/` · `POST /api/v1/anexos/<id>/legalizacion/` | D2 · S2 | Orden 3 | ⬜ | ⬜ |
| 5 | Alejandro (`AlejandroTatum`) | Envío de reportes semanales, horas y evidencias PDF (RF-03, RF-15, RNF-05), #64 | `POST /api/v1/practicas/<id>/reportes/` | E4 (Nuevo reporte semanal) | Órdenes 1 y 2 (#63, #60) | ✅ #67 | ⬜ |

Issues: Jaime #63 → Ivett #60 → Melissa #61 → Doménica #62; Alejandro #64 depende de #63 y #60 y puede trabajar en paralelo al orden 3. `X-Rol` es únicamente un selector de persona sintética: el API del prototipo exige `DEBUG=True`, no implementa autenticación ni persistencia reales. Los reportes del orden 5 se guardan solo en la sesión del navegador que los envía y se borran con «Reiniciar demo» en E2 ([docs/api.md §5](docs/api.md#5-envío-de-reportes-semanales-implementado-alejandro-64)).
