# Frontend (APE-006)

Angular 22 (componentes standalone, signals, `HttpClient` con interceptores).
Consume la feature **F-002** (registrar horas semanales):
`POST /api/v1/practicas/{practica_id}/reportes/`.

## Correr

```bash
cd frontend
npm install
npm start            # http://localhost:4200, datos simulados (mock)
npm run start:real   # API real en http://localhost:8000/api/v1
npm test             # Vitest: contratos, interceptores, mock y E4
npm run build        # también chequea tipos y plantillas
```

La configuración vive en `src/environments/`:

| Archivo               | Cuándo                                                      | `useMock` |
| --------------------- | ----------------------------------------------------------- | --------- |
| `environment.ts`      | `npm start`, `npm run build`                                | `true`    |
| `environment.real.ts` | `npm run start:real` (`fileReplacements` en `angular.json`) | `false`   |

Con el mock todo funciona sin backend ni login. Con la API real hace falta el
backend en `:8000`, CORS habilitado para `http://localhost:4200` y una sesión iniciada.

## Autenticación (F-003)

`core/auth/sesion.service.ts` habla con la API real:

| Acción                          | Endpoint                             | Qué guarda                        |
| ------------------------------- | ------------------------------------ | --------------------------------- |
| `iniciarSesion(usuario, clave)` | `POST /auth/token/`                  | el par `access` + `refresh`       |
| `cargarPerfil()`                | `GET /me/`                           | el perfil de la cuenta            |
| `refrescar()`                   | `POST /auth/token/refresh/`          | el par **nuevo**: el refresh rota |
| `cerrarSesion()`                | `POST /auth/logout/` con `{refresh}` | limpia la sesión local            |

`authInterceptor` agrega `Authorization: Bearer <access>` y, ante un 401, renueva
una sola vez con `refrescar()` y repite la petición con el token nuevo. Si el
refresh también falla, limpia la sesión y deja pasar el error; los endpoints de
token nunca se reintentan, así que no hay bucles. El login (`features/auth/login/`)
usa formulario reactivo y `EstadoUi`, muestra la cuenta atrás del 429 (leyendo los
segundos del `detail`, porque `ApiError` no expone cabeceras) y, después de
consultar `/me/`, abre el tablero del rol de la cuenta. `/login` vive fuera del
layout del tablero. En modo real, abrir un tablero sin sesión lleva a `/login`;
la API sigue siendo responsable de autorizar cada operación.

**Dónde viven los tokens:** solo en memoria, en los signals de `SesionService`.
Nunca `sessionStorage`/`localStorage`: un XSS no puede leer el refresh de un
almacenamiento persistente. El costo asumido es que **recargar la página pierde
la sesión** y hay que volver a entrar; con la pestaña abierta, la renovación
automática mantiene la sesión hasta el vencimiento del refresh (30 min).

## Estructura

| Ruta (`src/app/`)                                            | Qué es                                                    | Responsable        |
| ------------------------------------------------------------ | --------------------------------------------------------- | ------------------ |
| `core/api/envelope.ts`                                       | Envelope del ADR 0012 y `ApiError`                        | compartido         |
| `core/api/api-client.ts`                                     | `ApiClient.get/post`: URL base y desenvuelve `data`       | compartido         |
| `core/api/api-error.interceptor.ts`                          | Toda respuesta no 2xx → `ApiError`                        | compartido         |
| `core/auth/auth.interceptor.ts`                              | Agrega `Authorization: Bearer` y renueva una vez ante 401 | compartido (Jaime) |
| `core/estado-ui.ts`                                          | `EstadoUi<T>`: inicial, cargando, éxito, vacío, error     | compartido         |
| `app.config.ts`                                              | `provideHttpClient`, interceptores y elección mock / real | compartido         |
| `core/auth/sesion.service.ts`, `features/auth/login/`        | Sesión JWT y login                                        | Jaime              |
| `features/reportes/reportes.http.ts`                         | Servicio real de reportes                                 | Alejandro          |
| `features/reportes/registrar-reporte/`, `nuevo-reporte.ts`   | Pantalla E4 y ruta `/reportes/nuevo`                      | Melissa            |
| `core/errores.ts`                                            | Mensajes por código HTTP y validación                     | Ivett              |
| `features/practicas/practicas.http.ts`, `selector-practica/` | Selector de práctica                                      | Doménica           |

Regla: los componentes hacen `inject(ReportesApi)` / `inject(PracticasApi)` (clases
abstractas usadas como token), nunca inyectan `*Http` ni `*Mock`. `app.config.ts`
decide cuál se usa según `environment.useMock`.

Excepción: el plan (C-09) y el informe final (C-10) usan `PlanInformeHttp`, que no es un
token abstracto. `rutasEstudiante(false)` lo provee en `providers` de su entrada y el
componente real lo inyecta directamente; en modo demo la ruta monta la pantalla del
prototipo y no provee nada, así que no hay respaldo simulado sobre el API real.

## Escenarios del mock

| Entrada                                | Respuesta                         |
| -------------------------------------- | --------------------------------- |
| práctica `1`, semana nueva, horas 1–40 | `201`, `requiere_revision: false` |
| horas mayores que 40                   | `201`, `requiere_revision: true`  |
| horas `0` o mayores que 168            | `400` en `horas_reportadas`       |
| la misma semana dos veces              | `409 semana_duplicada`            |
| práctica `409`                         | `409 practica_no_en_curso`        |
| práctica `404`                         | `404 no_encontrado`               |

## Ramas

Cada integrante trabaja en `feat/ape006-<pieza>` desde `develop` y abre su propio PR.
