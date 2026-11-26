import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ESTADO_REPORTE, formatoFecha, TOTAL_SEMANAS } from '../../core/demo';
import type { EstadoReporte, Practica } from '../../core/demo';
import { Insignia, Kpi, KpiGrid, Tarjeta, Vacio } from '../../shared/ui';
import { EstudianteApi } from './estudiante.api';
import { estadoPorPractica, nombrePropio, paramsReporte, rangoCorto, textoReporte, tipoReporte } from './estudiante.util';
import { EstadoPantalla } from './ui/estado-pantalla';

type Filtro = '' | EstadoReporte;

/** E2 · pestaña «Reportes semanales»: tabla con filtro por estado y acceso a E5 / E4. */
@Component({
  selector: 'app-practica-reportes',
  imports: [RouterLink, Tarjeta, Insignia, Kpi, KpiGrid, Vacio, EstadoPantalla],
  host: { class: 'span-12' },
  template: `
    @let e = estado();
    @if (e.tipo === 'exito') {
      @let p = e.datos;
      @let filas = visibles(p);
      <div class="grilla">
        <app-tarjeta titulo="Reportes semanales" sub="Un reporte activo por semana. Solo las horas validadas cuentan para su avance." [span]="12">
          <app-kpi-grid>
            <app-kpi etiqueta="Reportes enviados" [valor]="contar(p, null)" />
            <app-kpi etiqueta="Validados" [valor]="contar(p, 'validado')" />
            <app-kpi etiqueta="Devueltos" [valor]="contar(p, 'devuelto')" />
            <app-kpi etiqueta="En revisión" [valor]="contar(p, 'en_revision')" />
          </app-kpi-grid>
          <div class="herramientas">
            <label for="filtro-estado">Estado
              <select id="filtro-estado" [value]="filtro()" (change)="filtro.set($any($event.target).value)">
                <option value="">--Todos--</option>
                @for (opcion of opciones; track opcion) {
                  <option [value]="opcion">{{ etiqueta(opcion) }}</option>
                }
              </select>
            </label>
            <a class="boton" routerLink="/estudiante/reportes/nuevo">
              Nuevo reporte semanal <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" aria-hidden="true"><path d="M9 6l6 6-6 6" /></svg>
            </a>
          </div>
          <div class="tabla-caja">
            <table>
              <caption class="sr-only">Reportes semanales de la práctica {{ p.tipo }}</caption>
              <thead>
                <tr>
                  <th scope="col">Semana</th><th scope="col">Periodo</th><th scope="col">Horas</th><th scope="col">Estado</th><th scope="col">Enviado</th><th scope="col">Validación</th><th scope="col"><span class="sr-only">Acción</span></th>
                </tr>
              </thead>
              <tbody>
                @for (r of filas; track r.semana) {
                  <tr>
                    <td class="nowrap"><strong>Semana {{ r.semana }}</strong></td>
                    <td class="nowrap">{{ rangoCorto(r) }}</td>
                    <td class="nowrap">{{ r.estado === 'sin_reporte' ? '—' : r.horas + ' h' }}</td>
                    <td><app-insignia [tipo]="tipoReporte(r.estado)" [texto]="textoReporte(r.estado, true)" /></td>
                    <td class="nowrap">{{ r.enviadoEl ? formatoFecha(r.enviadoEl) : '—' }}</td>
                    <td>{{ validacion(r) }}</td>
                    <td>
                      @if (r.estado === 'sin_reporte') {
                        <a class="enlace" routerLink="/estudiante/reportes/nuevo" [attr.aria-label]="'Reportar la semana ' + r.semana">Reportar</a>
                      } @else {
                        <a class="enlace" routerLink="/estudiante/reporte" [queryParams]="paramsReporte(p.id, r.semana)" [attr.aria-label]="(r.estado === 'devuelto' ? 'Corregir' : 'Ver') + ' el reporte de la semana ' + r.semana">{{ r.estado === 'devuelto' ? 'Corregir' : 'Ver' }}</a>
                      }
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
          @if (!filas.length) {
            <app-vacio titulo="No hay reportes con ese estado" texto="Elija «--Todos--» para ver todas las semanas." />
          }
          @if (p.semanaActual < semanas) {
            <p class="nota">Semanas {{ p.semanaActual + 1 }} a {{ semanas }}: aún no inician.</p>
          }
        </app-tarjeta>
      </div>
    } @else {
      <app-estado-pantalla [estado]="e" />
    }
  `,
  styleUrl: './pantalla.css',
  styles: `
    .herramientas {
      display: flex;
      flex-wrap: wrap;
      gap: 14px;
      align-items: end;
      justify-content: space-between;
    }
    .herramientas label {
      display: grid;
      gap: var(--espacio-1);
      font-size: 12px;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      color: var(--color-texto-suave);
    }
    select {
      min-width: 200px;
      padding: 10px 14px;
      font: inherit;
      font-size: 14.5px;
      text-transform: none;
      letter-spacing: 0;
      color: var(--color-texto);
      background: #fff;
      border: 1px solid #7b838c;
      border-radius: 10px;
    }
    select:focus {
      outline: none;
      border-color: var(--color-enlace);
      box-shadow: 0 0 0 3px rgba(0, 80, 158, 0.18);
    }
    .tabla-caja {
      margin-top: var(--espacio-3);
      overflow: auto;
    }
    table {
      width: 100%;
      font-size: 14.5px;
      border-collapse: collapse;
    }
    th {
      padding: 10px var(--espacio-3);
      font-size: 12px;
      font-weight: 500;
      letter-spacing: 0.05em;
      text-align: left;
      text-transform: uppercase;
      color: var(--color-texto-suave);
      background: var(--color-crema-2);
      border-bottom: 2px solid var(--color-borde);
    }
    td {
      padding: var(--espacio-3);
      vertical-align: middle;
      border-bottom: 1px dashed var(--color-borde);
    }
    tbody tr:hover td {
      background: #fbf6ea;
    }
    .nowrap {
      white-space: nowrap;
    }
  `,
})
export class PracticaReportes {
  private readonly api = inject(EstudianteApi);
  protected readonly estado = estadoPorPractica((id) => this.api.practica(id));

