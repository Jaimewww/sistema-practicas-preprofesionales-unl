import { Component, computed, input } from '@angular/core';
import { formatoFecha } from '../../../core/demo';
import { Aviso, Insignia, Tarjeta, type TipoInsignia } from '../../../shared/ui';
import type { Revision } from '../tutor-academico.model';
import { textoRevision, tipoRevision } from '../tutor-academico.util';

/** Una fila «etiqueta: valor» del documento; el valor puede ser texto, lista, archivos o una insignia. */
export interface FilaDocumento {
  etiqueta: string;
  texto?: string;
  lista?: string[];
  archivos?: string[];
  insignia?: { tipo: TipoInsignia; texto: string };
}

/**
 * Tarjeta del documento que se revisa en T2: título, avisos según su estado, insignia de estado
 * (región en vivo), filas de datos y, si ya se decidió, quién, cuándo y la observación.
 */
@Component({
  selector: 'app-documento-revision',
  imports: [Tarjeta, Aviso, Insignia],
  host: { style: 'display: contents' }, // la tarjeta interior es la que ocupa columnas en .grilla
  template: `
    @let r = revision();
    <app-tarjeta [titulo]="titulo()" [sub]="subtitulo()" [span]="7">
      @if (inicial().estado === 'en_revision' && inicial().fueraDePlazo) {
        <app-aviso tipo="bad"><strong>Fuera del plazo de revisión.</strong> Lleva {{ inicial().dias }} días hábiles; el plazo de la carrera es de {{ inicial().plazo }}. Se avisó a la coordinación.</app-aviso>
      }
      @if (inicial().estado === 'devuelto') {
        <app-aviso tipo="warn"><strong>{{ documento() }} devuelto con observación</strong>. El estudiante verá la observación y podrá corregirlo.</app-aviso>
      }
      @if (inicial().estado === 'validado') {
        <app-aviso tipo="info"><strong>{{ documento() }} validado</strong> por {{ inicial().decididoPor }} el {{ fechaInicial() }}. {{ textoValidado() }}</app-aviso>
      }
      <div aria-live="polite"><app-insignia [tipo]="tipoEstado()" [texto]="textoEstado()" /></div>
      <dl class="dl">
        <dt>Fecha de envío</dt>
        <dd>{{ r.enviadoEl ? fecha(r.enviadoEl) : '—' }}</dd>
        @if (r.dias !== null) {
          <dt>Días hábiles de espera</dt>
          <dd>
            {{ r.dias }} de {{ r.plazo }} días hábiles
            @if (r.fueraDePlazo) {
              <app-insignia tipo="bad" texto="Fuera de plazo" />
            }
          </dd>
        }
        @for (f of filas(); track f.etiqueta) {
          <dt>{{ f.etiqueta }}</dt>
          <dd>
            @if (f.texto) {
              {{ f.texto }}
            }
            @if (f.insignia) {
              <app-insignia [tipo]="f.insignia.tipo" [texto]="f.insignia.texto" />
            }
            @if (f.lista) {
              <ul>
                @for (x of f.lista; track x) {
                  <li>{{ x }}</li>
                }
              </ul>
            }
            @if (f.archivos) {
              <ul class="archivos">
                @for (a of f.archivos; track a) {
                  <li><span>{{ a }}</span><span class="tam">PDF</span></li>
                }
              </ul>
            }
          </dd>
        }
        @if (r.estado !== 'en_revision') {
          <dt>{{ r.estado === 'validado' ? 'Validado por' : 'Devuelto por' }}</dt>
          <dd>{{ r.decididoPor }}</dd>
          <dt>Fecha</dt>
          <dd>{{ r.decididoEl ? fecha(r.decididoEl) : '—' }}</dd>
        }
      </dl>
      @if (r.estado === 'devuelto' && r.observacion) {
        <div class="cita"><strong>Observación del tutor</strong><br />{{ r.observacion }}</div>
      }
    </app-tarjeta>
  `,
  styleUrl: '../pantalla.css',
})
export class DocumentoRevision {
  readonly titulo = input.required<string>();
  readonly subtitulo = input('');
  /** La revisión vigente (con la decisión tomada en pantalla, si la hubo). */
  readonly revision = input.required<Revision>();
  /** La revisión tal como se cargó: define los avisos de arriba, que no cambian al decidir. */
  readonly inicial = input.required<Revision>();
  /** «Reporte semanal», «Plan de actividades» o «Informe final». */
  readonly documento = input.required<string>();
  /** Frase que sigue a «validado por … el …». */
  readonly textoValidado = input('');
  readonly filas = input<FilaDocumento[]>([]);

  protected readonly fecha = formatoFecha;
  protected readonly fechaInicial = computed(() => {
    const el = this.inicial().decididoEl;
    return el ? formatoFecha(el) : '';
  });
  protected readonly tipoEstado = computed(() => tipoRevision(this.revision().estado));
  protected readonly textoEstado = computed(() => textoRevision(this.revision().estado));
}
