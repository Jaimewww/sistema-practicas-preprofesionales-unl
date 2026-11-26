import { Component, computed, input } from '@angular/core';

/** Barra de horas tipo bala: validadas, en revisión y marca opcional de las esperadas a la fecha. */
@Component({
  selector: 'app-barra-horas',
  template: `
    <div class="barra" role="img" [attr.aria-label]="etiquetaAria()">
      <span class="v" [style.width.%]="pv()"></span>
      <span class="r" [style.left.%]="pv()" [style.width.%]="pr()"></span>
      @if (pe() !== null) {
        <span class="e" [style.left.%]="pe()"></span>
      }
    </div>
    @if (leyenda()) {
      <ul class="leyenda">
        <li><span class="sw sw--v"></span>Validadas: <span class="cifra">{{ validadas() }} h</span></li>
        <li><span class="sw sw--r"></span>En revisión: <span class="cifra">{{ enRevision() }} h</span></li>
        @if (esperadas() !== undefined) {
          <li><span class="sw sw--e"></span>Esperadas: <span class="cifra">{{ esperadas() }} h</span></li>
        }
        <li>Requeridas: <span class="cifra">{{ requeridas() }} h</span></li>
      </ul>
    }
  `,
  styles: `
    :host {
      display: block;
    }
    .barra {
      position: relative;
      height: 14px;
      margin: var(--espacio-5) 0 var(--espacio-2);
      background: var(--horas-pista);
      border-radius: 999px;
    }
    .v,
    .r {
      position: absolute;
      top: 0;
      bottom: 0;
    }
    .v {
      left: 0;
      background: var(--horas-validadas);
      border-radius: 999px 0 0 999px;
    }
    .r {
      background: repeating-linear-gradient(45deg, var(--color-dorado), var(--color-dorado) 6px, var(--horas-revision) 6px, var(--horas-revision) 12px);
    }
    .e {
      position: absolute;
      top: -6px;
      bottom: -6px;
      width: 3px;
      background: var(--color-marino);
      border-radius: 3px;
    }
    .leyenda {
      display: flex;
      flex-wrap: wrap;
      gap: 6px 22px;
      margin: 0;
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
      display: inline-block;
      width: 14px;
      height: 14px;
      border-radius: 4px;
    }
    .sw--v {
      background: var(--horas-validadas);
    }
    .sw--r {
      background: var(--color-dorado);
    }
    .sw--e {
      width: 4px;
      background: var(--color-marino);
    }
    .cifra {
      font-variant-numeric: tabular-nums;
    }
  `,
})
export class BarraHoras {
  readonly validadas = input.required<number>();
  readonly enRevision = input.required<number>();
  readonly requeridas = input.required<number>();
  /** Horas esperadas a la fecha; si falta, no se dibuja la marca. */
  readonly esperadas = input<number>();
  /** Muestra la leyenda bajo la barra. */
  readonly leyenda = input(true);

  private pct(horas: number): number {
    const requeridas = this.requeridas();
    return requeridas > 0 ? Math.max(0, Math.min(100, (horas / requeridas) * 100)) : 0;
  }

  protected readonly pv = computed(() => this.pct(this.validadas()));
  /** El tramo «en revisión» empieza donde terminan las validadas y no pasa del 100 %. */
  protected readonly pr = computed(() => Math.min(100 - this.pv(), this.pct(this.enRevision())));
  protected readonly pe = computed(() => {
    const esperadas = this.esperadas();
    return esperadas === undefined ? null : this.pct(esperadas);
  });
  protected readonly etiquetaAria = computed(() => {
    const base = `${this.validadas()} h validadas y ${this.enRevision()} h en revisión de ${this.requeridas()} h requeridas`;
    const esperadas = this.esperadas();
    return esperadas === undefined ? base : `${base}. Esperadas a la fecha: ${esperadas} h`;
  });
}
