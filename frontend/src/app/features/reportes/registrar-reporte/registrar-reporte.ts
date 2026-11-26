import { Component, inject, input, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { estadoDeError } from '../../../core/errores';
import { cargando, exito, inicial, type EstadoUi } from '../../../core/estado-ui';
import type { Reporte } from '../reporte.model';
import { ReportesApi } from '../reportes.api';

/**
 * Pantalla E4: registrar horas semanales (F-002).     RESPONSABLE: Melissa
 *
 * El esqueleto deja el flujo mínimo funcionando contra el mock para probar el
 * cableado. Pendiente (Melissa): diseño del formulario, confirmación del 201,
 * horas acumuladas con reportesApi.horas() y recibir practicaId del selector.
 */
@Component({
  selector: 'app-registrar-reporte',
  imports: [ReactiveFormsModule],
  templateUrl: './registrar-reporte.html',
})
export class RegistrarReporte {
  private readonly reportesApi = inject(ReportesApi);

  readonly practicaId = input(1);
  readonly estado = signal<EstadoUi<Reporte>>(inicial());

  readonly form = inject(NonNullableFormBuilder).group({
    semana: [1, Validators.required],
    horas_reportadas: [0, Validators.required],
  });

  enviar(): void {
    this.estado.set(cargando());
    this.reportesApi.crear(this.practicaId(), this.form.getRawValue()).subscribe({
      next: (reporte) => this.estado.set(exito(reporte)),
      error: (e: unknown) => this.estado.set(estadoDeError(e)),
    });
  }
}