  protected readonly filtro = signal<Filtro>('');
  protected readonly opciones: EstadoReporte[] = ['validado', 'devuelto', 'en_revision', 'sin_reporte'];
  protected readonly semanas = TOTAL_SEMANAS;

  protected readonly etiqueta = (e: EstadoReporte): string => (e === 'devuelto' ? 'Devuelto' : ESTADO_REPORTE[e]);
  protected readonly tipoReporte = tipoReporte;
  protected readonly textoReporte = textoReporte;
  protected readonly paramsReporte = paramsReporte;
  protected readonly rangoCorto = rangoCorto;
  protected readonly formatoFecha = formatoFecha;

  /** Con `null`, los enviados (todo menos «sin reporte»). */
  protected contar(p: Practica, estado: EstadoReporte | null): number {
    return p.reportes.filter((r) => (estado ? r.estado === estado : r.estado !== 'sin_reporte')).length;
  }

  protected readonly visibles = (p: Practica) => (this.filtro() ? p.reportes.filter((r) => r.estado === this.filtro()) : p.reportes);

  protected validacion(r: Practica['reportes'][number]): string {
    switch (r.estado) {
      case 'validado':
        return `${nombrePropio(r.validadoPor)} · ${formatoFecha(r.validadoEl ?? r.hasta)}`;
      case 'devuelto':
        return `Devuelto por ${nombrePropio(r.validadoPor)} · ${formatoFecha(r.validadoEl ?? r.hasta)}`;
      case 'en_revision':
        return 'Esperando validación';
      default:
        return '—';
    }
  }
}
