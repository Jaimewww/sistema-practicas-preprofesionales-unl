import { Component, inject } from '@angular/core';
import { ESTADO_PRACTICA, formatoFecha, RESULTADO_PRACTICA } from '../../core/demo';
import type { EntradaHistorial, EstadoPractica, Practica } from '../../core/demo';
import { Aviso, Pasos, Tarjeta, type PasoItem } from '../../shared/ui';
import { DirectorApi } from './director.api';
import { estadoPorCierre } from './director.util';
import { EstadoPantalla } from './ui/estado-pantalla';

/** D2 · Historial del cierre: quién, qué y cuándo, en solo lectura, con la línea de seguimiento. */
@Component({
  selector: 'app-cierre-historial',
  imports: [Tarjeta, Aviso, Pasos, EstadoPantalla],
  template: `
    @let e = estado();
    @if (e.tipo === 'exito') {
      @let p = e.datos;
      <div class="grilla">
        <app-tarjeta [titulo]="'Historial de ' + p.estudiante" [span]="12">
          <app-aviso tipo="info">Solo lectura: cada cambio conserva el estado anterior y el nuevo, quién lo hizo y cuándo (RF-10). El director únicamente consulta.</app-aviso>
          <div class="tabla-marco">
            <table class="tbl">
              <caption class="sr-only">Cambios de estado de la práctica</caption>
              <thead>
                <tr><th scope="col">Estado anterior</th><th scope="col">Estado nuevo</th><th scope="col">Quién</th><th scope="col">Cuándo</th><th scope="col">Motivo</th></tr>
              </thead>
              <tbody>
                @for (h of p.historial; track $index) {
                  <tr>
                    <td>{{ h.estadoAnterior ? etiqueta(p, h.estadoAnterior) : '—' }}</td>
                    <td><strong>{{ etiqueta(p, h.estadoNuevo) }}</strong></td>
                    <td>{{ h.autor }}</td>
                    <td>{{ fecha(h.fecha) }}</td>
                    <td>{{ h.motivo || '—' }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        </app-tarjeta>
        <app-tarjeta titulo="Línea de seguimiento" [span]="12">
          <app-pasos [pasos]="pasos(p)" />
        </app-tarjeta>
      </div>
    } @else {
      <app-estado-pantalla [estado]="e" />
    }
  `,
  styleUrl: './pantalla.css',
})
export class CierreHistorial {
  private readonly api = inject(DirectorApi);
  protected readonly estado = estadoPorCierre((id) => this.api.cierre(id));
  protected readonly fecha = formatoFecha;

  /** `Cerrada (aprobada)` para el estado final; el resto, su nombre. */
  protected etiqueta(p: Practica, estado: EstadoPractica): string {
    return estado === 'cerrada' && p.resultado ? `${ESTADO_PRACTICA.cerrada} (${RESULTADO_PRACTICA[p.resultado].toLowerCase()})` : ESTADO_PRACTICA[estado];
  }

  protected pasos(p: Practica): PasoItem[] {
    return p.historial.map((h: EntradaHistorial) => ({ estado: 'done', titulo: this.etiqueta(p, h.estadoNuevo), detalle: `${h.autor} · ${formatoFecha(h.fecha)}` }));
  }
}
