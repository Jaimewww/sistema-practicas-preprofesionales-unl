import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import type { Envelope } from './envelope';

/**
 * Cliente compartido sobre HttpClient: arma la URL con la base del environment
 * y desenvuelve `data` del envelope (ADR 0012).
 *
 * El Bearer lo agrega `authInterceptor` y los errores los convierte en `ApiError`
 * `apiErrorInterceptor`, así que los servicios (reportes, practicas, auth) solo
 * llaman a `get` / `post` y reciben datos ya tipados.
 */
@Injectable({ providedIn: 'root' })
export class ApiClient {
  private readonly http = inject(HttpClient);

  get<T>(ruta: string): Observable<T> {
    return this.http.get<Envelope<T>>(this.url(ruta)).pipe(map(desenvolver));
  }

  post<T>(ruta: string, cuerpo: unknown): Observable<T> {
    return this.http.post<Envelope<T>>(this.url(ruta), cuerpo).pipe(map(desenvolver));
  }

  private url(ruta: string): string {
    return `${environment.apiBaseUrl}${ruta}`;
  }
}

/** Las respuestas 204 llegan sin cuerpo: HttpClient entrega `null`. */
function desenvolver<T>(cuerpo: Envelope<T> | null): T {
  return (cuerpo?.data ?? undefined) as T;
}
