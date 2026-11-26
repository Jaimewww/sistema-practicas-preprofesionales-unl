import { Injectable, computed, signal } from '@angular/core';
import { Observable, throwError } from 'rxjs';

/**
 * Sesión JWT del frontend.            RESPONSABLE: Jaime (F-003)
 *
 * Endpoints: POST /auth/token/ -> data {access, refresh};
 *            POST /auth/token/refresh/ -> nuevo par (el refresh rota);
 *            POST /auth/logout/ con {refresh} y el access vigente.
 *
 * El esqueleto solo deja lo que usa `authInterceptor` (accessToken). Jaime
 * implementa iniciarSesion, refrescar y cerrarSesion con ApiClient y decide
 * dónde guardar los tokens.
 */
@Injectable({ providedIn: 'root' })
export class SesionService {
  private readonly access = signal<string | null>(null);

  readonly accessToken = this.access.asReadonly();
  readonly autenticado = computed(() => this.access() !== null);

  guardarTokens(access: string | null): void {
    this.access.set(access);
  }

  iniciarSesion(_usuario: string, _clave: string): Observable<void> {
    return throwError(() => new Error('Pendiente (Jaime): POST /auth/token/ y guardar el par de tokens.'));
  }

  refrescar(): Observable<void> {
    return throwError(() => new Error('Pendiente (Jaime): POST /auth/token/refresh/ y guardar el nuevo par.'));
  }

  cerrarSesion(): Observable<void> {
    return throwError(() => new Error('Pendiente (Jaime): POST /auth/logout/ y limpiar la sesión.'));
  }
}
