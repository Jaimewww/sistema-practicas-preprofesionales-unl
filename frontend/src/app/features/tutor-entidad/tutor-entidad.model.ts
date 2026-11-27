import type { Fecha, Practica, ReporteSemanal } from '../../core/demo';

/** Un reporte semanal que espera (o ya tuvo) la confirmación de la entidad. `codigo` es el `?r=` de la URL. */
export interface ReporteConfirmable {
  codigo: string;
  practica: Practica;
  reporte: ReporteSemanal;
  /** Quién confirmó y cuándo; `null` mientras la entidad no lo confirma. */
  confirmacion: Confirmacion | null;
}

export interface Confirmacion {
  por: string;
  el: Fecha;
}

export interface ArchivoInforme {
  nombre: string;
  bytes: number;
}

export interface RegistroInformeExterno {
  registradoPor: string;
  registradoEl: Fecha;
  archivo: string;
}

export interface RegistroIncumplimiento {
  reportadoPor: string;
  reportadoEl: Fecha;
  /** Tutor académico al que se avisó. */
  avisadoA: string;
}
