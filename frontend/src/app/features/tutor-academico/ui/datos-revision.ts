import { Component, computed, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { avanceDe } from '../../../core/demo';
import { BarraHoras, Insignia, Tarjeta } from '../../../shared/ui';
import type { Revision } from '../tutor-academico.model';
import { descripcionPractica, textoPractica, tipoPractica } from '../tutor-academico.util';

/** Tarjeta «Datos de la práctica» de las pantallas de revisión (T2): quién, dónde, horas y enlace a la práctica. */
@Component({
  selector: 'app-datos-revision',
  imports: [RouterLink, Tarjeta, Insignia, BarraHoras],
  host: { style: 'display: contents' }, // la tarjeta interior es la que ocupa columnas en .grilla
  template: `
    @let p = revision().practica;
    @let av = avance();
    <app-tarjeta titulo="Datos de la práctica" [span]="5">
      <dl class="dl">
        <dt>Estudiante</dt>
        <dd>{{ p.estudiante }}</dd>
        <dt>Práctica</dt>
        <dd>{{ descripcion(p) }}</dd>
        <dt>Entidad receptora</dt>
        <dd>{{ p.entidad }}</dd>
        @if (p.tipo === 'laboral') {
          <dt>Tutor de la entidad</dt>
          <dd>{{ p.tutorEntidad }}</dd>
        } @else {
          <dt>Proyecto</dt>
          <dd>{{ p.proyectoVinculacion }}</dd>
        }
        <dt>Estado</dt>
        <dd><app-insignia [tipo]="tipoEstado(p.estado)" [texto]="textoEstado(p.estado)" /></dd>
        <dt>Horas</dt>
        <dd>
          @if (p.estado === 'en_curso') {
            <app-insignia [tipo]="av.rezagada ? 'bad' : 'ok'" [texto]="av.rezagada ? 'Rezagada' : 'Al día'" />
          } @else {
            —
          }
        </dd>
      </dl>
      <app-barra-horas [validadas]="av.validadas" [enRevision]="av.enRevision" [requeridas]="av.requeridas" [esperadas]="p.estado === 'en_curso' ? av.esperadas : undefined" />
      <div class="acciones-fila">
        <a class="boton-secundario boton-sm" routerLink="/tutor-academico/practica" [queryParams]="{ p: p.id }">Ver práctica</a>
      </div>
    </app-tarjeta>
  `,
  styleUrl: '../pantalla.css',
})
export class DatosRevision {
  readonly revision = input.required<Revision>();
  protected readonly avance = computed(() => avanceDe(this.revision().practica));
  protected readonly descripcion = descripcionPractica;
  protected readonly tipoEstado = tipoPractica;
  protected readonly textoEstado = textoPractica;
}
