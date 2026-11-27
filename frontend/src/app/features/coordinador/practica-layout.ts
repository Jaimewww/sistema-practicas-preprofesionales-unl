import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ESTADO_PRACTICA } from '../../core/demo';
import type { EstadoPractica } from '../../core/demo';
import { Insignia, Pestanas, Tarjeta, type PestanaItem } from '../../shared/ui';
import { componente, nombrePropio, paramsPractica, textoEstado, tipoEstado } from './coordinador.util';
import { PracticaActual } from './practica-actual';
import { EstadoPantalla } from './ui/estado-pantalla';

/** Marco de C3: datos de la práctica, selector de estado de la demostración y pestañas Resumen / Historial. */
@Component({
  selector: 'app-practica-layout',
  imports: [RouterOutlet, Tarjeta, Insignia, Pestanas, EstadoPantalla],
  providers: [PracticaActual],
  template: `
    <div class="grilla">
      @let e = ctx.estado();
      @if (e.tipo === 'exito') {
        @let p = e.datos.practica;
        @let est = ctx.estadoMostrado() ?? p.estado;
        <app-tarjeta [titulo]="nombrePropio(p.estudiante)" [sub]="componente(p) + ' · ' + p.periodo" [span]="12">
          <div acciones><app-insignia [tipo]="tipoEstado(p, est)" [texto]="textoEstado(p, est)" /></div>
          <div class="filtros">
            <label>Estado (demo)
              <select id="demo-estado" aria-describedby="demo-estado-ayuda" (change)="ctx.cambiarDemo(valor($event))">
                @for (x of estados; track x[0]) { <option [value]="x[0]" [selected]="x[0] === est">{{ x[1] }}</option> }
              </select>
            </label>
            <span id="demo-estado-ayuda" class="sub">Solo para la demostración: muestra cómo cambian las acciones y el modo de solo lectura según el estado.</span>
          </div>
        </app-tarjeta>
        <div class="span-12">
          <app-pestanas etiqueta="Secciones de la práctica" [items]="pestanas(p.id)" />
          <router-outlet />
        </div>
      } @else {
        <div class="span-12"><app-estado-pantalla [estado]="e" vacioTitulo="No encontramos esa práctica" /></div>
      }
    </div>
  `,
  styleUrl: './pantalla.css',
})
export class PracticaLayout {
  protected readonly ctx = inject(PracticaActual);
  protected readonly estados = Object.entries(ESTADO_PRACTICA) as Array<[EstadoPractica, string]>;
  protected readonly componente = componente;
  protected readonly nombrePropio = nombrePropio;
  protected readonly textoEstado = textoEstado;
  protected readonly tipoEstado = tipoEstado;

  protected valor(evento: Event): string {
    return (evento.target as HTMLSelectElement).value;
  }

  protected pestanas(id: number): PestanaItem[] {
    const demo = this.ctx.demoParam();
    const parametros = paramsPractica(id, demo ? { estado: demo } : {});
    return [
      { texto: 'Resumen', enlace: '/coordinador/practica', parametros },
      { texto: 'Historial', enlace: '/coordinador/practica/historial', parametros },
    ];
  }
}
