import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Aviso, Insignia, Tarjeta } from '../../shared/ui';
import { estadoDeError } from '../../core/errores';
import { etiquetaEstadoPractica } from '../../core/demo';
import { CoordinadorApi } from './coordinador.api';
import type { DetallePractica } from './coordinador.model';
import { componente, estadoPorPractica, nombrePropio, paramsPractica, tipoEstado } from './coordinador.util';
import { type CasoCierre, datosDeCierre, MINIMO_EVALUACION, requisitos } from './cierre.util';
import { EstadoPantalla } from './ui/estado-pantalla';

/** C4 · Cerrar práctica: requisitos de RF-09; «Cerrar» queda deshabilitado mientras falte alguno. */
@Component({
  selector: 'app-cerrar-practica',
  imports: [RouterLink, Aviso, Insignia, Tarjeta, EstadoPantalla],
  templateUrl: './cerrar-practica.html',
  styleUrls: ['./pantalla.css', './cerrar-practica.css'],
})
export class CerrarPractica {
  private readonly api = inject(CoordinadorApi);
  protected readonly estado = estadoPorPractica((id) => this.api.practica(id));
  protected readonly caso = signal<CasoCierre>('real');
  protected readonly confirmado = signal(false);
  protected readonly errorConfirmar = signal(false);
  protected readonly errorApi = signal('');
  /** La práctica ya cerrada en esta pantalla, con lo que devolvió el cierre. */
  protected readonly cerrada = signal<DetallePractica | null>(null);

  protected readonly componente = componente;
  protected readonly nombrePropio = nombrePropio;
  protected readonly paramsPractica = paramsPractica;
  protected readonly tipoEstado = tipoEstado;
  protected readonly etiqueta = etiquetaEstadoPractica;
  protected readonly minimo = MINIMO_EVALUACION;
  protected readonly requisitos = (d: DetallePractica) => requisitos(d.practica, datosDeCierre(d.practica, this.caso()));
  protected readonly datos = (d: DetallePractica) => datosDeCierre(d.practica, this.caso());
  protected readonly faltantes = (d: DetallePractica) => this.requisitos(d).filter((r) => !r.cumplido);

  protected elegirCaso(evento: Event): void {
    this.caso.set((evento.target as HTMLSelectElement).value as CasoCierre);
    this.confirmado.set(false);
    this.errorConfirmar.set(false);
    this.cerrada.set(null);
  }

  protected confirmar(evento: Event): void {
    this.confirmado.set((evento.target as HTMLInputElement).checked);
    this.errorConfirmar.set(false);
  }

  protected cerrar(d: DetallePractica): void {
    if (this.faltantes(d).length) return;
    if (!this.confirmado()) {
      this.errorConfirmar.set(true);
      return;
    }
    this.errorApi.set('');
    this.api.cerrar(d.practica.id, this.datos(d).evaluacion ?? 0).subscribe({
      next: (cerrada) => this.cerrada.set(cerrada),
      error: (e: unknown) => {
        const r = estadoDeError<void>(e);
        this.errorApi.set(r.tipo === 'error' ? r.mensaje : 'No se pudo cerrar la práctica.');
      },
    });
  }
}
