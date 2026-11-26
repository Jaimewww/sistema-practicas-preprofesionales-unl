import { Component, input } from '@angular/core';
import { Params, RouterLink, RouterLinkActive } from '@angular/router';

export interface PestanaItem {
  texto: string;
  enlace: string;
  /** Parámetros de consulta del enlace (`?p=`). */
  parametros?: Params;
  /** Por defecto `true`: solo está activa con la ruta exacta. */
  exacto?: boolean;
}

/** Pestañas de sección con enlaces del router; la activa lleva `aria-current="page"`. */
@Component({
  selector: 'app-pestanas',
  imports: [RouterLink, RouterLinkActive],
  template: `
    <ul class="pestanas" [attr.aria-label]="etiqueta()">
      @for (item of items(); track item.enlace + item.texto) {
        <li>
          <a [routerLink]="item.enlace" [queryParams]="item.parametros" routerLinkActive="activa" ariaCurrentWhenActive="page" [routerLinkActiveOptions]="{ exact: item.exacto ?? true }">{{ item.texto }}</a>
        </li>
      }
    </ul>
  `,
  styles: `
    :host {
      display: block;
    }
    .pestanas {
      display: flex;
      gap: 6px;
      width: max-content;
      max-width: 100%;
      margin: 0 0 var(--espacio-4);
      padding: 5px;
      overflow: auto;
      list-style: none;
      background: var(--color-crema-2);
      border-radius: 14px;
    }
    a {
      display: block;
      padding: 9px 18px;
      font-size: 14.5px;
      font-weight: 600;
      color: var(--color-marino);
      text-decoration: none;
      white-space: nowrap;
      border-radius: 10px;
    }
    a:hover {
      background: var(--color-borde);
    }
    a.activa {
      color: #fff;
      background: var(--color-marino);
    }
  `,
})
export class Pestanas {
  readonly items = input.required<PestanaItem[]>();
  readonly etiqueta = input('Secciones');
}
