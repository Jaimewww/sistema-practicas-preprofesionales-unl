import { obtenerAccessToken } from '../auth/sesion';
import { API_BASE_URL } from './config';
import { ApiError, esErrorDeDominio, type Envelope, type ErroresDeCampo } from './envelope';

/**
 * Cliente HTTP compartido: arma la URL, adjunta el Bearer si hay sesión,
 * desenvuelve `data` y convierte cualquier respuesta no 2xx en `ApiError`.
 *
 * Los servicios (reportes, practicas, auth) solo llaman a `pedir`.
 */
export async function pedir<T>(ruta: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set('Accept', 'application/json');
  if (init.body !== undefined) headers.set('Content-Type', 'application/json');

  const token = obtenerAccessToken();
  if (token) headers.set('Authorization', `Bearer ${token}`);

  let respuesta: Response;
  try {
    respuesta = await fetch(`${API_BASE_URL}${ruta}`, { ...init, headers });
  } catch {
    // fetch solo rechaza sin respuesta: red caída o CORS bloqueado por el navegador.
    throw new ApiError(0, 'sin_conexion', 'No se pudo conectar con el servidor.');
  }

  if (respuesta.status === 204) return undefined as T;

  const cuerpo = (await respuesta.json().catch(() => null)) as Envelope<T> | null;

  if (!respuesta.ok || !cuerpo?.success) {
    const errors = cuerpo?.errors ?? null;
    if (esErrorDeDominio(errors)) {
      throw new ApiError(respuesta.status, errors.code, errors.detail);
    }
    throw new ApiError(
      respuesta.status,
      respuesta.status === 400 ? 'validacion' : 'error_desconocido',
      cuerpo?.message || 'La solicitud no se pudo completar.',
      (errors as ErroresDeCampo | null) ?? {},
    );
  }

  return cuerpo.data;
}
