import { Component, ElementRef, inject, input, output, signal, viewChild } from '@angular/core';
import { ApiError } from '../../../core/api/envelope';
import { mensajeDeError } from '../../../core/errores';
import { Aviso, Tarjeta } from '../../../shared/ui';
import { TutorAcademicoApi } from '../tutor-academico.api';
import type { Revision } from '../tutor-academico.model';

/** Error que se pinta cuando se pide devolver sin observación (y que la API también exige). */
export const ERROR_SIN_OBSERVACION = 'La devolución exige una observación';

/**
 * Tarjeta «Decisión» de T2: observación, «Validar» y «Devolver». Devolver exige la observación;
 * sin ella no se registra nada y el documento sigue en revisión. Al decidir entrega la revisión nueva.
 */
@Component({
  selector: 'app-decision-revision',
  imports: [Tarjeta, Aviso],
  host: { style: 'display: contents' }, // la tarjeta interior es la que ocupa columnas en .grilla
  template: `
    <app-tarjeta titulo="Decisión" [span]="12">
      <div class="cuerpo">
        @switch (resultado()) {
          @case ('validar') {
            <app-aviso tipo="info"><strong>{{ okValidar().titulo }}</strong> {{ okValidar().texto }}</app-aviso>
          }
          @case ('devolver') {
            <app-aviso tipo="info"><strong>{{ okDevolver().titulo }}</strong> {{ okDevolver().texto }}</app-aviso>
          }
        }
        @if (falloApi()) {
          <app-aviso tipo="bad">{{ falloApi() }}</app-aviso>
        }
        <div class="campo" [class.campo--error]="error()">
          <label [for]="idObservacion">Observación</label>
          <textarea
            #observacionEl
            [id]="idObservacion"
            rows="4"
            placeholder="Indique qué debe corregir el estudiante"
            [value]="observacion()"
            [disabled]="cerrado()"
            [attr.aria-invalid]="error() ? 'true' : null"
            [attr.aria-describedby]="error() ? idObservacion + '-error ' + idObservacion + '-ayuda' : idObservacion + '-ayuda'"
            (input)="escribir($any($event.target).value)"
          ></textarea>
          @if (error()) {
            <p class="campo__mensaje" [id]="idObservacion + '-error'" role="alert">{{ errorTexto }}</p>
          }
          <p class="campo__mensaje" [id]="idObservacion + '-ayuda'">Obligatoria para devolver; para validar es opcional.</p>
        </div>
        @if (error()) {
          <p class="texto">No se registró la decisión: el elemento sigue en su bandeja de pendientes, en revisión.</p>
        }
        <div class="acciones-fila">
          <button type="button" class="boton" [disabled]="cerrado() || enviando()" (click)="decidir('validar')">Validar</button>
          <button type="button" class="boton-secundario" [disabled]="cerrado() || enviando()" (click)="decidir('devolver')">Devolver</button>
        </div>
      </div>
    </app-tarjeta>
  `,
  styleUrl: '../pantalla.css',
  styles: `
    textarea {
      width: 100%;
      min-height: 110px;
      padding: var(--espacio-3) 14px;
      font: inherit;
      color: var(--color-texto);
      resize: vertical;
      background: #fff;
      border: 1px solid #7b838c;
      border-radius: 10px;
    }
    textarea:focus {
      outline: none;
      border-color: var(--color-enlace);
      box-shadow: 0 0 0 3px rgba(0, 80, 158, 0.18);
    }
    textarea:disabled {
      color: var(--color-texto-suave);
      cursor: not-allowed;
      background: #f1ede2;
      border-color: #bdb8a8;
    }
    .campo {
      display: grid;
      gap: 6px;
    }
    .campo label {
      font-weight: 600;
      color: var(--color-marino);
    }
    .campo__mensaje {
      margin: 0;
      font-size: 13px;
      color: var(--color-texto-suave);
    }
    .campo--error label,
    .campo--error [role='alert'] {
      font-weight: 600;
      color: var(--color-error);
    }
    .campo--error textarea {
      background: #fff8f8;
      border-color: var(--color-error);
    }
  `,
})
export class DecisionRevision {
  private static siguiente = 0;
  private readonly api = inject(TutorAcademicoApi);
  private readonly campo = viewChild<ElementRef<HTMLTextAreaElement>>('observacionEl');

  readonly revision = input.required<Revision>();
  /** Aviso al validar (título en negrita y frase). */
  readonly okValidar = input.required<{ titulo: string; texto: string }>();
  readonly okDevolver = input.required<{ titulo: string; texto: string }>();
  /** Se emite con la revisión ya decidida. */
  readonly decidida = output<Revision>();

  protected readonly idObservacion = `observacion-${++DecisionRevision.siguiente}`;
  protected readonly errorTexto = ERROR_SIN_OBSERVACION;
  protected readonly observacion = signal('');
  protected readonly error = signal(false);
  protected readonly falloApi = signal('');
  protected readonly enviando = signal(false);
  protected readonly resultado = signal<'validar' | 'devolver' | null>(null);
  protected readonly cerrado = () => this.resultado() !== null;

  protected escribir(texto: string): void {
    this.observacion.set(texto);
    if (texto.trim()) this.error.set(false);
  }

  protected decidir(accion: 'validar' | 'devolver'): void {
    this.falloApi.set('');
    if (accion === 'devolver' && !this.observacion().trim()) {
      this.error.set(true);
      this.campo()?.nativeElement.focus();
      return;
    }
    this.error.set(false);
    this.enviando.set(true);
    const r = this.revision();
    this.api.decidir(r.tipo, r.clave, accion, this.observacion()).subscribe({
      next: (revision) => {
        this.enviando.set(false);
        this.resultado.set(accion);
        this.decidida.emit(revision);
      },
      error: (e: unknown) => {
        this.enviando.set(false);
        if (e instanceof ApiError && e.campos['observacion']) {
          this.error.set(true);
        } else {
          this.falloApi.set(e instanceof ApiError ? mensajeDeError(e) : 'No se pudo registrar la decisión.');
        }
      },
    });
  }
}
