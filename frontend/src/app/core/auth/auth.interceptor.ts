import { inject } from '@angular/core';
import type { HttpInterceptorFn } from '@angular/common/http';
import { SesionService } from './sesion.service';

/** Adjunta `Authorization: Bearer <access>` si hay sesión. Jaime agrega aquí el refresh ante 401. */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = inject(SesionService).accessToken();
  return next(token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req);
};
