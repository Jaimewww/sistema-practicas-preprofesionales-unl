import { ApiError } from './api/envelope';
import type { EstadoUi } from './estado-ui';
import { aApiError } from './api/api-error.interceptor';

/** Qué debe hacer la interfaz además de mostrar el mensaje (ACD 6 §5). */
export type AccionDeError =
  | 'marcar_campos' // 400: marcar el campo y conservar lo escrito
  | 'ir_a_login' // 401
  | 'ocultar_accion' // 403
  | 'volver_al_selector' // 404
  | 'conservar_formulario' // 409 semana duplicada
  | 'deshabilitar_envio' // 409 práctica no en curso
  | 'reintentar' // 0 y 500
  | 'ninguna';

/**
 * Traduce un error del API a lo que ve la persona.
 *
 * Un mensaje por cada caso de la matriz ACD 6 §5. Nunca expone detalles internos del servidor.
 */
export function mensajeDeError(error: ApiError): string {
  if (error.status === 0 || error.code === 'sin_conexion') {
    return 'No hay conexión con el servidor.';
  }
  if (error.status === 400) {
    const mensajes = Object.values(error.campos).flat();
    return mensajes.length > 0 ? mensajes.join(' ') : 'Revisa los datos ingresados.';
  }
  if (error.status === 401) return 'Tu sesión terminó.';
  if (error.status === 403) return 'Solo un estudiante puede registrar horas.';
  if (error.status === 404) return 'No encontramos esa práctica.';
  if (error.status === 409) {
    if (error.code === 'semana_duplicada') return 'Ya enviaste esa semana.';
    if (error.code === 'practica_no_en_curso') return 'La práctica no está en curso.';
    return error.detail;
  }
  return 'Ocurrió un problema en el servidor. Inténtalo de nuevo.';
}

/** Acción que la interfaz debe tomar según el error. */
export function accionDeError(error: ApiError): AccionDeError {
  if (error.status === 0 || error.code === 'sin_conexion') return 'reintentar';
  if (error.status === 400) return 'marcar_campos';
  if (error.status === 401) return 'ir_a_login';
  if (error.status === 403) return 'ocultar_accion';
  if (error.status === 404) return 'volver_al_selector';
  if (error.status === 409) {
    if (error.code === 'semana_duplicada') return 'conservar_formulario';
    if (error.code === 'practica_no_en_curso') return 'deshabilitar_envio';
    return 'ninguna';
  }
  if (error.status >= 500) return 'reintentar';
  return 'ninguna';
}

/** Convierte cualquier excepción en el estado `error` de EstadoUi. */
export function estadoDeError<T>(e: unknown): EstadoUi<T> {
  const error = aApiError(e);
  return { tipo: 'error', error, mensaje: mensajeDeError(error) };
}
