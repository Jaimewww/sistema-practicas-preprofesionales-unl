import { Component, inject } from '@angular/core';
import { avanceDe, ESTADO_ANEXO, fechaCierre, formatoFecha, CARRERA } from '../../core/demo';
import type { Anexo } from '../../core/demo';
import { BarraHoras, Insignia, Tarjeta } from '../../shared/ui';
import { DirectorApi } from './director.api';
import { estadoPorCierre, textoResultado, textoTipoLargo, tipoResultado } from './director.util';
import { EstadoPantalla } from './ui/estado-pantalla';

/** D2 · Detalle del cierre (pestaña Resumen): datos, horas, resultado de la evaluación final y anexos. */
@Component({
  selector: 'app-cierre-resumen',
  imports: [Tarjeta, Insignia, BarraHoras, EstadoPantalla],
  template: `
    @let e = estado();
    @if (e.tipo === 'exito') {
      @let p = e.datos;
      @let av = avance(p);
      <div class="grilla">
        <app-tarjeta [titulo]="p.estudiante" [span]="12">
          <div class="insignias">
            <app-insignia [tipo]="tipoResultado(p.resultado)" [texto]="textoResultado(p.resultado)" />
            <app-insignia tipo="info" [texto]="'Cerrada el ' + cerradaEl(p)" />
          </div>
          <div class="dos-columnas">
            <dl class="datos">
              <dt>Estudiante</dt><dd>{{ p.estudiante }}</dd>
              <dt>Tipo</dt><dd>{{ textoTipoLargo(p) }}</dd>
              @if (p.entidad) {
                <dt>Entidad receptora</dt><dd>{{ p.entidad }}</dd>
              }
              <dt>Tutor académico</dt><dd>{{ p.tutorAcademico }}</dd>
              @if (p.tipo === 'laboral') {
                <dt>Tutor de la entidad</dt><dd>{{ p.tutorEntidad }}</dd>
              } @else {
                <dt>Proyecto de vinculación</dt><dd>{{ p.proyectoVinculacion }}</dd>
              }
            </dl>
            <dl class="datos">
              <dt>Período académico</dt><dd>{{ p.periodo }}</dd>
              <dt>Carrera</dt><dd>{{ carrera }}</dd>
              <dt>Horas validadas</dt><dd><strong>{{ av.validadas }} h</strong> de {{ av.requeridas }} h requeridas</dd>
            </dl>
          </div>
          <app-barra-horas [validadas]="av.validadas" [enRevision]="av.enRevision" [requeridas]="av.requeridas" />
        </app-tarjeta>
        <app-tarjeta titulo="Resultado de la evaluación final" [span]="5">
          @if (p.evaluacion; as ev) {
            <dl class="datos">
              <dt>Desempeño</dt><dd>{{ ev.porcentaje }} %</dd>
              <dt>Resultado</dt><dd><app-insignia [tipo]="tipoResultado(ev.resultado)" [texto]="textoResultado(ev.resultado)" /></dd>
              <dt>Registrado por</dt><dd>{{ ev.registradoPor }} el {{ fecha(ev.registradoEl) }}</dd>
            </dl>
          } @else {
            <p class="texto">Sin evaluación final registrada.</p>
          }
        </app-tarjeta>
        <app-tarjeta titulo="Anexos del cierre" sub="Los legaliza la Secretaría de la carrera." [span]="7">
          <div class="tabla-marco">
            <table class="tbl">
              <caption class="sr-only">Anexos del cierre</caption>
              <thead>
                <tr><th scope="col">Anexo</th><th scope="col">Archivo</th><th scope="col">Estado</th><th scope="col">Legalizado por</th></tr>
              </thead>
              <tbody>
                @for (a of p.anexos; track a.id) {
                  <tr>
                    <td>{{ a.nombre }}</td>
                    <td>{{ a.archivo }}</td>
                    <td><app-insignia [tipo]="a.estado === 'legalizado' ? 'ok' : 'warn'" [texto]="textoAnexo(a)" /></td>
                    <td>{{ legalizadoPor(a) }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        </app-tarjeta>
      </div>
    } @else {
      <app-estado-pantalla [estado]="e" />
    }
  `,
  styleUrl: './pantalla.css',
})
export class CierreResumen {
  private readonly api = inject(DirectorApi);
  protected readonly estado = estadoPorCierre((id) => this.api.cierre(id));

  protected readonly carrera = CARRERA;
  protected readonly avance = avanceDe;
  protected readonly textoResultado = textoResultado;
  protected readonly tipoResultado = tipoResultado;
  protected readonly textoTipoLargo = textoTipoLargo;
  protected readonly fecha = formatoFecha;
  protected readonly cerradaEl = (p: Parameters<typeof fechaCierre>[0]): string => formatoFecha(fechaCierre(p) ?? '');
  protected readonly textoAnexo = (a: Anexo): string => ESTADO_ANEXO[a.estado];
  protected readonly legalizadoPor = (a: Anexo): string => (a.legalizadoEl ? `${a.legalizadoPor} el ${formatoFecha(a.legalizadoEl)}` : '—');
}
