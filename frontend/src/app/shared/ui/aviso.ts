import { Component, computed, input } from '@angular/core';

export type TipoAviso = 'ok' | 'warn' | 'bad' | 'info';

/** Aviso en línea: ícono + contenido; `bad` se anuncia como alerta, el resto como estado. */
@Component({
  selector: 'app-aviso',
  template: `
    @switch (tipo()) {
      @case ('ok') {
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12l5 5 9-10" /></svg>
      }
      @case ('warn') {
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>
      }
      @case ('bad') {
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l10 18H2z" /><path d="M12 10v5M12 18h.01" /></svg>
      }
      @default {
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 8h.01" /></svg>
      }
    }
    <div class="contenido"><ng-content /></div>
  `,
  host: {
    '[class]': '"aviso-" + tipo()',
    '[attr.role]': 'rol()',
  },
  styles: `
    :host {
      display: flex;
      gap: var(--espacio-3);
      padding: 14px var(--espacio-4);
      color: var(--color-texto);
      border: 1px solid;
      border-radius: var(--radio);
    }
    svg {
      flex: none;
      width: 22px;
      height: 22px;
    }
    .contenido {
      min-width: 0;
    }
    :host(.aviso-ok) {
      background: var(--color-exito-fondo);
      border-color: var(--color-exito);
    }
    :host(.aviso-warn) {
      background: var(--color-aviso-fondo);
      border-color: var(--color-aviso);
    }
    :host(.aviso-bad) {
      background: var(--color-error-fondo);
      border-color: var(--color-error);
    }
    :host(.aviso-info) {
      background: var(--color-info-fondo);
      border-color: var(--color-info);
    }
  `,
})
export class Aviso {
  readonly tipo = input<TipoAviso>('info');
  protected readonly rol = computed(() => (this.tipo() === 'bad' ? 'alert' : 'status'));
}
