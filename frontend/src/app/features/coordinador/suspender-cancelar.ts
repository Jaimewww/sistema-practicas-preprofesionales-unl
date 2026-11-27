import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { map } from 'rxjs';
import { Aviso, Insignia, Tarjeta } from '../../shared/ui';
import { estadoDeError } from '../../core/errores';
import type { EstadoPractica } from '../../core/demo';
import { CoordinadorApi } from './coordinador.api';
import type { DetallePractica } from './coordinador.model';
import { componente, estadoDemo, estadoPorPractica, nombrePropio, paramsPractica, textoEstado, tipoEstado } from './coordinador.util';
import { EstadoPantalla } from './ui/estado-pantalla';

type Accion = 'suspender' | 'cancelar';

/** Estado desde el que se aplica cada decisión, el que queda y el texto del botón. */
const DECISION: Record<Accion, { desde: EstadoPractica; hacia: EstadoPractica; boton: string; nombre: string; solo: string }> = {
  suspender: { desde: 'en_curso', hacia: 'suspendida', boton: 'Suspender práctica', nombre: 'Suspendida', solo: 'solo se suspende una práctica en curso.' },
  cancelar: { desde: 'suspendida', hacia: 'cancelada', boton: 'Cancelar práctica', nombre: 'Cancelada', solo: 'solo se cancela una práctica suspendida.' },
};
export const MAXIMO_MOTIVO = 500;
export const ERROR_MOTIVO = 'Escriba el motivo de la decisión.';

/** C5 · Suspender o cancelar una práctica con motivo obligatorio (RF-13). */
@Component({
  selector: 'app-suspender-cancelar',
  imports: [RouterLink, Aviso, Insignia, Tarjeta, EstadoPantalla],
  templateUrl: './suspender-cancelar.html',
  styleUrls: ['./pantalla.css'],
})
export class SuspenderCancelar {
  private readonly api = inject(CoordinadorApi);
  private readonly ruta = inject(ActivatedRoute);
  protected readonly estado = estadoPorPractica((id) => this.api.practica(id));
  private readonly consulta = toSignal(this.ruta.queryParamMap.pipe(map((q) => ({ accion: q.get('accion'), estado: q.get('estado') }))), { initialValue: { accion: this.ruta.snapshot.queryParamMap.get('accion'), estado: this.ruta.snapshot.queryParamMap.get('estado') } });

  /** `null` mientras no se haya elegido: sale de `?accion=` o del estado de la práctica. */
  private readonly elegida = signal<Accion | null>(null);
  protected readonly motivo = signal('');
  protected readonly errorMotivo = signal(false);
  protected readonly errorApi = signal('');
  protected readonly hecho = signal<DetallePractica | null>(null);

  protected readonly accion = computed<Accion>(() => {
    const e = this.estado();
    const q = this.consulta().accion;
    const real = e.tipo === 'exito' ? this.vigente(e.datos) : null;
    return this.elegida() ?? (q === 'suspender' || q === 'cancelar' ? q : real === 'suspendida' ? 'cancelar' : 'suspender');
  });

  protected readonly decision = DECISION;
  protected readonly maximo = MAXIMO_MOTIVO;
  protected readonly errorTexto = ERROR_MOTIVO;
  protected readonly componente = componente;
  protected readonly nombrePropio = nombrePropio;
  protected readonly paramsPractica = paramsPractica;
  protected readonly tipoEstado = tipoEstado;
  protected readonly textoEstado = textoEstado;

  /** Estado vigente: el de la demostración (`?estado=`) o el real. */
  protected vigente(d: DetallePractica): EstadoPractica {
    return estadoDemo(this.consulta().estado, d.practica.estado);
  }

  protected aplicable(d: DetallePractica): boolean {
    return this.vigente(d) === DECISION[this.accion()].desde;
  }

  protected elegirAccion(evento: Event): void {
    this.elegida.set((evento.target as HTMLSelectElement).value as Accion);
    this.errorMotivo.set(false);
  }

  protected escribir(evento: Event): void {
    const texto = (evento.target as HTMLTextAreaElement).value;
    this.motivo.set(texto);
    if (texto.trim()) this.errorMotivo.set(false);
  }

  protected enviar(d: DetallePractica): void {
    if (!this.aplicable(d)) return;
    if (!this.motivo().trim()) {
      this.errorMotivo.set(true);
      return;
    }
    this.errorApi.set('');
    const pedir = this.accion() === 'suspender' ? this.api.suspender(d.practica.id, this.motivo().trim()) : this.api.cancelar(d.practica.id, this.motivo().trim());
    pedir.subscribe({
      next: (hecho) => this.hecho.set(hecho),
      error: (e: unknown) => {
        const r = estadoDeError<void>(e);
        this.errorApi.set(r.tipo === 'error' ? r.mensaje : 'No se pudo aplicar la decisión.');
      },
    });
  }
}
