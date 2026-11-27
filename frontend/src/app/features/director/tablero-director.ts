import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { cargando } from '../../core/estado-ui';
import { CARRERA, fechaCierre, formatoFecha, PERIODO } from '../../core/demo';
import type { Practica } from '../../core/demo';
import { Aviso, Insignia, Kpi, KpiGrid, Tarjeta } from '../../shared/ui';
import { DirectorApi } from './director.api';
import { aEstado, textoResultado, textoTipo, tipoResultado } from './director.util';
import { EstadoPantalla } from './ui/estado-pantalla';

/** D0 · Tablero del director: resumen de los cierres de su carrera, en solo lectura. */
@Component({
  selector: 'app-tablero-director',
  imports: [RouterLink, Tarjeta, Insignia, Kpi, KpiGrid, Aviso, EstadoPantalla],
  template: `
    @let e = estado();
    @if (e.tipo === 'exito') {
      @let aprobadas = contar(e.datos, 'aprobada');
      <div class="grilla">
        <div class="span-12">
          <app-kpi-grid>
            <app-kpi etiqueta="Prácticas cerradas" [valor]="e.datos.length" nota="Carrera de Computación" />
            <app-kpi etiqueta="Aprobadas" [valor]="aprobadas" nota="Resultado de la evaluación final" />
            <app-kpi etiqueta="No aprobadas" [valor]="e.datos.length - aprobadas" nota="Se consultan en el detalle del cierre" [alerta]="true" />
            <app-kpi etiqueta="Período" [valor]="periodoCorto" [nota]="periodoResto" />
          </app-kpi-grid>
        </div>
        <app-tarjeta titulo="Últimos cierres" sub="Como director solo consulta: el cierre lo registra el coordinador." [span]="8">
          <ul class="lista-lineas">
            @for (p of ultimos(e.datos); track p.id) {
              <li>
                <div>
                  <strong>{{ p.estudiante }}</strong>
                  <small>{{ textoTipo(p) }} · cerrada el {{ cerradaEl(p) }}</small>
                </div>
                <app-insignia [tipo]="tipoResultado(p.resultado)" [texto]="textoResultado(p.resultado)" />
              </li>
            }
          </ul>
          <div class="acciones-fila">
            <a class="boton" routerLink="/director/cierres">
              Ver todos los cierres
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" aria-hidden="true"><path d="M9 6l6 6-6 6" /></svg>
            </a>
          </div>
        </app-tarjeta>
        <app-tarjeta titulo="Tu rol en las prácticas" [span]="4">
          <app-aviso tipo="info">Consultas los cierres de tu carrera y su historial (quién, qué y cuándo). No hay acciones de edición en estas pantallas.</app-aviso>
          <p class="texto">Carrera: {{ carrera }}</p>
        </app-tarjeta>
      </div>
    } @else {
      <app-estado-pantalla [estado]="e" vacioTitulo="Aún no hay cierres" vacioTexto="Cuando el coordinador cierre una práctica de su carrera la verá aquí." />
    }
  `,
  styleUrl: './pantalla.css',
})
export class TableroDirector {
  private readonly api = inject(DirectorApi);
  protected readonly estado = toSignal(aEstado(this.api.cierres(), (lista) => lista.length === 0), { initialValue: cargando<Practica[]>() });

  protected readonly carrera = CARRERA;
  protected readonly periodoCorto = PERIODO.split('-')[0];
  protected readonly periodoResto = PERIODO.split('-')[1];
  protected readonly textoTipo = textoTipo;
  protected readonly textoResultado = textoResultado;
  protected readonly tipoResultado = tipoResultado;

  protected contar = (lista: Practica[], resultado: string): number => lista.filter((p) => p.resultado === resultado).length;
  protected ultimos = (lista: Practica[]): Practica[] => lista.slice(0, 3);
  protected cerradaEl = (p: Practica): string => formatoFecha(fechaCierre(p) ?? '');
}
