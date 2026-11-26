import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { cargando } from '../../core/estado-ui';
import { avanceDe, TOTAL_SEMANAS } from '../../core/demo';
import type { Practica } from '../../core/demo';
import { BarraHoras, Insignia, Tarjeta } from '../../shared/ui';
import { EstudianteApi } from './estudiante.api';
import { aEstado, nombrePropio, paramPractica, rezagada, textoPractica, textoTipo, tipoPractica } from './estudiante.util';
import { EstadoPantalla } from './ui/estado-pantalla';

/** E1 · Mis prácticas: la laboral y la comunitaria son registros separados. */
@Component({
  selector: 'app-mis-practicas',
  imports: [RouterLink, Tarjeta, Insignia, BarraHoras, EstadoPantalla],
  template: `
    @let e = estado();
    @if (e.tipo === 'exito') {
      <div class="grilla">
        <app-tarjeta titulo="Mis prácticas" sub="La práctica laboral y la comunitaria son registros separados. Si solo tuviera una, entraría directo a «Mi práctica»." [span]="12" />
        @for (p of e.datos; track p.id) {
          @let av = avance(p);
          <app-tarjeta [titulo]="titulo(p)" [sub]="'Periodo ' + p.periodo + ' · Semana ' + p.semanaActual + ' de ' + semanas" [span]="6">
            <div class="cuerpo">
              <div class="insignias">
                <app-insignia tipo="info" [texto]="textoTipo(p)" />
                <app-insignia [tipo]="tipoPractica(p)" [texto]="textoPractica(p)" />
                @if (p.plan.estado !== 'validado') {
                  <app-insignia tipo="warn" texto="Plan pendiente" />
                } @else {
                  <app-insignia [tipo]="rezagada(p) ? 'bad' : 'ok'" [texto]="rezagada(p) ? 'Rezagada' : 'Al día'" />
                }
              </div>
              <dl class="datos">
                <div><dt>Tutor académico</dt><dd>{{ nombrePropio(p.tutorAcademico) }}</dd></div>
                @if (p.tipo === 'laboral') {
                  <div><dt>Tutora de la entidad</dt><dd>{{ nombrePropio(p.tutorEntidad) }}</dd></div>
                } @else {
                  <div><dt>Tutor de la entidad</dt><dd>No aplica en servicio comunitario</dd></div>
                }
              </dl>
              <div>
                <app-barra-horas [validadas]="av.validadas" [enRevision]="av.enRevision" [requeridas]="av.requeridas" [leyenda]="false" />
                <p class="texto">{{ av.validadas }} h validadas · {{ av.enRevision }} h en revisión · {{ av.requeridas }} h requeridas</p>
              </div>
              <div class="acciones-fila">
                @if (p.plan.estado === 'validado') {
                  <a class="boton" routerLink="/estudiante/practica" [queryParams]="paramPractica(p.id)">Ir a mi práctica <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" aria-hidden="true"><path d="M9 6l6 6-6 6" /></svg></a>
                } @else {
                  <a class="boton" routerLink="/estudiante/plan" [queryParams]="paramPractica(p.id)">Registrar mi plan <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" aria-hidden="true"><path d="M9 6l6 6-6 6" /></svg></a>
                  <a class="boton-secundario" routerLink="/estudiante/practica" [queryParams]="paramPractica(p.id)">Ver práctica</a>
                }
              </div>
            </div>
          </app-tarjeta>
        }
        <p class="demo span-12">Datos de ejemplo del prototipo.</p>
      </div>
    } @else {
      <app-estado-pantalla [estado]="e" vacioTitulo="Aún no tiene prácticas" vacioTexto="Cuando la coordinación le asigne una práctica la verá aquí." />
    }
  `,
  styleUrl: './pantalla.css',
})
export class MisPracticas {
  private readonly api = inject(EstudianteApi);
  protected readonly estado = toSignal(aEstado(this.api.misPracticas(), (lista) => lista.length === 0), { initialValue: cargando<Practica[]>() });

  protected readonly semanas = TOTAL_SEMANAS;
  protected readonly avance = avanceDe;
  protected readonly rezagada = rezagada;
  protected readonly textoPractica = textoPractica;
  protected readonly tipoPractica = tipoPractica;
  protected readonly textoTipo = textoTipo;
  protected readonly nombrePropio = nombrePropio;
  protected readonly paramPractica = paramPractica;

  /** La laboral se titula con su entidad; la comunitaria, con el proyecto de vinculación. */
  protected titulo(p: Practica): string {
    return p.tipo === 'laboral' ? p.entidad : `Proyecto de vinculación · ${p.proyectoVinculacion}`;
  }
}
