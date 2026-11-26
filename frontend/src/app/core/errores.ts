import { ApiError } from './api/envelope';
import type { EstadoUi } from './estado-ui';
import { aApiError } from './api/api-error.interceptor';

/**
 * Traduce un error del API a lo que ve la persona.     RESPONSABLE: Ivett
 *
 * Pendiente: un mensaje y una acción por cada caso de la matriz ACD 6 §5
 * (400 por campo, 401 -> login, 403 ocultar acción, 404, 409 conservar formulario,
 * 0 sin conexión / CORS, 500 genérico). Por ahora devuelve el `detail` del servidor.
 */
export function mensajeDeError(error: ApiError): string {
  return error.detail;
}

/** Convierte cualquier excepción en el estado `error` de EstadoUi. */
export function estadoDeError<T>(e: unknown): EstadoUi<T> {
  const error = aApiError(e);
  return { tipo: 'error', error, mensaje: mensajeDeError(error) };
}
