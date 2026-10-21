# Arquitectura y patrones de diseño

**Fecha**: 2026-10-21 | **Estado**: adoptada por el equipo (ver Gobernanza) | **Aplica a**: todo el backend y el prototipo

Registro de la decisión de arquitectura y los patrones de diseño del sistema, conforme al principio V de la [constitución](constitution.md) (decisiones con justificación y alternativas descartadas). El detalle operativo del API está en [api.md](api.md).

## 1. Arquitectura: monolito modular

**Decision**: un único proceso Django (un deploy, una base) organizado en **módulos por dominio** con fronteras explícitas.

**Rationale**: a la escala del MVP (5 carreras, ~300 estudiantes, ~150 prácticas activas — supuesto del `plan.md`), un monolito modular da la trazabilidad y el control de acceso que exige el problema sin el costo operativo de servicios distribuidos (despliegue, latencia de red, consistencia eventual). Django ya estructura el proyecto por aplicaciones: cada módulo de dominio es una app con frontera clara. Coincide con la decisión de integración institucional (RNF-11): un módulo del SIAAF es un servicio único detrás del sistema académico.

**Fronteras de módulo** (lo que hace "modular" al monolito):

1. Cada app de `backend/apps/` es un módulo: `usuarios`, `carreras`, `entidades`, `practicas`, `actividades`, `alertas`, `auditoria`, `reportes`, `prototipo` (ver estructura en [plan.md](../specs/001-seguimiento-practicas/plan.md)).
2. Un módulo expone su **fachada** (funciones de caso de uso y DTOs) y oculta sus internos: las vistas, el API y las plantillas solo consumen la fachada del módulo, nunca sus modelos o helpers privados.
3. Prohibido el acceso cruzado a modelos de otro módulo sin pasar por su fachada (lo verifica la revisión de PR).
4. En el prototipo, `sample_data.py` hace el papel del dominio: las fronteras se ejercen igual, y al implementar con PostgreSQL los módulos ya están delimitados.

**Alternatives considered**:

- **Microservicios**: descartados. El costo operativo (dos o tres despliegues, red, transacciones distribuidas, observabilidad) no se justifica a esta escala y contradice "arranca con un solo comando".
- **Monolito sin fronteras** (todo en una app gigante): descartado; es el punto de partida natural de Django pero pierde el aislamiento por dominio que la trazabilidad y el RBAC exigen.

## 2. Patrones adoptados

| Patrón | Dónde | Para qué |
| --- | --- | --- |
| **DTO** | `apps/<modulo>/dto.py` | Los payloads del API y los contextos de pantallas se arman con funciones DTO (`to_practica_dto`), que devuelven diccionarios con la forma exacta del contrato. El contrato del API no es la estructura interna: si cambia el modelo, el DTO absorbe el cambio y el contrato no se rompe. |
| **Facade** | `apps/<modulo>/facade.py` | La única puerta de entrada de cada módulo: funciones de caso de uso (`practicas_de(rol)`, `validar_reporte(...)`, `cerrar_practica(...)`). Las vistas del API y las de plantilla llaman a la fachada; nada consume modelos o helpers privados de otro módulo. |
| **Service layer** (decisión adicional) | `apps/<modulo>/services.py` | La lógica que no es solo lectura (validar, cerrar, suspender) vive en funciones de caso de uso separadas de las vistas. Django lo recomienda y mantiene las vistas finas y testeables. En el prototipo, la fachada y los servicios coinciden. |
| **Tabla de transiciones (State)** (decisión adicional) | `apps/practicas/estados.py` | La máquina de estados del spec (`asignada → en curso → …`) se implementa como **tabla explícita** `{estado: {acción: estado_nuevo}}` con sus guardas (RF-09, RF-13). Una transición no listada es un `409` del API, nunca un error 500. |

## 3. Patrones considerados y descartados

| Patrón | Decisión | Motivo |
| --- | --- | --- |
| **Repository** | Descartado por ahora | El dominio del prototipo es en memoria (`sample_data`); una capa de repositorio sobre diccionarios sería ceremonia sin valor. Al entrar PostgreSQL, el ORM de Django cumple ese rol; si un caso lo exige, se reintroduce solo en el módulo que lo necesite. |
| **Observer / Signals** | Diferido | Las alertas (RF-07) hoy las emite el comando programado (cron). Cuando el módulo real de alertas entre, las transiciones de estado pueden disparar señales de Django para notificar; no se añade hasta que exista más de un emisor. |
| **DRF / serializers** | Descartado (MVP) | Decisión de `research.md` (Tema 1): sin API REST completa en el MVP; el API v1 usa `JsonResponse` como `/health/`. Los DTO cubren la parte que un serializer haría. Re-evaluar solo si el producto pide una SPA. |

## 4. Capas (de afuera hacia adentro)

```text
URL / plantillas        (config/urls.py, apps/<modulo>/urls.py, templates/)
   │
API v1  (JsonResponse)  apps/<modulo>/api_urls.py + api.py        ─┐
   │                                                                     │ consumen
Vistas de plantilla      apps/<modulo>/views.py                         │ SOLO la fachada
   │                                                                   ─┘
Fachada / servicios      apps/<modulo>/facade.py, services.py, dto.py
   │
Dominio / datos          sample_data.py (prototipo) → modelos Django (producción)
```

Reglas de las capas:

- Las vistas no contienen reglas de negocio: llaman a la fachada y arman la respuesta.
- La fachada valida rol y estado antes de operar; los errores salen como excepciones/valores que la capa del API traduce a `403`/`409`/`422` con el contrato JSON.
- Los DTO son la única forma en que el dominio sale hacia el API o las plantillas.

## Gobernanza

Cambiar la arquitectura (módulos, patrones adoptados o descartados) es una decisión del equipo: se enmienda este documento por PR y se registra en el changelog del release correspondiente. El `Constitution Check` de cada `plan.md` debe citar este documento al evaluar el principio V.
