import { Component, computed } from '@angular/core';
import { RouterLink, RouterOutlet } from '@angular/router';
import { Pestanas, type PestanaItem } from '../../shared/ui';
import { cierreActual } from './director.util';

/** Marco del detalle de un cierre: las pestañas Resumen/Historial y el regreso a la lista. */
@Component({
  selector: 'app-cierre-layout',
  imports: [RouterOutlet, RouterLink, Pestanas],
  template: `
    <app-pestanas etiqueta="Secciones" [items]="pestanas()" />
    <router-outlet />
    <div class="acciones-fila">
      <a class="boton-secundario" routerLink="/director/cierres">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" aria-hidden="true"><path d="M15 6l-6 6 6 6" /></svg>
        Volver a los cierres
      </a>
    </div>
  `,
  styleUrl: './pantalla.css',
})
export class CierreLayout {
  private readonly id = cierreActual();
  protected readonly pestanas = computed<PestanaItem[]>(() => {
    const parametros = { p: this.id() };
    return [
      { texto: 'Resumen del cierre', enlace: '/director/cierre', parametros },
      { texto: 'Historial', enlace: '/director/cierre/historial', parametros },
    ];
  });
}
