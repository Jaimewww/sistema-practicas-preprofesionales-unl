# 0010. Adoptar Django REST Framework y PostgreSQL

- **Estado**: Aceptada (confirmada al mergear #98)
- **Fecha**: 2026-11-03
- **Decisores**: Jaime (#76, responsable de la implementación) y Alejandro (revisión); confirmada al mergear #98
- **Reemplaza a**: [0009](0009-api-del-prototipo-sin-drf-ni-base-de-datos.md)

## Contexto

El prototipo sirve datos sintéticos desde `sample_data.py` y guarda el estado en la sesión y en cookies firmadas ([0009](0009-api-del-prototipo-sin-drf-ni-base-de-datos.md)). Eso no alcanza para la sumativa 1, que pide persistencia real, validación de entrada, permisos, un contrato uniforme y OpenAPI. Además [0002](0002-postgresql-como-motor-de-base-de-datos.md) ya fijó PostgreSQL como motor, pero `backend/config/settings.py` sigue en SQLite. El equipo abrió #76 a #80 para cerrar esa brecha.

## Decisión

1. Pasar el dominio a **modelos Django con migraciones** sobre **PostgreSQL**, configurado con las variables `POSTGRES_*` del contrato compartido.
2. Adoptar **Django REST Framework** para el API de `/api/v1/` (serializers, vistas, permisos, renderer y exception handler) y **drf-spectacular** para OpenAPI.
3. Estructurar el backend por capas `api/`, `application/`, `domain/` e `infrastructure/`.
4. Cargar los datos de demo con un comando `seed`, no desde la API; ningún endpoint lee `sample_data.py`.

Esto reemplaza la decisión «sin DRF y sin base de datos» de [docs/api.md](../api.md), el descarte de DRF en [docs/arquitectura.md §3](../arquitectura.md) y la nota de [plan.md](../../specs/001-seguimiento-practicas/plan.md). La decisión del frontend con plantillas se mantiene para las pantallas del prototipo.

## Alternativas consideradas

- **Seguir con `JsonResponse` y datos en memoria**: no da persistencia compartida, validación declarativa, permisos por objeto ni OpenAPI.
- **Django Ninja o FastAPI**: reducen código, pero rompen la continuidad con Django ([0001](0001-backend-con-django.md)) y con el ecosistema (`django-simple-history`, admin, RBAC).
- **Mantener SQLite**: ya descartada en 0002 por no reproducir el comportamiento del entorno real.

## Consecuencias

- **Positivas**: contrato verificable (serializers y OpenAPI), pruebas contra la misma base que producción, base para auth y permisos reales ([0011](0011-metodo-de-autenticacion-de-la-api.md)).
- **Negativas o costos**: migrar fachada, DTO y pruebas existentes; dos dependencias nuevas (`djangorestframework`, `drf-spectacular`); la suite actual de `unittest` debe seguir verde durante la migración.
- **Pendiente**: hecho. `docs/api.md` documenta la API real de DRF (§2, §4, §5 y §10) y este ADR pasó a Aceptada al mergear #98. `docs/arquitectura.md` y `plan.md` son documentos históricos: la nota de revisión de `plan.md` registra el giro a DRF + PostgreSQL + JWT.

## Referencias

- Issues #76, #77, #78, #79, #80
- [0002](0002-postgresql-como-motor-de-base-de-datos.md), [0009](0009-api-del-prototipo-sin-drf-ni-base-de-datos.md), [0012](0012-contrato-universal-de-respuesta.md)
- [docs/arquitectura/c4-codigo.puml](../arquitectura/c4-codigo.puml)
