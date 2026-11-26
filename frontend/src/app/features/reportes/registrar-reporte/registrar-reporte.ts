import { DatePipe } from '@angular/common';
import { Component, computed, DestroyRef, inject, input, signal } from '@angular/core';
import { takeUntilDestroyed, toObservable } from '@angular/core/rxjs-interop';
import { NonNullableFormBuilder, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { catchError, map, of, startWith, switchMap } from 'rxjs';
import { accionDeError, estadoDeError } from '../../../core/errores';
import { mensajesDeControl, validarHoras, validarSemana } from '../../../core/validacion';
import { cargando, exito, inicial, type EstadoUi } from '../../../core/estado-ui';
import type { EstadoReporte, HorasPractica, Reporte } from '../reporte.model';
import { Contador } from '../../../shared/ui';
import { ReportesApi } from '../reportes.api';

/** Texto que ve la persona para cada estado del reporte. */
const ETIQUETA_ESTADO: Record<EstadoReporte, string> = {
  en_revision: 'en revisión',
  validado: 'validado',
  devuelto: 'devuelto',
};

/**
 * Pantalla E4: registrar horas semanales (F-002).     RESPONSABLE: Melissa
 *
 * Solo usa ReportesApi y EstadoUi: no sabe si detrás hay el mock o el servicio
 * real, y los textos de error vienen de `estado().mensaje`.
 */
@Component({
  selector: 'app-registrar-reporte',
  imports: [ReactiveFormsModule, DatePipe, Contador],
  templateUrl: './registrar-reporte.html',
  styleUrl: './registrar-reporte.css',
})
export class RegistrarReporte {
  private readonly reportesApi = inject(ReportesApi);
  private readonly router = inject(Router);

  readonly practicaId = input(1);
  /** Tope de horas por semana si la práctica es ayudantía (10); null si no aplica. */
  readonly horasMaximas = input<number | null>(null);
  readonly estado = signal<EstadoUi<Reporte>>(inicial());
  readonly estadoHoras = signal<EstadoUi<HorasPractica>>(inicial());

  /** Sube cada vez que hay que volver a pedir las horas (tras un 201). */
  private readonly recarga = signal(0);

  readonly form = inject(NonNullableFormBuilder).group({
    semana: [1, validarSemana()],
    horas_reportadas: [0, validarHoras(() => this.horasMaximas())],
  });

  /** Acción que pide el último error del servidor (ACD 6 §5). */
  readonly accion = computed(() => {
    const e = this.estado();
    return e.tipo === 'error' ? accionDeError(e.error) : 'ninguna';
  });

  /** Sin permiso o con la práctica fuera de curso no tiene sentido enviar. */
  readonly envioBloqueado = computed(
    () => this.accion() === 'deshabilitar_envio' || this.accion() === 'ocultar_accion',
  );
  readonly ocultarAccion = computed(() => this.accion() === 'ocultar_accion');
  readonly puedeReintentar = computed(() => this.accion() === 'reintentar');
  readonly volverAlSelector = computed(() => this.accion() === 'volver_al_selector');

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

  /**
   * Mensajes de un campo: los del validador local (si ya lo tocaron o se intentó enviar)
   * y, si no, los que devolvió el servidor en un 400 (`error.campos`).
   */
  erroresDe(campo: 'semana' | 'horas_reportadas'): string[] {
    const control = this.form.controls[campo];
    if (control.invalid && (control.touched || control.dirty)) return mensajesDeControl(control);
    const e = this.estado();
    return e.tipo === 'error' && e.error.status === 400 ? (e.error.campos[campo] ?? []) : [];
  }

  /**
   * Envía el reporte. Con `omitirValidacion` se salta la del frontend: sirve para
   * comprobar (P3) que el backend valida igual y responde 400.
   */
  enviar(omitirValidacion = false): void {
    if (!omitirValidacion && this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.estado.set(cargando());
    this.reportesApi.crear(this.practicaId(), this.form.getRawValue()).subscribe({
      next: (reporte) => {
        this.estado.set(exito(reporte));
        this.recarga.update((n) => n + 1);
      },
      error: (e: unknown) => {
        const estado = estadoDeError<Reporte>(e);
        this.estado.set(estado);
        if (estado.tipo === 'error' && accionDeError(estado.error) === 'ir_a_login') {
          void this.router.navigateByUrl('/login');
        }
      },
    });
  }
}
