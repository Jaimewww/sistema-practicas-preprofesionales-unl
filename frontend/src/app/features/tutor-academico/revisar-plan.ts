import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TutorAcademicoApi } from './tutor-academico.api';
import type { Revision } from './tutor-academico.model';
import { estadoPorParametro } from './tutor-academico.util';
import { DatosRevision } from './ui/datos-revision';
import { DecisionRevision } from './ui/decision-revision';
import { DocumentoRevision, type FilaDocumento } from './ui/documento-revision';
import { EstadoPantalla } from './ui/estado-pantalla';
import { EstadosEjemplo, type EstadoEjemplo } from './ui/estados-ejemplo';
import { SiguientePaso } from './ui/siguiente-paso';

/** T2 · Revisar plan de actividades: validar (la práctica pasa a «En curso») o devolver con observación. */
@Component({
  selector: 'app-revisar-plan',
  imports: [RouterLink, DocumentoRevision, DatosRevision, DecisionRevision, EstadoPantalla, EstadosEjemplo, SiguientePaso],
  template: `
    @let e = estado();
    @if (e.tipo === 'exito') {
      @let ini = e.datos;
      @let r = vigente(ini);
      <div class="grilla">
        <div class="span-12"><app-estados-ejemplo parametro="r" [estados]="ejemplos" [activo]="ini.clave" /></div>
        <app-documento-revision
          titulo="Plan de actividades"
          [subtitulo]="subtitulo(ini)"
          [revision]="r"
          [inicial]="ini"
          documento="Plan de actividades"
          textoValidado="La práctica pasó a «En curso»."
          [filas]="filas(r)"
        />
        <app-datos-revision [revision]="r" />
        @if (ini.estado === 'en_revision') {
          <app-decision-revision
            [revision]="ini"
            [okValidar]="{ titulo: 'Plan validado.', texto: 'La práctica pasa a «En curso» y el estudiante ya puede enviar sus reportes semanales.' }"
            [okDevolver]="{ titulo: 'Plan devuelto con observación.', texto: 'El estudiante verá la observación y podrá corregir el plan.' }"
            (decidida)="decidida.set($event)"
          />
        } @else {
          <app-siguiente-paso />
        }
        <a class="boton-secundario boton-sm volver" routerLink="/tutor-academico/pendientes">Volver a pendientes de revisión</a>
      </div>
    } @else {
      <app-estado-pantalla [estado]="e" />
    }
  `,
  styleUrl: './pantalla.css',
})
export class RevisarPlan {
  private readonly api = inject(TutorAcademicoApi);
  protected readonly estado = estadoPorParametro('r', (clave) => this.api.revision('plan', clave));
  protected readonly decidida = signal<Revision | null>(null);

  protected readonly ejemplos: EstadoEjemplo[] = [
    { clave: 'a4', texto: 'Andrea (en revisión)' },
    { clave: 'a4d', texto: 'Devuelto' },
    { clave: 'l1', texto: 'Validado' },
  ];

  protected vigente(inicial: Revision): Revision {
    const d = this.decidida();
    return d && d.clave === inicial.clave ? d : inicial;
  }

  protected subtitulo(r: Revision): string {
    if (r.estado !== 'en_revision') return `Estado de ejemplo: ${r.estado === 'validado' ? 'validado' : 'devuelto con observación'}`;
    return r.practica.estado === 'asignada' ? `Práctica ${r.practica.tipo} · sin plan aprobado todavía` : `Práctica ${r.practica.tipo}`;
  }

  protected filas(r: Revision): FilaDocumento[] {
    const p = r.practica;
    const filas: FilaDocumento[] = [];
    if (p.tipo === 'comunitaria') filas.push({ etiqueta: 'Proyecto', texto: p.proyectoVinculacion });
    filas.push({ etiqueta: 'Horas requeridas', texto: `${p.horasRequeridas} h` }, { etiqueta: 'Actividades', lista: p.plan.actividades });
    return filas;
  }
}
