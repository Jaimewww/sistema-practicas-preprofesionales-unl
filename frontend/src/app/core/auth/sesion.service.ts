import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, catchError, finalize, map, of, shareReplay, tap, throwError } from 'rxjs';
import { ApiClient } from '../api/api-client';
import { ApiError } from '../api/envelope';

/** Par de tokens que devuelve la API: el login y el refresh rotado mandan los dos. */
interface Tokens {
  access: string;
  refresh: string;
}

/**
 * Sesión JWT del frontend (F-003).          RESPONSABLE: Jaime
 *
 * Endpoints: POST /auth/token/ -> data {access, refresh};
 *            POST /auth/token/refresh/ -> nuevo par (el refresh rota);
 *            POST /auth/logout/ con {refresh} y el access vigente.
 *
 * Almacenamiento elegido: **solo memoria** (signals), nunca sessionStorage ni
 * localStorage. Así el refresh token no queda legible por JavaScript ni sobrevive
 * a un XSS en disco; el costo es que recargar la página pierde la sesión y hay que
 * volver a entrar (los tokens duran 15/30 min: la sesión de una pestaña abierta
 * sobrevive, la de una recarga no). Si más adelante se prefiere persistir, el
 * único punto a cambiar es `guardarPar` / `limpiarSesion`.
 */
@Injectable({ providedIn: 'root' })
export class SesionService {
  private readonly api = inject(ApiClient);

  private readonly access = signal<string | null>(null);
  private readonly refresh = signal<string | null>(null);

  readonly accessToken = this.access.asReadonly();
  readonly autenticado = computed(() => this.access() !== null);

  /** Renovación compartida: el refresh rota y dos en paralelo se invalidarían. */
  private refrescoEnCurso: Observable<void> | null = null;

  /**
   * Tokens vigentes. Se conserva el nombre que ya usaba `authInterceptor`;
   * `null` además limpia el refresh para no dejar media sesión.
   */
  guardarTokens(access: string | null): void {
    this.access.set(access);
    if (access === null) {
      this.refresh.set(null);
    }
  }

  /** POST /auth/token/: credenciales -> par de tokens (S4). */
  iniciarSesion(usuario: string, clave: string): Observable<void> {
    return this.api.post<Tokens>('/auth/token/', { username: usuario, password: clave }).pipe(
      tap((tokens) => this.guardarPar(tokens)),
      map(() => undefined),
    );
  }

  /**
   * POST /auth/token/refresh/ (S5). El refresh rota: se guarda el par nuevo o la
   * siguiente renovación fallaría. Si falla, la sesión ya no sirve y se limpia.
   */
  refrescar(): Observable<void> {
    if (this.refresh() === null) {
      return throwError(() => new ApiError(401, 'no_autenticado', 'La sesión no está iniciada.'));
    }
    this.refrescoEnCurso ??= this.api
      .post<Tokens>('/auth/token/refresh/', { refresh: this.refresh() })
      .pipe(
        tap((tokens) => this.guardarPar(tokens)),
        map(() => undefined),
        catchError((error: unknown) => {
          this.limpiarSesion();
          return throwError(() => error);
        }),
        finalize(() => {
          this.refrescoEnCurso = null;
        }),
        shareReplay({ bufferSize: 1, refCount: false }),
      );
    return this.refrescoEnCurso;
  }

  /**
   * POST /auth/logout/ con {refresh} (el access lo agrega `authInterceptor`) y
   * después limpia (S6). El cierre local no depende del servidor: si el logout
   * falla por red, la sesión de esta pestaña se limpia igual.
   */
  cerrarSesion(): Observable<void> {
    const refresh = this.refresh();
    const peticion: Observable<unknown> =
      refresh === null ? of(undefined) : this.api.post<void>('/auth/logout/', { refresh });
    return peticion.pipe(
      catchError(() => of(undefined)),
      map(() => undefined),
      finalize(() => this.limpiarSesion()),
    );
  }

  /** Borra el par en memoria (logout, refresh vencido o revocado). */
  limpiarSesion(): void {
    this.access.set(null);
    this.refresh.set(null);
  }

  private guardarPar({ access, refresh }: Tokens): void {
    this.access.set(access);
    this.refresh.set(refresh);
  }
}
