import { HttpErrorResponse, type HttpInterceptorFn } from '@angular/common/http';
import { catchError, throwError } from 'rxjs';
import { ApiError, esErrorDeDominio, type Envelope, type ErroresDeCampo } from './envelope';

/**
 * Convierte cualquier respuesta no 2xx en `ApiError {status, code, detail, campos}`.
 * Los componentes nunca ven `HttpErrorResponse`.
 */
export const apiErrorInterceptor: HttpInterceptorFn = (req, next) =>
  next(req).pipe(catchError((e: unknown) => throwError(() => aApiError(e))));

export function aApiError(e: unknown): ApiError {
  if (e instanceof ApiError) return e;
  if (!(e instanceof HttpErrorResponse)) {
    return new ApiError(500, 'error_interno', 'Ocurrió un error inesperado.');
  }
  // status 0: no hubo respuesta (red caída o CORS bloqueado por el navegador).
  if (e.status === 0) {
    return new ApiError(0, 'sin_conexion', 'No se pudo conectar con el servidor.');
  }
  const cuerpo = e.error as Partial<Envelope<unknown>> | null;
  const errors = cuerpo?.errors ?? null;
  if (esErrorDeDominio(errors)) {
    return new ApiError(e.status, errors.code, errors.detail);
  }
  return new ApiError(
    e.status,
    e.status === 400 ? 'validacion' : 'error_desconocido',
    cuerpo?.message || 'La solicitud no se pudo completar.',
    (errors as ErroresDeCampo | null) ?? {},
  );
}
