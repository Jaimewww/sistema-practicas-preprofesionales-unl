import { Component, computed, input } from '@angular/core';
import { ESTADO_REPORTE, TOTAL_SEMANAS } from '../../../core/demo';
import type { EstadoReporte, ReporteSemanal } from '../../../core/demo';

type EstadoSemana = EstadoReporte | 'futura';

interface Celda {
  semana: number;
  estado: EstadoSemana;
  ahora: boolean;
  texto: string;
}

const FORMA: Record<EstadoSemana, string> = { validado: '✓', en_revision: '…', devuelto: '!', sin_reporte: '✕', futura: '–' };
const LEYENDA: ReadonlyArray<{ estado: EstadoSemana; texto: string }> = [
  { estado: 'validado', texto: 'Validado' },
  { estado: 'en_revision', texto: 'En revisión' },
  { estado: 'devuelto', texto: 'Devuelto' },
  { estado: 'sin_reporte', texto: 'Sin reporte' },
  { estado: 'futura', texto: 'Futura' },
];

/** Las 16 semanas de la práctica: cada celda lleva número, símbolo y texto oculto, no solo color. */
@Component({
  selector: 'app-franja-semanas',
  template: `
    <ol class="semanas" aria-label="Estado de cada semana">
      @for (celda of celdas(); track celda.semana) {
        <li [class.ahora]="celda.ahora">
          <span class="d" [class]="'d ' + celda.estado">
            <span class="sr-only">Semana {{ celda.semana }}: {{ celda.texto }}{{ celda.ahora ? ' (semana actual)' : '' }}</span>
            <span class="num" aria-hidden="true">{{ celda.semana }}</span>
            <span class="forma" aria-hidden="true">{{ forma(celda.estado) }}</span>
          </span>
        </li>
      }
    </ol>
    <ul class="leyenda">
      @for (item of leyenda; track item.estado) {
        <li><span class="sw" [class]="'sw ' + item.estado" aria-hidden="true">{{ forma(item.estado) }}</span>{{ item.texto }}</li>
      }
    </ul>
  `,
  styles: `
    :host {
      display: block;
    }
    .semanas {
      display: grid;
      grid-template-columns: repeat(16, minmax(0, 1fr));
      gap: 6px;
      margin: 14px 0 6px;
      padding: 0;
      list-style: none;
    }
    .d {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 40px;
      font-size: 12px;
      font-weight: 700;
      line-height: 1.1;
      color: #fff;
      border: 2px solid transparent;
      border-radius: 10px;
    }
    .forma {
      font-size: 11px;
    }
    .validado {
      background: var(--color-exito);
    }
    .en_revision {
      background: var(--estado-revision);
    }
    .devuelto {
      background: var(--color-error);
    }
    .sin_reporte {
      color: var(--color-error);
      background: #fff;
      border: 2px dashed var(--color-error);
    }
    .futura {
      color: var(--color-texto-suave);
      background: var(--horas-pista);
    }
    .ahora .d {
      box-shadow:
        0 0 0 3px #fff,
        0 0 0 6px var(--color-marino);
    }
    .leyenda {
      display: flex;
      flex-wrap: wrap;
      gap: 6px 22px;
      margin: var(--espacio-2) 0 0;
      padding: 0;
      font-size: 14px;
      list-style: none;
    }
    .leyenda li {
      display: flex;
      align-items: center;
      gap: var(--espacio-2);
    }
    .sw {
      display: inline-grid;
      place-items: center;
      width: 18px;
      height: 18px;
      font-size: 11px;
      font-weight: 700;
      color: #fff;
      border: 2px solid transparent;
      border-radius: 5px;
    }
    .sw.sin_reporte {
      color: var(--color-error);
    }
    .sw.futura {
      color: var(--color-texto-suave);
    }
    @media (max-width: 1100px) {
      .semanas {
        grid-template-columns: repeat(8, minmax(0, 1fr));
      }
    }
  `,
})
export class FranjaSemanas {
  readonly reportes = input.required<ReporteSemanal[]>();
  readonly semanaActual = input.required<number>();
  readonly total = input(TOTAL_SEMANAS);

  protected readonly leyenda = LEYENDA;
  protected readonly forma = (estado: EstadoSemana): string => FORMA[estado];

  protected readonly celdas = computed<Celda[]>(() => {
    const porSemana = new Map(this.reportes().map((r) => [r.semana, r.estado]));
    return Array.from({ length: this.total() }, (_, i) => {
      const semana = i + 1;
      const estado: EstadoSemana = porSemana.get(semana) ?? 'futura';
      return { semana, estado, ahora: semana === this.semanaActual(), texto: estado === 'futura' ? 'Futura' : ESTADO_REPORTE[estado] };
    });
  });
}
