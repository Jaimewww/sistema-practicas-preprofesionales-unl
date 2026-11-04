# usuarios

Usuario personalizado (T012, [data-model.md](../../../specs/001-seguimiento-practicas/data-model.md),
RF-11): es el `AUTH_USER_MODEL` y debe existir antes de migraciones de usuarios.

## Modelo

`Usuario` extiende `AbstractUser`: conserva login por `username`, hash de
contraseña, sesiones y admin. Campos propios: `nombre` (obligatorio), `email`
(obligatorio y único), `rol` (obligatorio, seis slugs) y `carrera` (FK opcional
con `PROTECT`). `clean()` exige carrera en `coordinador`, `tutor_academico`,
`director` y `secretaria`; puede faltar en `estudiante` y `tutor_entidad`
(RF-11). El rol no otorga permisos ni staff.

## Creación y validación

`UsuarioManager` valida con `full_clean()` **antes** de escribir:
`create_user`, `create_superuser`, sus versiones async y `createsuperuser`
crean un usuario válido o fallan sin guardar (no hay rol por defecto).
`createsuperuser` exige `--nombre`, `--email` y `--rol`; la entrada antigua
(solo username, email y contraseña) se rechaza sin escribir, igual que un rol
inválido o uno que exige carrera sin indicarla (esos se crean desde el admin,
que incluye la carrera). `save()` directo no valida. La unicidad de `email`
también la impone la base de datos.

## Migraciones y bases existentes

`usuarios/0001_initial` depende de `auth.0012` y `carreras.0001`, crea una tabla
nueva y no usa `RunPython`.

> ⚠️ No ejecutes `migrate` contra una base existente (`backend/db.sqlite3` o
> una copia de desarrollo): su historial y usuarios son desconocidos y la
> migración de usuarios preexistentes no se verificó ni ejecutó. Solo se usó la
> base de pruebas en memoria de SQLite. PostgreSQL nuevo es el destino
> previsto, pero **no se ejecutó ninguna migración PostgreSQL**: pendiente.

Sin endpoints de autenticación, JWT/DRF, permisos ni login propio; la
separación JWT API / sesiones sigue siendo de tareas posteriores.
