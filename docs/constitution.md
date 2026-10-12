# Constitución del equipo — Sistema de prácticas preprofesionales (APE-001)

**Versión**: 0.1 (borrador para ratificación del equipo) | **Fecha**: 2026-10-12 | **Estado**: en revisión por PR

## Propósito

La constitución fija los principios que el equipo acepta para desarrollar este proyecto. Rige sobre las herramientas: los principios se cumplen aunque una herramienta concreta (por ejemplo Spec Kit) no esté versionada en el repositorio. Cada principio dice qué exige y cómo se verifica en el repositorio.

## Principios

### I. GitFlow estricto

**Qué exige**: `main` es producción y solo recibe `release/*` o `hotfix/*`; `develop` es integración y solo recibe `feature/*`, `bugfix/*`, `release/*` o `hotfix/*`. Nadie pushea directo a `main` ni a `develop`: todo llega por Pull Request.

**Cómo se verifica**: protección de ramas activa en `main` (PR + 1 aprobación, sin force-push ni borrado) y en `develop` (sin force-push ni borrado); historial del repo con merges y sin commits directos a las ramas protegidas. Las ramas de los PRs se borran automáticamente al mergear.

### II. Pull Requests chicas y revisadas

**Qué exige**: un PR cubre un solo tema y es revisable (si supera ~400 líneas o toca varias áreas, se parte). El merge a `main` exige una aprobación de otra persona; a `develop` alcanza con la revisión del responsable del tema.

**Cómo se verifica**: revisión de PRs del historial: título in format Conventional Commit, descripción con cambios y verificación, y una sola área por PR.

### III. Conventional Commits

**Qué exige**: cada mensaje de commit usa tipo (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`) y, cuando hace falta, scope, con subject claro en español o inglés, consistente dentro del mismo PR.

**Cómo se verifica**: `git log --format=%s` del historial del repo.

### IV. Fases SDD documentadas en el repositorio

**Qué exige**: cada funcionalidad deja sus artefactos de fases en `specs/NNN-nombre/`: `spec.md` (specify/clarify), `plan.md`, `research.md`, `data-model.md` (plan) y `tasks.md` (tasks) antes de implementar. Las herramientas de autoría (Spec Kit, `.opencode/`) no se versionan: son locales; sus productos sí.

**Cómo se verifica**: por cada funcionalidad en `specs/` existe la cadena de documentos y su `tasks.md` referenciado desde el `plan.md`.

### V. Decisiones registradas con justificación

**Qué exige**: toda decisión de arquitectura, stack o normativa se documenta en `research.md` con `Decision`, `Rationale` y `Alternatives considered`. Los temas abiertos se marcan con `[NEEDS CLARIFICATION]` y se cierran en una sesión de clarify antes de generar tareas.

**Cómo se verifica**: `research.md` de la funcionalidad no declara temas abiertos sin resolver al momento de generar `tasks.md`.

### VI. Código con tests, documentación verificable

**Qué exige**: cuando el cambio tiene tests aplicables, se escriben primero (RED → GREEN → refactor). Para documentación y configuraciones sin runner, se verifica por estructura y ejecución de lo que sí se puede correr. El README debe permitir reproducir el entorno completo desde cero.

**Cómo se verifica**: la funcionalidad corre la suite de tests; el README permite instalar, ejecutar y verificar el endpoint `/health`; la prueba cruzada (una persona distinta del autor sigue el README) queda registrada en `docs/contribuciones.md`.

### VII. Cumplimiento y evidencias

**Qué exige**: cada integrante deja constancia de su contribución (commits y PRs en `main`) y de su uso de IA en `docs/contribuciones.md` y `docs/declaracion-ia.md`; el repositorio guarda evidencias de ramas, PRs y protección en `evidencias/`, y las entregas finales en `entregables/`.

**Cómo se verifica**: la rúbrica de la APE-001 se cubre desde el propio repositorio: filas completadas por cada integrante, capturas subidas con fechas y los PDF finales en `entregables/`.

## Gobernanza

Esta constitución se modifica por Pull Request a `develop`, aprobado por la mayoría del equipo; los cambios de `main` siguen exigiendo la aprobación de otra persona. Si un principio entra en conflicto con una decisión de cátedra, gana la decisión de cátedra y se registra la excepción aquí.

**Versión**: 0.1 | **Fecha**: 2026-10-12 | **Ratificada por**: pendiente de revisión del equipo