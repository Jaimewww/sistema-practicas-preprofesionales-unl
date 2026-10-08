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
