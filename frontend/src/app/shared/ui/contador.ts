import { Component, computed, forwardRef, input, signal } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

/**
 * Contador − / + que también se puede escribir. Es un ControlValueAccessor de número:
 * al escribir emite lo tecleado y al salir del campo (o con − / +) lo ajusta a [min, max].
 */
@Component({
  selector: 'app-contador',
  providers: [{ provide: NG_VALUE_ACCESSOR, useExisting: forwardRef(() => Contador), multi: true }],
  template: `
    <div class="contador">
      <button type="button" class="boton-paso" [attr.aria-label]="'Disminuir ' + etiqueta()" [disabled]="deshabilitado() || enMinimo()" (click)="mover(-1)">−</button>
      <span class="valor">
        <input
          [attr.id]="idControl() || null"
          type="number"
          title="Escriba el valor o use − y +"
          inputmode="numeric"
          [attr.aria-label]="etiqueta()"
          [attr.aria-describedby]="ayudaId() || null"
          [required]="requerido()"
          [min]="min()"
          [max]="max()"
          [step]="paso()"
          [value]="valor() ?? ''"
          [disabled]="deshabilitado()"
          (focus)="$any($event.target).select()"
          (input)="escribir($any($event.target).value)"
          (change)="ajustar()"
          (blur)="alTocar()"
        />
        @if (unidad()) {
          <span class="unidad" aria-hidden="true">{{ unidad() }}</span>
        }
      </span>
      <button type="button" class="boton-paso" [attr.aria-label]="'Aumentar ' + etiqueta()" [disabled]="deshabilitado() || enMaximo()" (click)="mover(1)">+</button>
    </div>
  `,
  styles: `
    :host {
      display: block;
    }
    .contador {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--espacio-3);
      max-width: 420px;
      padding: 10px var(--espacio-4);
      background: #fff;
      border: 1px solid var(--color-borde);
      border-radius: 14px;
      box-shadow: 0 2px 8px rgba(37, 41, 89, 0.08);
    }
    .contador:focus-within {
      outline: 2px solid var(--color-enlace);
      outline-offset: 2px;
    }
    .boton-paso {
      display: grid;
      flex: none;
      place-items: center;
      width: 44px;
      height: 44px;
      padding: 0;
      font: inherit;
      font-size: 26px;
      font-weight: 500;
      line-height: 1;
      color: var(--color-marino);
      background: var(--color-lila);
      border: 0;
      border-radius: 50%;
      cursor: pointer;
      transition: background 0.2s;
    }
    .boton-paso:hover:not(:disabled) {
      background: #d4c9ff;
    }
    .boton-paso:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }
    .valor {
      display: flex;
      flex: 1;
      align-items: baseline;
      justify-content: center;
      gap: 4px;
      padding: 6px 10px;
      cursor: text;
      border-radius: 10px;
      transition: background 0.2s;
    }
    .valor:hover,
    .valor:focus-within {
      background: #f4f1ff;
    }
    .valor:focus-within {
      box-shadow: inset 0 -2px 0 var(--color-enlace);
    }
    input {
      flex: 1;
      width: auto;
      min-width: 3.4ch;
      padding: 0;
      font: inherit;
      font-size: 22px;
      font-weight: 500;
      font-variant-numeric: tabular-nums;
      color: var(--color-marino);
      text-align: center;
      caret-color: var(--color-enlace);
      background: transparent;
      border: 0;
      box-shadow: none;
      outline: none;
      -moz-appearance: textfield;
      appearance: textfield;
    }
    input::-webkit-inner-spin-button,
    input::-webkit-outer-spin-button {
      margin: 0;
      -webkit-appearance: none;
    }
    .unidad {
      font-size: 15px;
      color: var(--color-texto-suave);
    }
  `,
})
export class Contador implements ControlValueAccessor {
  /** Nombre que leen los lectores de pantalla: «Disminuir {etiqueta}», «Aumentar {etiqueta}». */
  readonly etiqueta = input.required<string>();
  readonly min = input(0);
  readonly max = input(999);
  readonly paso = input(1);
  readonly unidad = input('');
  /** `id` del `<input>` interno, para enlazarlo con un `<label for>`. */
  readonly idControl = input('');
  readonly ayudaId = input('');
  readonly requerido = input(false);

  protected readonly valor = signal<number | null>(null);
  protected readonly deshabilitado = signal(false);
  protected readonly enMinimo = computed(() => (this.valor() ?? this.min()) <= this.min());
  protected readonly enMaximo = computed(() => (this.valor() ?? this.min()) >= this.max());

  private alCambiar: (valor: number | null) => void = () => {};
  protected alTocar: () => void = () => {};

  writeValue(valor: number | null): void {
    this.valor.set(valor === null || valor === undefined ? null : Number(valor));
  }
  registerOnChange(fn: (valor: number | null) => void): void {
    this.alCambiar = fn;
  }
  registerOnTouched(fn: () => void): void {
    this.alTocar = fn;
  }
  setDisabledState(deshabilitado: boolean): void {
    this.deshabilitado.set(deshabilitado);
  }

  private limitar(n: number): number {
    return Math.max(this.min(), Math.min(this.max(), n));
  }

  private fijar(n: number | null): void {
    this.valor.set(n);
    this.alCambiar(n);
  }

  /** − / +: parte del valor actual (o del mínimo) y respeta [min, max]. */
  mover(direccion: 1 | -1): void {
    const actual = this.valor() || this.min();
    this.fijar(this.limitar(actual + direccion * this.paso()));
  }

  /** Escribir: emite lo tecleado sin ajustarlo, para no estorbar mientras se teclea. */
  protected escribir(texto: string): void {
    this.fijar(texto.trim() === '' ? null : Number(texto));
  }

  /** Al terminar de escribir: lo vacío o inválido vuelve al mínimo y todo cabe en [min, max]. */
  protected ajustar(): void {
    const n = this.valor();
    this.fijar(this.limitar(n === null || Number.isNaN(n) ? this.min() : n));
  }
}
