import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { formatoFecha } from '../../core/demo';
import { TutorAcademicoApi } from './tutor-academico.api';
import type { Revision } from './tutor-academico.model';
import { estadoPorParametro, subtipoTexto } from './tutor-academico.util';
import { DatosRevision } from './ui/datos-revision';
import { DecisionRevision } from './ui/decision-revision';
import { DocumentoRevision, type FilaDocumento } from './ui/documento-revision';
import { EstadoPantalla } from './ui/estado-pantalla';
import { EstadosEjemplo, type EstadoEjemplo } from './ui/estados-ejemplo';
import { SiguientePaso } from './ui/siguiente-paso';

/** T2 · Revisar informe final: validar o devolver con observación el informe de un tutorado. */
@Component({
  selector: 'app-revisar-informe',
  imports: [RouterLink, DocumentoRevision, DatosRevision, DecisionRevision, EstadoPantalla, EstadosEjemplo, SiguientePaso],
  template: `
    @let e = estado();
    @if (e.tipo === 'exito') {
      @let ini = e.datos;
      @let r = vigente(ini);
      <div class="grilla">
        <div class="span-12"><app-estados-ejemplo parametro="r" [estados]="ejemplos" [activo]="ini.clave" /></div>
        <app-documento-revision
          titulo="Informe final de actividades"
          [subtitulo]="subtitulo(ini)"
          [revision]="r"
          [inicial]="ini"
          documento="Informe final"
          textoValidado="Ya puede registrar la evaluación final."
          [filas]="filas(r)"
        />
        <app-datos-revision [revision]="r" />
        @if (ini.estado === 'en_revision') {
          <app-decision-revision
            [revision]="ini"
            [okValidar]="{
              titulo: 'Informe final validado.',
              texto: ini.practica.informeExterno ? 'Ya puede registrar la evaluación final.' : 'Cuando el informe externo esté registrado podrá registrar la evaluación final.',
            }"
            [okDevolver]="{ titulo: 'Informe final devuelto con observación.', texto: 'El estudiante verá la observación y podrá corregirlo.' }"
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
export class RevisarInforme {
  private readonly api = inject(TutorAcademicoApi);
  protected readonly estado = estadoPorParametro('r', (clave) => this.api.revision('informe', clave));
  protected readonly decidida = signal<Revision | null>(null);

  protected readonly ejemplos: EstadoEjemplo[] = [
    { clave: 'v6', texto: 'Valeria (en revisión)' },
    { clave: 'v6d', texto: 'Devuelto' },
    { clave: 'm5', texto: 'Validado · Mateo' },
  ];

  protected vigente(inicial: Revision): Revision {
    const d = this.decidida();
    return d && d.clave === inicial.clave ? d : inicial;
  }

  protected subtitulo(r: Revision): string {
    if (r.estado !== 'en_revision') return `Estado de ejemplo: ${r.estado === 'validado' ? 'validado' : 'devuelto con observación'}`;
    return `${subtipoTexto(r.practica)} · enviado por el estudiante`;
  }

  protected filas(r: Revision): FilaDocumento[] {
    const { informeFinal, informeExterno } = r.practica;
    return [
      { etiqueta: 'Resumen', texto: informeFinal?.resumen ?? '' },
      { etiqueta: 'Archivo', archivos: informeFinal ? [informeFinal.archivo] : [] },
      {
        etiqueta: 'Informe externo',
        insignia: informeExterno ? { tipo: 'ok', texto: `Registrado el ${formatoFecha(informeExterno.registradoEl)}` } : { tipo: 'warn', texto: 'Informe externo aún no registrado' },
      },
    ];
  }
}
