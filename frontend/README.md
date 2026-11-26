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

| Archivo | Cuándo | `useMock` |
|---|---|---|
| `environment.ts` | `npm start`, `npm run build` | `true` |
| `environment.real.ts` | `npm run start:real` (`fileReplacements` en `angular.json`) | `false` |

Con el mock todo funciona sin backend ni login. Con la API real hace falta el
backend en `:8000`, CORS habilitado para `http://localhost:4200` y una sesión iniciada.

## Estructura

| Ruta (`src/app/`) | Qué es | Responsable |
|---|---|---|
| `core/api/envelope.ts` | Envelope del ADR 0012 y `ApiError` | compartido |
| `core/api/api-client.ts` | `ApiClient.get/post`: URL base y desenvuelve `data` | compartido |
| `core/api/api-error.interceptor.ts` | Toda respuesta no 2xx → `ApiError` | compartido |
| `core/auth/auth.interceptor.ts` | Agrega `Authorization: Bearer` | compartido (Jaime suma el refresh) |
| `core/estado-ui.ts` | `EstadoUi<T>`: inicial, cargando, éxito, vacío, error | compartido |
| `app.config.ts` | `provideHttpClient`, interceptores y elección mock / real | compartido |
| `core/auth/sesion.service.ts`, `features/auth/login/` | Sesión JWT y login | Jaime |
| `features/reportes/reportes.http.ts` | Servicio real de reportes | Alejandro |
| `features/reportes/registrar-reporte/`, `nuevo-reporte.ts` | Pantalla E4 y ruta `/reportes/nuevo` | Melissa |
| `core/errores.ts` | Mensajes por código HTTP y validación | Ivett |
| `features/practicas/practicas.http.ts`, `selector-practica/` | Selector de práctica | Doménica |

Regla: los componentes hacen `inject(ReportesApi)` / `inject(PracticasApi)` (clases
abstractas usadas como token), nunca inyectan `*Http` ni `*Mock`. `app.config.ts`
decide cuál se usa según `environment.useMock`.

## Escenarios del mock

| Entrada | Respuesta |
|---|---|
| práctica `1`, semana nueva, horas 1–40 | `201`, `requiere_revision: false` |
| horas mayores que 40 | `201`, `requiere_revision: true` |
| horas `0` o mayores que 168 | `400` en `horas_reportadas` |
| la misma semana dos veces | `409 semana_duplicada` |
| práctica `409` | `409 practica_no_en_curso` |
| práctica `404` | `404 no_encontrado` |

## Ramas

Cada integrante trabaja en `feat/ape006-<pieza>` desde `develop` y abre su propio PR.
