import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';

export interface EstadoEjemplo {
  clave: string;
  texto: string;
}

/**
 * «Estados de ejemplo» del prototipo: enlaces que cambian la variante con `?r=` o `?p=` para recorrer
 * los estados de la pantalla. El activo lleva `aria-current`.
 */
@Component({
  selector: 'app-estados-ejemplo',
  imports: [RouterLink],
  template: `
    <nav class="demo-vistas" aria-label="Estados de ejemplo">
      <span>Estados de ejemplo:</span>
      @for (e of estados(); track e.clave) {
        <a [routerLink]="[]" [queryParams]="parametros(e.clave)" [attr.aria-current]="e.clave === activo() ? 'true' : null">{{ e.texto }}</a>
      }
    </nav>
  `,
  styleUrl: '../pantalla.css',
})
export class EstadosEjemplo {
  readonly parametro = input.required<string>();
  readonly estados = input.required<EstadoEjemplo[]>();
  readonly activo = input.required<string>();

  protected parametros(clave: string): Record<string, string> {
    return { [this.parametro()]: clave };
  }
}
