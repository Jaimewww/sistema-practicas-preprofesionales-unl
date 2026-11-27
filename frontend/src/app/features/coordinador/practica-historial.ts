import { Component, inject } from '@angular/core';
import { formatoFecha, ESTADO_PRACTICA } from '../../core/demo';
import { Tarjeta } from '../../shared/ui';
import { nombrePropio } from './coordinador.util';
import { PracticaActual } from './practica-actual';

/** C3 · Pestaña Historial: quién, qué y cuándo de cada cambio de estado (RF-10). */
@Component({
  selector: 'app-practica-historial',
  imports: [Tarjeta],
  template: `
    @let e = ctx.estado();
    @if (e.tipo === 'exito') {
      <app-tarjeta titulo="Historial de estados" sub="Quién, qué y cuándo (RF-10). El historial original nunca se edita; cada decisión agrega una entrada.">
        <div class="tabla-marco">
          <table class="tbl">
            <caption class="sr-only">Historial de estados</caption>
            <thead><tr><th scope="col">Cuándo</th><th scope="col">Quién</th><th scope="col">Qué</th><th scope="col">Motivo</th></tr></thead>
            <tbody>
              @for (h of e.datos.historial.slice().reverse(); track $index) {
                <tr>
                  <td>{{ formatoFecha(h.fecha) }}</td>
                  <td>{{ nombrePropio(h.autor) }}</td>
                  <td>
                    @if (h.estadoAnterior) { {{ estados[h.estadoAnterior] }} → }
                    <strong>{{ estados[h.estadoNuevo] }}</strong>
                  </td>
                  <td>{{ h.motivo || '—' }}</td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </app-tarjeta>
    }
  `,
  styleUrl: './pantalla.css',
})
export class PracticaHistorial {
  protected readonly ctx = inject(PracticaActual);
  protected readonly estados = ESTADO_PRACTICA;
  protected readonly formatoFecha = formatoFecha;
  protected readonly nombrePropio = nombrePropio;
}
