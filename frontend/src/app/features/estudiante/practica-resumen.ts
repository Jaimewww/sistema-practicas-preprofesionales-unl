import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { avanceDe, formatoFecha, TOTAL_SEMANAS } from '../../core/demo';
import { BarraHoras, Insignia, Kpi, KpiGrid, Tarjeta, Vacio } from '../../shared/ui';
import { EstudianteApi } from './estudiante.api';
import { estadoPorPractica, nombrePropio, paramPractica, paramsReporte, pendientes, rangoCorto, rangoLargo } from './estudiante.util';
import { EstadoPantalla } from './ui/estado-pantalla';
import { FranjaSemanas } from './ui/franja-semanas';

/** E2 · Mi práctica (pestaña «Resumen»): avance frente a lo esperado, semanas y pendientes. */
@Component({
  selector: 'app-practica-resumen',
  imports: [RouterLink, Tarjeta, Insignia, BarraHoras, Kpi, KpiGrid, Vacio, FranjaSemanas, EstadoPantalla],
  host: { class: 'span-12' },
  template: `
    @let e = estado();
    @if (e.tipo === 'exito') {
      @let p = e.datos;
      @let av = avance(p);
      @let lista = pendientes(p);
      <div class="grilla">
        <app-tarjeta titulo="Avance frente a lo esperado" [span]="7">
          <div class="cuerpo">
            <p class="texto">
              A la semana {{ p.semanaActual }} de {{ semanas }} debería llevar <strong>{{ av.esperadas }} h</strong> validadas y lleva <strong>{{ av.validadas }} h</strong> ({{ av.pctCumplimiento }} % de lo esperado).
              Cuenta con {{ av.enRevision }} h en revisión.
            </p>
            <app-kpi-grid [tres]="true">
              <app-kpi etiqueta="Validadas" [valor]="av.validadas + ' h'" />
              <app-kpi etiqueta="En revisión" [valor]="av.enRevision + ' h'" />
              <app-kpi etiqueta="Requeridas" [valor]="av.requeridas + ' h'" />
            </app-kpi-grid>
            <app-barra-horas [validadas]="av.validadas" [enRevision]="av.enRevision" [requeridas]="av.requeridas" [esperadas]="av.esperadas" />
            <h4>Semanas de la práctica</h4>
            <app-franja-semanas [reportes]="p.reportes" [semanaActual]="p.semanaActual" />
            <p class="nota">Solo cuentan las horas validadas por su tutor académico. Le faltan <strong>{{ av.faltantes }} h</strong> para completar las {{ av.requeridas }} requeridas.</p>
          </div>
        </app-tarjeta>

        <app-tarjeta titulo="Pendiente" sub="Acciones que dependen de usted." [span]="5">
          <div class="cuerpo">
            @if (lista.length) {
              <ul class="pendientes">
                @for (x of lista; track x.reporte.semana) {
                  <li>
                    <div class="cabeza">
                      @switch (x.tipo) {
                        @case ('devuelto') {
                          <app-insignia tipo="bad" texto="Devuelto con observación" />
                        }
                        @case ('sin_reporte') {
                          <app-insignia tipo="warn" texto="Sin reporte" />
                        }
                        @default {
                          <app-insignia tipo="warn" texto="En revisión" />
                        }
                      }
                      <strong>Semana {{ x.reporte.semana }}</strong>
                    </div>
                    @switch (x.tipo) {
                      @case ('devuelto') {
                        <p class="demo">{{ rangoLargo(x.reporte) }} · devuelto por {{ nombrePropio(x.reporte.validadoPor) }} el {{ formatoFecha(x.reporte.validadoEl ?? x.reporte.hasta) }}</p>
                        <p><strong>Observación:</strong> {{ x.reporte.observacion }}</p>
                        <a class="enlace" routerLink="/estudiante/reporte" [queryParams]="paramsReporte(p.id, x.reporte.semana)">
                          Corregir reporte <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" aria-hidden="true"><path d="M9 6l6 6-6 6" /></svg>
                        </a>
                      }
                      @case ('sin_reporte') {
                        <p>Aún no envía el reporte de esta semana ({{ rangoCorto(x.reporte) }}).</p>
                        <a class="enlace" routerLink="/estudiante/reportes/nuevo">
                          Reportar semana {{ x.reporte.semana }} <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" aria-hidden="true"><path d="M9 6l6 6-6 6" /></svg>
                        </a>
                      }
                      @default {
                        <p>{{ x.reporte.horas }} h esperando la validación de su tutor académico. No tiene que hacer nada.</p>
                      }
                    }
                  </li>
                }
              </ul>
            } @else {
              <app-vacio titulo="Todo al día" texto="No tiene acciones pendientes por ahora." />
            }
            <div class="acciones-fila">
              <a class="boton" routerLink="/estudiante/reportes/nuevo">
                Nuevo reporte semanal <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" aria-hidden="true"><path d="M9 6l6 6-6 6" /></svg>
              </a>
            </div>
          </div>
        </app-tarjeta>
      </div>
    } @else {
      <app-estado-pantalla [estado]="e" />
    }
  `,
  styleUrl: './pantalla.css',
})
export class PracticaResumen {
  private readonly api = inject(EstudianteApi);
  protected readonly estado = estadoPorPractica((id) => this.api.practica(id));

  protected readonly semanas = TOTAL_SEMANAS;
  protected readonly avance = avanceDe;
  protected readonly pendientes = pendientes;
  protected readonly nombrePropio = nombrePropio;
  protected readonly paramPractica = paramPractica;
  protected readonly paramsReporte = paramsReporte;
  protected readonly rangoCorto = rangoCorto;
  protected readonly rangoLargo = rangoLargo;
  protected readonly formatoFecha = formatoFecha;
}
