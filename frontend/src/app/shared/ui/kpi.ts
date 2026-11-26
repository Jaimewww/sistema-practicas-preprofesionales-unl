import { Component, input } from '@angular/core';

/** Indicador: etiqueta, valor grande y nota; `alerta` pinta el valor en rojo. */
@Component({
  selector: 'app-kpi',
  template: `
    <small>{{ etiqueta() }}</small>
    <strong>{{ valor() }}</strong>
    @if (nota()) {
      <span>{{ nota() }}</span>
    }
  `,
  host: { '[class.alerta]': 'alerta()' },
  styles: `
    :host {
      display: block;
      padding: var(--espacio-3) var(--espacio-4);
      background: var(--color-crema-2);
      border: 1px solid var(--color-borde);
      border-radius: 14px;
    }
    small {
      display: block;
      font-size: 12px;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      color: var(--color-texto-suave);
    }
    strong {
      display: block;
      font-size: 30px;
      font-weight: 600;
      line-height: 1.2;
      font-variant-numeric: tabular-nums;
      color: var(--color-marino);
    }
    span {
      font-size: 13px;
      color: var(--color-texto-suave);
    }
    :host(.alerta) strong {
      color: var(--color-error);
    }
  `,
})
export class Kpi {
  readonly etiqueta = input.required<string>();
  readonly valor = input.required<string | number>();
  readonly nota = input('');
  readonly alerta = input(false);
}
