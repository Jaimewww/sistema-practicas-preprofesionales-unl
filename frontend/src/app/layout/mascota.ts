import { Component, DestroyRef, booleanAttribute, computed, inject, input, signal } from '@angular/core';

export type Accion = 'ninguna' | 'saludar' | 'saltar' | 'balancear';

/** Duración (ms) de cada acción; debe coincidir con las animaciones de mascota.css. */
const DURACION: Record<Exclude<Accion, 'ninguna'>, number> = { saludar: 1800, saltar: 700, balancear: 1600 };
const CICLO: readonly Exclude<Accion, 'ninguna'>[] = ['saludar', 'saltar', 'balancear'];
const RETARDO_INICIAL = 1500;
const INTERVALO = 7000;
const DURACION_GLOBO = 3500;

/**
 * Oso de la UNL: cuerpo y brazo son dos capas; el brazo saluda girando sobre el hombro.
 * Respeta `prefers-reduced-motion`: sin animaciones ni temporizadores, solo el globo al hacer clic.
 */
@Component({
  selector: 'app-mascota',
  templateUrl: './mascota.html',
  styleUrl: './mascota.css',
})
export class Mascota {
  /** Nombre de pila para el saludo del globo (opcional). */
  readonly nombre = input<string | undefined>();

  /** Silencioso: solo hace el movimiento (saludar, saltar, balancear), sin globo de texto. */
  readonly callado = input(false, { transform: booleanAttribute });

  readonly accion = signal<Accion>('ninguna');
  readonly mensaje = signal<string | null>(null);

  private readonly mensajes = computed(() => {
    const nombre = this.nombre()?.trim();
    return [nombre ? `¡Hola, ${nombre}!` : '¡Hola!', '¡Bienvenido al SIAAF!', '¡Qué gusto verte!'];
  });

  private readonly reducido: boolean;
  private readonly temporizadores = new Set<ReturnType<typeof setTimeout>>();
  private intervalo: ReturnType<typeof setInterval> | undefined;
  private timerGlobo: ReturnType<typeof setTimeout> | undefined;
  private siguiente = 0;
  private indiceMensaje = 0;

  constructor() {
    this.reducido = typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!this.reducido) {
      this.programar(() => {
        this.cicloAutomatico();
        this.intervalo = setInterval(() => this.cicloAutomatico(), INTERVALO);
      }, RETARDO_INICIAL);
    }
    inject(DestroyRef).onDestroy(() => {
      this.temporizadores.forEach((t) => clearTimeout(t));
      this.temporizadores.clear();
      clearInterval(this.intervalo);
      clearTimeout(this.timerGlobo);
    });
  }

  /** Hover o foco de teclado: salta y saluda justo después. */
  alEntrar(): void {
    this.ejecutar('saltar', 'saludar');
  }

  alPulsar(): void {
    this.ejecutar('saludar');
    if (this.callado()) return;

    const mensajes = this.mensajes();
    this.mensaje.set(mensajes[this.indiceMensaje % mensajes.length]);
    this.indiceMensaje++;
    clearTimeout(this.timerGlobo);
    this.timerGlobo = setTimeout(() => this.mensaje.set(null), DURACION_GLOBO);
  }

  private cicloAutomatico(): void {
    if (this.accion() !== 'ninguna') return;
    const accion = CICLO[this.siguiente % CICLO.length];
    this.siguiente++;
    this.ejecutar(accion);
  }

  private ejecutar(accion: Exclude<Accion, 'ninguna'>, luego?: Exclude<Accion, 'ninguna'>): void {
    if (this.reducido || this.accion() !== 'ninguna') return;
    this.accion.set(accion);
    this.programar(() => {
      this.accion.set('ninguna');
      if (luego) this.ejecutar(luego);
    }, DURACION[accion]);
  }

  private programar(fn: () => void, ms: number): void {
    const t = setTimeout(() => {
      this.temporizadores.delete(t);
      fn();
    }, ms);
    this.temporizadores.add(t);
  }
}
