import { Component, input } from '@angular/core';

let siguiente = 0;

/**
 * Tarjeta de contenido. `span` (1–12) la hace ocupar esas columnas dentro de `.grilla`.
 * Contenido por defecto = cuerpo; `<div acciones>` va a la derecha del título.
 */
@Component({
  selector: 'app-tarjeta',
  template: `
    <section class="tarjeta" [attr.aria-labelledby]="idTitulo">
      <div class="cabecera">
        <h3 [id]="idTitulo">{{ titulo() }}</h3>
        <div class="acciones"><ng-content select="[acciones]" /></div>
      </div>
      @if (sub()) {
        <p class="sub">{{ sub() }}</p>
      }
      <ng-content />
    </section>
  `,
  host: { '[class]': 'span() ? "span-" + span() : ""' },
  styles: `
    :host {
      display: block;
      min-width: 0;
    }
    .cabecera {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: var(--espacio-3);
    }
    h3 {
      margin: 0;
      font-size: 20px;
      font-weight: 600;
      letter-spacing: -0.01em;
      color: var(--color-marino);
    }
    .acciones:empty {
      display: none;
    }
    .sub {
      margin: var(--espacio-1) 0 0;
      font-size: 14.5px;
      color: var(--color-texto-suave);
    }
    .tarjeta > :not(.cabecera):not(.sub) {
      margin-top: var(--espacio-4);
    }
  `,
})
export class Tarjeta {
  readonly titulo = input.required<string>();
  readonly sub = input('');
  /** Columnas (de 12) que ocupa dentro de `.grilla`. */
  readonly span = input<number>();
  protected readonly idTitulo = `tarjeta-${++siguiente}`;
}
