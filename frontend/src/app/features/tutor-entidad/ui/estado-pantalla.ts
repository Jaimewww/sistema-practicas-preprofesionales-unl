import { Component, computed, input } from '@angular/core';
import type { EstadoUi } from '../../../core/estado-ui';
import { Aviso, Vacio } from '../../../shared/ui';

/** Pinta los estados que no son «éxito» de una carga: cargando, vacío y error (con su mensaje). */
@Component({
  selector: 'app-te-estado-pantalla',
  imports: [Aviso, Vacio],
  template: `
    @switch (estado().tipo) {
      @case ('cargando') {
        <p class="cargando" role="status">Cargando…</p>
      }
      @case ('vacio') {
        <app-vacio [titulo]="vacioTitulo()" [texto]="vacioTexto()" />
      }
      @case ('error') {
        <app-aviso tipo="bad">{{ mensaje() }}</app-aviso>
      }
    }
  `,
  styles: `
    :host {
      display: block;
    }
    .cargando {
      margin: 0;
      padding: var(--espacio-5);
      text-align: center;
      color: var(--color-texto-suave);
    }
  `,
})
export class EstadoPantalla {
  readonly estado = input.required<EstadoUi<unknown>>();
  readonly vacioTitulo = input('Sin datos');
  readonly vacioTexto = input('');
  protected readonly mensaje = computed(() => {
    const e = this.estado();
    return e.tipo === 'error' ? e.mensaje : '';
  });
}
