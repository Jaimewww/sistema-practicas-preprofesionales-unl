# Diagramas de arquitectura (C4)

Modelo C4 del sistema de seguimiento de prácticas. Los elementos **planificados** (aún sin implementar; dependen de los issues #76 a #80, #85 y #86) se marcan con la etiqueta `Planificado`, trazo discontinuo y el prefijo `[PLANIFICADO]` en la descripción.

| Archivo | Nivel | Contenido |
| --- | --- | --- |
| [workspace.dsl](workspace.dsl) | C1, C2, C3 y despliegue | Workspace de Structurizr, fuente única de los cuatro diagramas siguientes. |
| [c1-contexto.svg](c1-contexto.svg) | C1 Contexto | Actores (estudiante, tutor académico, tutor de la entidad, coordinador, director y secretaría) y el SIAAF como sistema externo fuera de alcance. |
| [c2-contenedores.svg](c2-contenedores.svg) | C2 Contenedores | API backend, prototipo web, PostgreSQL, almacén de evidencias, Swagger UI/OpenAPI y portal Quarto. |
| [c3-componentes-api.svg](c3-componentes-api.svg) | C3 Componentes | Componentes del backend por capas: seguridad de Django, API demo, fachada, DTO, reglas, estado de demo y, planificados, vistas DRF, serializers, renderer, permisos, casos de uso, dominio, repositorios y observabilidad. |
| [d1-despliegue.svg](d1-despliegue.svg) | Despliegue | Servicios `api` y `db` de `docker-compose.yml`. |
| [c4-codigo.puml](c4-codigo.puml) | C4 Código | Diagrama de clases en PlantUML con las clases y funciones reales de `backend/apps/prototipo` y `apps/health`, más la capa DRF «planificado». |
| [c4-codigo.svg](c4-codigo.svg) | C4 Código | Render del anterior. |

> **Mantenimiento**: actualizar `c4-codigo.puml` y el C3 al mergear #76 y #78 (las clases «planificado» son los nombres previstos, no las reales). Los SVG se regeneran con los comandos de abajo.

## Cómo validar y renderizar

Hace falta Docker. Ejecuta los comandos desde la raíz del repositorio.

**Validar el DSL** (imagen vigente `structurizr/structurizr`; la imagen anterior `structurizr/cli` está deprecada y ya no valida):

```bash
docker run --rm -v "$PWD/docs/arquitectura:/usr/local/workspace" \
  structurizr/structurizr validate -w /usr/local/workspace/workspace.dsl
```

Sin salida y código `0` significa que es válido; un error muestra la línea.

**Ver los diagramas de forma interactiva** (<http://localhost:8080>):

```bash
docker run --rm -p 8080:8080 -v "$PWD/docs/arquitectura:/usr/local/structurizr" \
  structurizr/structurizr local
```

**Regenerar los SVG de C1, C2, C3 y despliegue** (exporta a C4-PlantUML y renderiza):

```bash
mkdir -p /tmp/c4 && docker run --rm --user "$(id -u):$(id -g)" \
  -v "$PWD/docs/arquitectura:/usr/local/workspace" -v /tmp/c4:/out \
  structurizr/structurizr export -w /usr/local/workspace/workspace.dsl -f plantuml/c4plantuml -o /out
docker run --rm --user "$(id -u):$(id -g)" -v /tmp/c4:/data plantuml/plantuml -tsvg /data/*.puml
# copiar structurizr-C1-Contexto.svg a c1-contexto.svg, y así con C2, C3 y D1
```

La exportación C4-PlantUML no conserva las etiquetas ni los estilos del DSL; por eso el prefijo `[PLANIFICADO]` va en las descripciones. El trazo discontinuo se ve en Structurizr Local.

**Renderizar el diagrama de código**:

```bash
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD/docs/arquitectura:/data" \
  plantuml/plantuml -tsvg /data/c4-codigo.puml
```

## Fuentes

Actores y alcance: [spec.md](../../specs/001-seguimiento-practicas/spec.md) §2 · SIAAF: [referencia-siaaf.md](../referencia-siaaf.md) · Módulos y patrones: [arquitectura.md](../arquitectura.md) · Decisiones: [ADR](../adr/README.md) · Amenazas: [seguridad.md](../seguridad.md).
