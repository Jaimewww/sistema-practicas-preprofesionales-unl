import { DatePipe } from '@angular/common';
import { Component, computed, DestroyRef, inject, input, signal } from '@angular/core';
import { takeUntilDestroyed, toObservable, toSignal } from '@angular/core/rxjs-interop';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { catchError, map, of, startWith, switchMap } from 'rxjs';
import { estadoDeError } from '../../../core/errores';
import { cargando, exito, inicial, type EstadoUi } from '../../../core/estado-ui';
import type { EstadoReporte, HorasPractica, Reporte } from '../reporte.model';
import { ReportesApi } from '../reportes.api';

/** Texto que ve la persona para cada estado del reporte. */
const ETIQUETA_ESTADO: Record<EstadoReporte, string> = {
  en_revision: 'en revisión',
  validado: 'validado',
  devuelto: 'devuelto',
};

/** Límites de los contadores. */
const LIMITES = {
  semana: { min: 1, max: 52 },
  horas_reportadas: { min: 1, max: 168 },
} as const;

/**
 * Pantalla E4: registrar horas semanales (F-002).     RESPONSABLE: Melissa
 *
 * Solo usa ReportesApi y EstadoUi: no sabe si detrás hay el mock o el servicio
 * real, y los textos de error vienen de `estado().mensaje`.
 */
@Component({
  selector: 'app-registrar-reporte',
  imports: [ReactiveFormsModule, DatePipe],
  templateUrl: './registrar-reporte.html',
  styleUrl: './registrar-reporte.css',
})
export class RegistrarReporte {
  private readonly reportesApi = inject(ReportesApi);

  readonly practicaId = input(1);
  readonly estado = signal<EstadoUi<Reporte>>(inicial());
  readonly estadoHoras = signal<EstadoUi<HorasPractica>>(inicial());

  /** Sube cada vez que hay que volver a pedir las horas (tras un 201). */
  private readonly recarga = signal(0);

  readonly form = inject(NonNullableFormBuilder).group({
    semana: [1, Validators.required],
    horas_reportadas: [0, Validators.required],
  });

  /** Valores actuales de los contadores (para deshabilitar − / + en los límites). */
  private readonly valores = toSignal(this.form.valueChanges, { initialValue: this.form.getRawValue() });

  constructor() {
    const pedido = computed(() => ({ id: this.practicaId(), recarga: this.recarga() }));
    toObservable(pedido)
      .pipe(
        switchMap(({ id }) =>
          this.reportesApi.horas(id).pipe(
            map((datos) => exito(datos)),
            catchError((e: unknown) => of(estadoDeError<HorasPractica>(e))),
            startWith(cargando<HorasPractica>()),
          ),
        ),
        takeUntilDestroyed(inject(DestroyRef)),
      )
      .subscribe((estado) => this.estadoHoras.set(estado));
  }

  /** Contador − / +: mueve el control dentro de [min, max]. */
  paso(control: 'semana' | 'horas_reportadas', delta: number): void {
    const { min, max } = LIMITES[control];
    const actual = Number(this.form.controls[control].value) || min;
    this.form.controls[control].setValue(Math.max(min, Math.min(max, actual + delta)));
  }

  enLimite(control: 'semana' | 'horas_reportadas', lado: 'min' | 'max'): boolean {
    const valor = Number(this.valores()[control]);
    const limite = LIMITES[control][lado];
    return lado === 'min' ? valor <= limite : valor >= limite;
  }

  etiquetaEstado(estado: EstadoReporte): string {
    return ETIQUETA_ESTADO[estado];
  }

  /** Ancho (en %) de un tramo de la barra; la escala son las horas requeridas. */
  porcentaje(horas: number, requeridas: number): number {
    return requeridas > 0 ? Math.min(100, (horas / requeridas) * 100) : 0;
  }

  /** El tramo «en revisión» empieza donde terminan las validadas y no pasa del 100 %. */
  porcentajeRevision(h: HorasPractica): number {
    const validadas = this.porcentaje(h.horas_validadas, h.horas_requeridas);
    return Math.min(100 - validadas, this.porcentaje(h.horas_en_revision, h.horas_requeridas));
  }

  enviar(): void {
    this.estado.set(cargando());
    this.reportesApi.crear(this.practicaId(), this.form.getRawValue()).subscribe({
      next: (reporte) => {
        this.estado.set(exito(reporte));
        this.recarga.update((n) => n + 1);
      },
      error: (e: unknown) => this.estado.set(estadoDeError(e)),
    });
  }
}
