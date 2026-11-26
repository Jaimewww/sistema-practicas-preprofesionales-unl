import { Component, input } from '@angular/core';

/** Estado vacío: título en negrita y una frase que dice qué hacer. */
@Component({
  selector: 'app-vacio',
  template: `<strong>{{ titulo() }}</strong>{{ texto() }}`,
  styles: `
    :host {
      display: block;
      padding: 28px var(--espacio-3);
      text-align: center;
      color: var(--color-texto-suave);
    }
    strong {
      display: block;
      margin-bottom: var(--espacio-1);
      font-size: 17px;
      color: var(--color-marino);
    }
  `,
})
export class Vacio {
  readonly titulo = input.required<string>();
  readonly texto = input('');
}
