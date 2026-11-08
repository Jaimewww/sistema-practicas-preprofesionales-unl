# 0004. Autorización con RBAC de Django y filtrado obligatorio por consulta

- **Estado**: Aceptada
- **Fecha**: 2026-10-11
- **Decisores**: equipo (fase 0 de la planificación)

## Contexto

RF-11 y la restricción de privacidad exigen que cada actor vea y haga solo lo que le corresponde; HU-07 (caso 3) exige rechazar el acceso de un tutor de entidad a una práctica ajena. Hoy el aislamiento lo emula `facade._visible` según el header `X-Rol`, que no autentica. Origen: [research.md, Tema 4](../../specs/001-seguimiento-practicas/research.md).

## Decisión

Usar el **RBAC nativo de Django** (usuarios, grupos y permisos) más **filtrado obligatorio por consulta**: cada usuario ve solo su información, el coordinador solo la de su carrera y el tutor de entidad solo a sus practicantes. En la capa DRF (#79) esto se expresa con clases de permiso por rol y por objeto, y los repositorios filtran siempre por usuario.

## Alternativas consideradas

- **Permisos por objeto con `django-guardian`**: reglas muy finas, pero agrega filas de permisos por objeto y una dependencia para un aislamiento ya expresable con consultas.
- **Filtrar solo en las vistas**: menos infraestructura, pero cualquier endpoint nuevo puede exponer datos de otra carrera; se descarta por riesgo de fuga.

## Consecuencias

- **Positivas**: una vista nueva no puede olvidar la regla; el rechazo `403`/`404` es comprobable por pruebas rol × acción (RNF-02).
- **Negativas o costos**: todo acceso a datos debe pasar por repositorios o consultas filtradas; exige disciplina en la revisión de PR.
- **Pendiente**: la autenticación real y los permisos por objeto llegan con #79 (ver [0011](0011-metodo-de-autenticacion-de-la-api.md)).

## Referencias

- [research.md, Tema 4](../../specs/001-seguimiento-practicas/research.md)
- [spec.md, matriz RF-11](../../specs/001-seguimiento-practicas/spec.md)
- [seguridad.md](../seguridad.md)
