import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import type { ReporteSemanal } from '../../core/demo';
import { TutorAcademicoApi } from './tutor-academico.api';
import type { Revision } from './tutor-academico.model';
import { estadoPorParametro, rangoLargo, subtipoTexto } from './tutor-academico.util';
import { DatosRevision } from './ui/datos-revision';
import { DecisionRevision } from './ui/decision-revision';
import { DocumentoRevision, type FilaDocumento } from './ui/documento-revision';
import { EstadoPantalla } from './ui/estado-pantalla';
import { EstadosEjemplo, type EstadoEjemplo } from './ui/estados-ejemplo';
import { SiguientePaso } from './ui/siguiente-paso';

/** Horas máximas por semana de una ayudantía (Art. 341). */
const LIMITE_AYUDANTIA = 10;

/** T2 · Revisar reporte semanal: validar o devolver (con observación obligatoria) el reporte de un tutorado. */
@Component({
  selector: 'app-revisar-reporte',
  imports: [RouterLink, DocumentoRevision, DatosRevision, DecisionRevision, EstadoPantalla, EstadosEjemplo, SiguientePaso],
  template: `
    @let e = estado();
    @if (e.tipo === 'exito') {
      @let ini = e.datos;
      @let r = vigente(ini);
      @let rep = reporte(ini);
      <div class="grilla">
        <div class="span-12"><app-estados-ejemplo parametro="r" [estados]="ejemplos" [activo]="ini.clave" /></div>
        <app-documento-revision
          [titulo]="'Reporte semanal: Semana ' + ini.semana"
          [subtitulo]="ini.estado === 'en_revision' ? subtitulo(ini, rep) : ejemploEstado(ini)"
          [revision]="r"
          [inicial]="ini"
          documento="Reporte semanal"
          [textoValidado]="'Sus ' + rep.horas + ' h ya cuentan como horas validadas de la práctica.'"
          [filas]="filas(r, rep)"
        />
        <app-datos-revision [revision]="r" />
        @if (ini.estado === 'en_revision') {
          <app-decision-revision
            [revision]="ini"
            [okValidar]="{ titulo: 'Reporte validado.', texto: 'Sus ' + rep.horas + ' h ya cuentan como horas validadas de la práctica.' }"
            [okDevolver]="{ titulo: 'Reporte devuelto con observación.', texto: 'El estudiante la verá y podrá corregir el reporte y reenviarlo.' }"
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
export class RevisarReporte {
  private readonly api = inject(TutorAcademicoApi);
  protected readonly estado = estadoPorParametro('r', (clave) => this.api.revision('reporte', clave));
  protected readonly decidida = signal<Revision | null>(null);

  protected readonly ejemplos: EstadoEjemplo[] = [
    { clave: 'd7', texto: 'Semana 7 · Diego (fuera de plazo)' },
    { clave: 'l8', texto: 'Semana 8 · Luciana' },
    { clave: 'd8', texto: 'Semana 8 · Diego' },
    { clave: 'l5', texto: 'Devuelto' },
    { clave: 'l6', texto: 'Validado' },
  ];

  protected vigente(inicial: Revision): Revision {
    const d = this.decidida();
    return d && d.clave === inicial.clave ? d : inicial;
  }

  protected reporte(r: Revision): ReporteSemanal {
    return r.practica.reportes.find((x) => x.semana === r.semana)!;
  }

  protected subtitulo(r: Revision, rep: ReporteSemanal): string {
    return `${subtipoTexto(r.practica)} · ${rangoLargo(rep)}`;
  }

  protected ejemploEstado(r: Revision): string {
    return `Estado de ejemplo: ${r.estado === 'validado' ? 'validado' : 'devuelto con observación'}`;
  }

  protected filas(r: Revision, rep: ReporteSemanal): FilaDocumento[] {
    const enRevision = r.estado === 'en_revision';
    let horas = `${rep.horas} h`;
    if (r.practica.esAyudantia && enRevision) {
      horas += rep.horas >= LIMITE_AYUDANTIA ? ' (en el límite de la ayudantía, Art. 341)' : ` (límite de ayudantía: ${LIMITE_AYUDANTIA} h, Art. 341)`;
    }
    const entidad: FilaDocumento =
      rep.confirmadoPorEntidad === null
        ? { etiqueta: 'Entidad', texto: '—' }
        : { etiqueta: 'Entidad', insignia: rep.confirmadoPorEntidad ? { tipo: 'ok', texto: 'Confirmado por la entidad' } : { tipo: 'warn', texto: 'Pendiente de confirmación' } };
    return [
      { etiqueta: 'Semana', texto: rangoLargo(rep) },
      { etiqueta: 'Horas', texto: horas },
      rep.actividades.length ? { etiqueta: 'Actividades', lista: rep.actividades } : { etiqueta: 'Actividades', texto: 'Sin actividades registradas.' },
      rep.evidencias.length ? { etiqueta: 'Evidencias', archivos: rep.evidencias } : { etiqueta: 'Evidencias', texto: 'Sin evidencias adjuntas.' },
      entidad,
    ];
  }
}
