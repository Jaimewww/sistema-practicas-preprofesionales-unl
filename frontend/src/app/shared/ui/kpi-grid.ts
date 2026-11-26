import { Component, input } from '@angular/core';

/** Rejilla de `<app-kpi>`: cuatro columnas, o tres con `tres`. */
@Component({
  selector: 'app-kpi-grid',
  template: `<ng-content />`,
  host: { '[class.tres]': 'tres()', role: 'group' },
  styles: `
    :host {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      margin: 14px 0;
    }
    :host(.tres) {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
    @media (max-width: 1100px) {
      :host,
      :host(.tres) {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }
  `,
})
export class KpiGrid {
  readonly tres = input(false);
}
