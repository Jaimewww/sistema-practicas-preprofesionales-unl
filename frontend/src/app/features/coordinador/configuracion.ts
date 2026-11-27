import { Component, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { tap } from 'rxjs';
import { ApiError } from '../../core/api/envelope';
import { cargando } from '../../core/estado-ui';
import { CONFIGURACION_CARRERA } from '../../core/demo';
import type { ConfiguracionCarrera } from '../../core/demo';
import { Aviso, Contador, Tarjeta } from '../../shared/ui';
import { CoordinadorApi } from './coordinador.api';
import { aEstado, camposDe, type CampoConfiguracion, validarConfiguracion } from './coordinador.util';
import { EstadoPantalla } from './ui/estado-pantalla';

interface CampoUi {
  campo: CampoConfiguracion;
  etiqueta: string;
  unidad: string;
  ayuda: string;
  max: number;
}

const HORAS = (campo: CampoConfiguracion, etiqueta: string, ayuda: string): CampoUi => ({ campo, etiqueta, unidad: 'h', ayuda, max: 2000 });

/** C7 · Configuración de la carrera: horas por modalidad, plazos y umbral de rezago (RF-12). */
@Component({
  selector: 'app-configuracion',
  imports: [ReactiveFormsModule, RouterLink, Aviso, Contador, Tarjeta, EstadoPantalla],
  templateUrl: './configuracion.html',
  styleUrls: ['./pantalla.css', './configuracion.css'],
})
export class Configuracion {
  private readonly api = inject(CoordinadorApi);
  protected readonly formulario = new FormGroup<Record<CampoConfiguracion, FormControl<number | null>>>({
    horasLaboral: new FormControl(CONFIGURACION_CARRERA.horasLaboral),
    horasComunitaria: new FormControl(CONFIGURACION_CARRERA.horasComunitaria),
    horasLaboralDistancia: new FormControl(CONFIGURACION_CARRERA.horasLaboralDistancia),
    horasComunitariaDistancia: new FormControl(CONFIGURACION_CARRERA.horasComunitariaDistancia),
    plazoReporteDias: new FormControl(CONFIGURACION_CARRERA.plazoReporteDias),
    plazoRevisionDias: new FormControl(CONFIGURACION_CARRERA.plazoRevisionDias),
    umbralRezago: new FormControl(CONFIGURACION_CARRERA.umbralRezago),
  });
  protected readonly estado = toSignal(aEstado(this.api.configuracion().pipe(tap((c) => this.formulario.setValue(camposDe(c))))), { initialValue: cargando<ConfiguracionCarrera>() });

  protected readonly errores = signal<Partial<Record<CampoConfiguracion, string>>>({});
  protected readonly guardado = signal(false);
  protected readonly errorApi = signal('');

  protected readonly horas: CampoUi[] = [
    HORAS('horasLaboral', 'Horas laborales · presencial', 'Pasantía, ayudantía o práctica laboral.'),
    HORAS('horasComunitaria', 'Horas comunitarias · presencial', 'Proyecto de vinculación.'),
    HORAS('horasLaboralDistancia', 'Horas laborales · a distancia', 'No puede ser menor que las presenciales.'),
    HORAS('horasComunitariaDistancia', 'Horas comunitarias · a distancia', 'No puede ser menor que las presenciales.'),
  ];
  protected readonly plazos: CampoUi[] = [
    { campo: 'plazoReporteDias', etiqueta: 'Plazo de reporte (días)', unidad: 'días', ayuda: 'Días naturales que tiene el estudiante tras cerrar la semana.', max: 365 },
    { campo: 'plazoRevisionDias', etiqueta: 'Plazo de revisión (días hábiles)', unidad: 'días hábiles', ayuda: 'Tiempo máximo del tutor académico para revisar.', max: 365 },
    { campo: 'umbralRezago', etiqueta: 'Umbral de rezago (%)', unidad: '%', ayuda: 'Una práctica se marca rezagada si sus horas validadas y en revisión están por debajo de este porcentaje de las esperadas.', max: 100 },
  ];
  protected readonly lista = (): Array<[CampoConfiguracion, string]> => Object.entries(this.errores()) as Array<[CampoConfiguracion, string]>;

  /** Cualquier cambio quita los avisos del guardado anterior. */
  protected tocar(): void {
    this.guardado.set(false);
  }

  protected guardar(): void {
    this.guardado.set(false);
    this.errorApi.set('');
    const errores = validarConfiguracion(this.formulario.getRawValue());
    this.errores.set(errores);
    if (Object.keys(errores).length) return;
    const valores = this.formulario.getRawValue() as Record<CampoConfiguracion, number>;
    this.api.guardarConfiguracion({ ...CONFIGURACION_CARRERA, ...valores }).subscribe({
      next: () => this.guardado.set(true),
      error: (e: unknown) => {
        if (e instanceof ApiError && e.status === 400) {
          this.errores.set(Object.fromEntries(Object.entries(e.campos).map(([k, v]) => [k, v[0]])));
        } else {
          this.errorApi.set('No se pudo guardar la configuración. Inténtelo de nuevo.');
        }
      },
    });
  }

  protected restablecer(): void {
    this.formulario.setValue(camposDe(CONFIGURACION_CARRERA));
    this.errores.set({});
    this.guardado.set(false);
    this.errorApi.set('');
  }
}
