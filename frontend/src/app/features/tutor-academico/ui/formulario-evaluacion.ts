import { Component, computed, inject, input, OnInit, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ApiError } from '../../../core/api/envelope';
import { mensajeDeError } from '../../../core/errores';
import { formatoFecha } from '../../../core/demo';
import { Aviso, Contador, Insignia } from '../../../shared/ui';
import { TutorAcademicoApi } from '../tutor-academico.api';
import type { DatosEvaluacion, ResultadoEvaluacion } from '../tutor-academico.model';

/** Desde este porcentaje la práctica queda aprobada (RF-17, Art. 339). */
export const MINIMO_APROBACION = 70;

/**
 * Formulario de la evaluación final (T5): el porcentaje de desempeño con su resultado en vivo.
 * «Guardar» sin los informes exigidos no registra nada y lista lo que falta.
 */
@Component({
  selector: 'app-formulario-evaluacion',
  imports: [ReactiveFormsModule, RouterLink, Aviso, Contador, Insignia],
  template: `
    @let p = datos().practica;
    <p class="texto">
      {{ p.estudiante }}. Práctica {{ p.tipo }}: {{ p.tipo === 'laboral' ? 'pasantía' : 'proyecto de vinculación' }} en {{ p.entidad }}{{ p.entidad.endsWith('.') ? '' : '.' }} Período {{ p.periodo }}.
    </p>
    <div class="cuerpo">
      @if (p.informeFinal?.estado === 'validado' && p.informeFinal?.validadoEl) {
        <ul class="requisitos">
          <li><app-insignia tipo="ok" texto="Cumplido" /><span>Informe final del estudiante: <strong>validado</strong> el {{ fecha(p.informeFinal!.validadoEl!) }}.</span></li>
          @if (p.informeExterno) {
            <li><app-insignia tipo="ok" texto="Cumplido" /><span>Informe externo del tutor de la entidad: <strong>registrado</strong> el {{ fecha(p.informeExterno.registradoEl) }}.</span></li>
          }
        </ul>
      } @else if (p.informeExterno) {
        <ul class="requisitos">
          <li><app-insignia tipo="ok" texto="Cumplido" /><span>Informe externo del tutor de la entidad: <strong>registrado</strong> el {{ fecha(p.informeExterno.registradoEl) }}.</span></li>
        </ul>
      }
      @if (datos().faltantes.length) {
        <app-aviso tipo="warn">Para registrar la evaluación final falta {{ datos().faltantes.join(' y ') }}.</app-aviso>
      }
      @if (p.estado !== 'en_revision_final') {
        <app-aviso tipo="warn">La práctica está «{{ estadoTexto() }}»: la evaluación final se habilita cuando llega a «En revisión final».</app-aviso>
      }
      @if (errores().length) {
        <div class="resumen-error" role="alert">
          <p>No se pudo registrar la evaluación. Corrija lo siguiente:</p>
          <ul>
            @for (m of errores(); track m) {
              <li>{{ m }}</li>
            }
          </ul>
        </div>
      }
      @if (registrada(); as r) {
        <app-aviso tipo="info">
          <strong>Evaluación final registrada</strong> por {{ r.registradoPor }} el {{ fecha(r.registradoEl) }}. Desempeño {{ r.porcentaje }} %: {{ r.resultado === 'aprobada' ? 'aprobada' : 'no aprobada' }}. La coordinación ya puede cerrar la práctica.
        </app-aviso>
      }
      <div class="campo">
        <label [for]="id()">Desempeño <span class="req" aria-hidden="true">*</span></label>
        <app-contador etiqueta="Desempeño" [idControl]="id()" [ayudaId]="id() + '-ayuda'" [min]="0" [max]="100" unidad="%" [requerido]="true" [formControl]="control" />
        <p class="campo__mensaje" [id]="id() + '-ayuda'">Porcentaje de 0 a 100. La práctica queda «aprobada» desde {{ minimo }} % y «no aprobada» por debajo (Art. 339).</p>
      </div>
      <div class="medidor" [class.ok]="aprobada()" role="img" [attr.aria-label]="'Porcentaje de desempeño: ' + valor() + ' %'">
        <span class="g" [style.width.%]="valor()"></span><span class="u"></span>
      </div>
      <div class="resultado">
        <strong>Resultado:</strong>
        <span class="resultado" aria-live="polite">
          <app-insignia [tipo]="aprobada() ? 'ok' : 'bad'" [texto]="aprobada() ? 'Aprobada' : 'No aprobada'" />
          <span>{{ valor() }} % {{ aprobada() ? '(desde ' + minimo + ' % se aprueba)' : '(por debajo de ' + minimo + ' %)' }}</span>
        </span>
      </div>
      <div class="acciones-fila">
        <button type="button" class="boton" [disabled]="registrada() || guardando()" (click)="guardar()">Guardar</button>
        <a class="boton-secundario" routerLink="/tutor-academico/practica" [queryParams]="{ p: p.id }">Cancelar</a>
      </div>
    </div>
  `,
  styleUrl: '../pantalla.css',
})
export class FormularioEvaluacion implements OnInit {
  private readonly api = inject(TutorAcademicoApi);
  readonly datos = input.required<DatosEvaluacion>();

  protected readonly minimo = MINIMO_APROBACION;
  protected readonly fecha = formatoFecha;
  protected readonly control = new FormControl<number | null>(null);
  private readonly bruto = toSignal(this.control.valueChanges, { initialValue: null });
  /** Lo escrito, llevado a [0, 100] para el medidor y el resultado. */
  protected readonly valor = computed(() => Math.max(0, Math.min(100, Number(this.bruto()) || 0)));
  protected readonly aprobada = computed(() => this.valor() >= MINIMO_APROBACION);
  protected readonly errores = signal<string[]>([]);
  protected readonly guardando = signal(false);
  protected readonly registrada = signal<ResultadoEvaluacion | null>(null);
  protected readonly id = computed(() => `porcentaje-${this.datos().practica.id}`);
  protected readonly estadoTexto = computed(() => ({ asignada: 'Asignada', en_curso: 'En curso', suspendida: 'Suspendida', cancelada: 'Cancelada', cerrada: 'Cerrada', en_revision_final: 'En revisión final' })[this.datos().practica.estado]);

  ngOnInit(): void {
    const ya = this.datos().evaluacion;
    this.control.setValue(this.datos().porcentajeInicial);
    if (ya) {
      this.registrada.set({ porcentaje: ya.porcentaje, resultado: ya.resultado, registradoPor: ya.registradoPor, registradoEl: ya.registradoEl });
      this.control.disable();
    }
  }

  protected guardar(): void {
    this.errores.set([]);
    this.guardando.set(true);
    this.api.registrarEvaluacion(this.datos().practica.id, this.valor()).subscribe({
      next: (r) => {
        this.guardando.set(false);
        this.registrada.set(r);
        this.control.disable();
      },
      error: (e: unknown) => {
        this.guardando.set(false);
        const campos = e instanceof ApiError ? Object.values(e.campos).flat() : [];
        this.errores.set(campos.length ? campos : [e instanceof ApiError ? mensajeDeError(e) : 'No se pudo registrar la evaluación.']);
      },
    });
  }
}

