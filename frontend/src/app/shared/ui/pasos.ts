import { Component, input } from '@angular/core';

export type EstadoPaso = 'done' | 'bad' | 'now' | 'pendiente';

export interface PasoItem {
  estado: EstadoPaso;
  titulo: string;
  detalle?: string;
}

const SIMBOLO: Record<EstadoPaso, string> = { done: '✓', bad: '!', now: '●', pendiente: '·' };
const TEXTO: Record<EstadoPaso, string> = { done: 'Completado', bad: 'Con observación', now: 'En curso', pendiente: 'Pendiente' };

/** Línea de seguimiento: cada paso lleva símbolo y texto oculto, no solo color. */
@Component({
  selector: 'app-pasos',
  template: `
    <ol class="pasos">
      @for (paso of pasos(); track $index) {
        <li [class]="paso.estado">
          <span class="punto" aria-hidden="true">{{ simbolo(paso.estado) }}</span>
          <div>
            <strong>{{ paso.titulo }} <span class="sr-only">({{ texto(paso.estado) }})</span></strong>
            @if (paso.detalle) {
              <span class="detalle">{{ paso.detalle }}</span>
            }
          </div>
        </li>
      }
    </ol>
  `,
  styles: `
    .pasos {
      display: grid;
      margin: 14px 0 0;
      padding: 0;
      list-style: none;
    }
    li {
      position: relative;
      display: grid;
      grid-template-columns: 28px 1fr;
      gap: var(--espacio-3);
      padding-bottom: var(--espacio-4);
      font-size: 14px;
    }
    li::before {
      content: '';
      position: absolute;
      top: 28px;
      bottom: 0;
      left: 13px;
      width: 2px;
      background: var(--color-borde);
    }
    li:last-child::before {
      display: none;
    }
    .punto {
      display: grid;
      place-items: center;
      width: 28px;
      height: 28px;
      font-size: 13px;
      font-weight: 700;
      color: var(--color-texto);
      background: var(--horas-pista);
      border-radius: 50%;
    }
    .done .punto {
      color: #fff;
      background: var(--color-exito);
    }
    .bad .punto {
      color: #fff;
      background: var(--color-error);
    }
    .now .punto {
      color: #fff;
      background: var(--color-marino);
      box-shadow: 0 0 0 4px var(--color-lila);
    }
    strong {
      display: block;
      color: var(--color-marino);
    }
    .detalle {
      color: var(--color-texto-suave);
    }
  `,
})
export class Pasos {
  readonly pasos = input.required<PasoItem[]>();
  protected simbolo(e: EstadoPaso): string {
    return SIMBOLO[e];
  }
  protected texto(e: EstadoPaso): string {
    return TEXTO[e];
  }
}
