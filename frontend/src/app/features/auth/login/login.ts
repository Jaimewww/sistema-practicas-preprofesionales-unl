import { Component, DestroyRef, computed, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { aApiError } from '../../../core/api/api-error.interceptor';
import type { ApiError } from '../../../core/api/envelope';
import { SesionService } from '../../../core/auth/sesion.service';
import { cargando, exito, inicial, type EstadoUi } from '../../../core/estado-ui';

/** El 429 del backend trae la espera en el `detail`: «… en 45 segundos.» */
const SEGUNDOS_EN_DETALLE = /en (\d+) segundos?/i;
/** Sin número en el `detail` se espera la ventana del scope `auth` (5/min). */
const SEGUNDOS_SIN_DETALLE = 60;

/** Espera del 429 en segundos: el `detail` la repite desde la cabecera Retry-After. */
function segundosDeEspera(error: ApiError): number {
  const encontrado = SEGUNDOS_EN_DETALLE.exec(error.detail);
  return encontrado ? Math.max(1, Number(encontrado[1])) : SEGUNDOS_SIN_DETALLE;
}

/** Texto que ve la persona para los casos que no son del formulario. */
function mensajeDeAcceso(error: ApiError): string {
  if (error.status === 0) {
    // El navegador entrega status 0 cuando la API no responde o CORS bloquea la
    // respuesta: se explica el origen y no se culpa a la contraseña.
    return (
      'No se pudo conectar con el servidor. Revisa tu conexión y que la API ' +
      'permita el origen http://localhost:4200 (CORS).'
    );
  }
  if (error.status === 401) return 'Usuario o contraseña incorrectos.';
  return error.detail;
}

/**
 * Formulario de inicio de sesión (F-003).     RESPONSABLE: Jaime
 *
 * Reactive forms + EstadoUi; 429 con cuenta atrás desde `Retry-After` (el backend
 * la repite en el `detail`), 401/400 con el mensaje del formulario, status 0
 * explicando conexión/CORS. Con éxito navega a `/reportes/nuevo`.
 *
 * Visual: artboard `02-panel-marca` aprobado (panel de marca partido). El logo
 * UNL va embebido como data URI dentro de este componente, nunca en `public/`:
 * así cada integrante puede usar el suyo sin tocar un asset compartido.
 */
@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule],
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class Login {
  private readonly sesion = inject(SesionService);
  private readonly router = inject(Router);

  readonly estado = signal<EstadoUi<null>>(inicial());
  readonly espera = signal(0);
  readonly verClave = signal(false);

  readonly form = inject(NonNullableFormBuilder).group({
    usuario: ['', Validators.required],
    clave: ['', Validators.required],
  });

  readonly error = computed(() => {
    const estado = this.estado();
    return estado.tipo === 'error' ? estado : null;
  });
  readonly esLimite = computed(() => this.error()?.error.status === 429);
  readonly erroresCampos = computed(() => this.error()?.error.campos ?? {});
  readonly enviando = computed(() => this.estado().tipo === 'cargando');
  /** Mientras corre la cuenta atrás del 429 no se puede reintentar. */
  readonly bloqueado = computed(() => this.enviando() || this.espera() > 0);

  private cuenta: ReturnType<typeof setInterval> | null = null;

  constructor() {
    inject(DestroyRef).onDestroy(() => this.detenerCuenta());
  }

  alternarClave(): void {
    this.verClave.update((visible) => !visible);
  }

  enviar(): void {
    if (this.bloqueado()) return;
    this.form.markAllAsTouched();
    if (this.form.invalid) return;

    this.estado.set(cargando());
    const { usuario, clave } = this.form.getRawValue();
    this.sesion.iniciarSesion(usuario.trim(), clave).subscribe({
      next: () => {
        this.estado.set(exito(null));
        void this.router.navigate(['/reportes/nuevo']);
      },
      error: (e: unknown) => this.manejarError(e),
    });
  }

  private manejarError(e: unknown): void {
    const error = aApiError(e);
    if (error.status === 429) {
      const segundos = segundosDeEspera(error);
      this.estado.set({ tipo: 'error', error, mensaje: 'Demasiados intentos.' });
      this.iniciarCuenta(segundos);
      return;
    }
    this.estado.set({ tipo: 'error', error, mensaje: mensajeDeAcceso(error) });
  }

  private iniciarCuenta(segundos: number): void {
    this.detenerCuenta();
    this.espera.set(segundos);
    this.cuenta = setInterval(() => {
      const restante = this.espera() - 1;
      this.espera.set(Math.max(0, restante));
      if (restante > 0) return;
      this.detenerCuenta();
      // Al llegar a cero el botón vuelve a habilitarse y el aviso desaparece.
      if (this.estado().tipo === 'error') this.estado.set(inicial());
    }, 1000);
  }

  private detenerCuenta(): void {
    if (this.cuenta === null) return;
    clearInterval(this.cuenta);
    this.cuenta = null;
  }
}
