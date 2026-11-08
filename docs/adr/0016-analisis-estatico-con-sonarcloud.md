# 0016. Análisis estático y quality gate con SonarCloud

- **Estado**: Propuesta (pasa a Aceptada cuando el job reporte el primer análisis)
- **Fecha**: 2026-11-04
- **Decisores**: equipo (issue #82, seguimiento de [0014](0014-integracion-continua-con-github-actions.md))

## Contexto

El CI ([0014](0014-integracion-continua-con-github-actions.md)) ya ejecuta `ruff` (estilo y errores), `bandit` (patrones inseguros), `pip-audit` (CVE en dependencias) y las pruebas con cobertura. Estas herramientas responden "pasa o no pasa" en cada PR, pero no ofrecen:

- una vista histórica de la calidad (deuda técnica, duplicación, *code smells*);
- la cobertura **del código nuevo de cada PR**, y no solo el total;
- un **quality gate** visible en el PR que el revisor pueda usar como criterio.

La consigna valora "análisis estático" y "validaciones de calidad" automatizadas en GitHub Actions, y pide justificar toda tecnología adicional.

## Decisión

Agregar **SonarQube Cloud (SonarCloud)**, gratuito para repositorios públicos, como job `sonarcloud` del CI:

1. Corre después del job `test` y reutiliza su `coverage.xml`, así que no repite las pruebas.
2. La configuración vive en `sonar-project.properties`: los tests se cuentan como pruebas, y se excluyen las migraciones y los estáticos.
3. Usa el análisis **desde CI** (`SonarSource/sonarqube-scan-action`) y no el "Automatic Analysis" de SonarCloud, porque solo el primero puede importar la cobertura.
4. El token va en el secret `SONAR_TOKEN`. **Sin el secret, el job se saltea y queda en verde**: un PR desde un fork o un repositorio sin configurar no rompe el CI.
5. Se usa el quality gate por defecto ("Sonar way"), que evalúa el código nuevo.

## Alternativas consideradas

- **SonarQube Community en Docker local**: sin costo ni cuentas, pero no queda integrado a los PR y depende de que alguien lo corra.
- **Solo ruff + bandit**: ya están en el CI, pero no dan histórico, duplicación ni cobertura del código nuevo.
- **Codacy / CodeClimate**: cumplen una función parecida; SonarCloud es el estándar más difundido y el que la cátedra puede reconocer.
- **CodeRabbit (revisor con IA)**: complementa pero no reemplaza el análisis estático. La rúbrica valora la revisión entre integrantes, y su uso tendría que declararse en `declaracion-ia.md`, así que queda fuera de esta decisión.

## Consecuencias

- **Positivas**: el quality gate y la cobertura del código nuevo aparecen en cada PR; queda un histórico de métricas para la demostración y para el criterio 3 de la rúbrica.
- **Negativas o costos**: depende de un servicio externo y de un secret que solo el owner del repositorio puede cargar; el código del repositorio (público) se envía a SonarCloud.
- **Pendiente**: que el owner importe el proyecto y cargue `SONAR_TOKEN` (pasos en [Calidad con SonarCloud](../portal/calidad-sonarcloud.qmd)); evaluar después si el quality gate pasa a ser un check obligatorio en la protección de `develop`.

## Referencias

- `sonar-project.properties`, `.github/workflows/ci.yml` (job `sonarcloud`)
- <https://docs.sonarsource.com/sonarqube-cloud/>
- <https://github.com/SonarSource/sonarqube-scan-action>
