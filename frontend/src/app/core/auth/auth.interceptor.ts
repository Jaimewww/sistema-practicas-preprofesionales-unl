import { inject } from '@angular/core';
import { HttpErrorResponse, type HttpInterceptorFn } from '@angular/common/http';
import { catchError, switchMap, throwError } from 'rxjs';
import { ApiError } from '../api/envelope';
import { SesionService } from './sesion.service';

/** Endpoints de tokens: renovarlos con el refresh nunca se reintenta (evita el bucle). */
const RUTAS_DE_TOKEN = ['/auth/token/', '/auth/token/refresh/'];

function esRutaDeToken(url: string): boolean {
  return RUTAS_DE_TOKEN.some((ruta) => url.includes(ruta));
}

/** 401 puede llegar ya como `ApiError` (interceptor de errores) o como respuesta HTTP. */
function esNoAutorizado(error: unknown): boolean {
  if (error instanceof ApiError) return error.status === 401;
  return error instanceof HttpErrorResponse && error.status === 401;
}

/**
 * Adjunta `Authorization: Bearer <access>` si hay sesión (S9) y, ante un 401,
 * renueva una sola vez con `SesionService.refrescar()` y repite la petición con
 * el token nuevo. Si el refresh también falla, limpia la sesión y deja pasar el
 * error. Los endpoints de token quedan fuera del reintento: un refresh vencido
 * no puede disparar otro refresh.
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const sesion = inject(SesionService);
  const token = sesion.accessToken();
  const conBearer = token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;

  return next(conBearer).pipe(
    catchError((error: unknown) => {
      if (!esNoAutorizado(error) || !sesion.autenticado() || esRutaDeToken(req.url)) {
        return throwError(() => error);
      }
      return sesion.refrescar().pipe(
        switchMap(() => {
          const nuevo = sesion.accessToken();
          return next(
            nuevo ? req.clone({ setHeaders: { Authorization: `Bearer ${nuevo}` } }) : req,
          );
        }),
        catchError((errorRefresco: unknown) => {
          sesion.limpiarSesion();
          return throwError(() => errorRefresco);
        }),
      );
    }),
  );
};
