import { Component, input } from '@angular/core';

export type TipoInsignia = 'ok' | 'warn' | 'bad' | 'info';

/** Píldora de estado: ícono + texto; el color solo refuerza (nunca es la única señal). */
@Component({
  selector: 'app-insignia',
  template: `
    @switch (tipo()) {
      @case ('ok') {
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12l5 5 9-10" /></svg>
      }
      @case ('warn') {
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>
      }
      @case ('bad') {
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l10 18H2z" /><path d="M12 10v5M12 18h.01" /></svg>
      }
      @default {
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 8h.01" /></svg>
      }
    }<span>{{ texto() }}</span>
  `,
  host: { '[class]': '"insignia insignia--" + tipo()' },
  styles: `
    :host {
      display: inline-flex;
      align-items: center;
      gap: var(--espacio-1);
      padding: 2px var(--espacio-3);
      font-size: 12.5px;
      font-weight: 600;
      white-space: nowrap;
      border-radius: 999px;
    }
    svg {
      flex: none;
      width: 15px;
      height: 15px;
    }
    :host(.insignia--ok) {
      color: var(--color-exito);
      background: var(--color-exito-fondo);
    }
    :host(.insignia--warn) {
      color: var(--color-aviso);
      background: var(--color-aviso-fondo);
    }
    :host(.insignia--bad) {
      color: var(--color-error);
      background: var(--color-error-fondo);
    }
    :host(.insignia--info) {
      color: var(--color-info);
      background: var(--color-info-fondo);
    }
  `,
})
export class Insignia {
  readonly tipo = input<TipoInsignia>('info');
  readonly texto = input.required<string>();
}
