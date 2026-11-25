# Frontend (APE-006)

Astro 7 con islas React. Consume la feature **F-002** (registrar horas semanales):
`POST /api/v1/practicas/{practica_id}/reportes/`.

## Correr

```bash
cd frontend
npm install
npm run dev        # http://localhost:4321
npm run check      # tipos
npm run build
```

Variables (opcionales, en un `.env` que no se versiona):

| Variable | Por defecto | Uso |
|---|---|---|
| `PUBLIC_API_BASE_URL` | `http://localhost:8000/api/v1` | URL base del backend |
| `PUBLIC_USE_MOCK` | `true` | `false` para usar la API real |

Con `PUBLIC_USE_MOCK=true` (por defecto) todo funciona sin backend ni login.
Con `false` usa la API real: el backend en `:8000`, CORS habilitado para
`http://localhost:4321` y una sesión iniciada.

## Estructura

| Ruta | Qué es | Responsable |
|---|---|---|
| `src/lib/api/envelope.ts` | Envelope del ADR 0012 y `ApiError` | compartido |
| `src/lib/api/http.ts` | `pedir()`: URL base, Bearer, desenvuelve `data`, lanza `ApiError` | compartido |
| `src/lib/api/config.ts` | `PUBLIC_API_BASE_URL`, `PUBLIC_USE_MOCK` | compartido |
| `src/lib/estado-ui.ts` | `EstadoUi<T>`: inicial, cargando, éxito, vacío, error | compartido |
| `src/lib/auth/sesion.ts`, `components/LoginForm.tsx` | Sesión JWT y login | Jaime |
| `src/lib/reportes/reportes.http.ts` | Servicio real de reportes | Alejandro |
| `src/components/RegistrarReporte.tsx` | Pantalla E4 | Melissa |
| `src/lib/errores.ts` | Mensajes por código HTTP y validación | Ivett |
| `src/lib/practicas/practicas.http.ts`, `components/SelectorPractica.tsx` | Selector de práctica | Doménica |

Regla: los componentes importan `reportesApi` / `practicasApi` desde `src/lib/*/index.ts`,
nunca la clase `*Http` o `*Mock`. Así el cambio de mock a API real es una variable de entorno.

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
