import type { Fecha } from './fechas';

export type TipoPractica = 'laboral' | 'comunitaria';
export type EstadoPractica = 'asignada' | 'en_curso' | 'en_revision_final' | 'suspendida' | 'cancelada' | 'cerrada';
export type ResultadoPractica = 'aprobada' | 'no_aprobada';
export type EstadoReporte = 'validado' | 'en_revision' | 'devuelto' | 'sin_reporte';
export type EstadoAnexo = 'pendiente' | 'legalizado';
export type TipoRevision = 'plan' | 'reporte' | 'informe';
export type TipoAlerta = 'reporte_no_enviado' | 'revision_pendiente' | 'rezago' | 'incumplimiento';
export type Subtipo = '' | 'ayudantia_docencia' | 'ayudantia_investigacion' | 'pasantia';
export type InstrumentoEntidad = 'convenio' | 'carta';
export type AprobacionEntidad = 'aprobado' | 'pendiente';

export interface ReporteSemanal {
  semana: number;
  desde: Fecha;
  hasta: Fecha;
  horas: number;
  estado: EstadoReporte;
  observacion: string;
  validadoPor: string;
  validadoEl: Fecha | null;
  /** `null` mientras la entidad no lo ha visto (sin reporte). */
  confirmadoPorEntidad: boolean | null;
  enviadoEl: Fecha | null;
  actividades: string[];
  evidencias: string[];
}

export interface PlanActividades {
  estado: 'validado' | 'en_revision' | 'devuelto';
  enviadoEl: Fecha | null;
  validadoPor: string;
  validadoEl: Fecha | null;
  observacion: string;
  actividades: string[];
}

export interface InformeFinal {
  estado: 'validado' | 'en_revision' | 'devuelto';
  enviadoEl: Fecha;
  validadoPor: string;
  validadoEl: Fecha | null;
  observacion: string;
  resumen: string;
  archivo: string;
}

export interface InformeExterno {
  registradoPor: string;
  registradoEl: Fecha;
  valoracion: string;
  archivo: string;
}

export interface Evaluacion {
  porcentaje: number;
  resultado: ResultadoPractica;
  registradoPor: string;
  registradoEl: Fecha;
}

export interface EntradaHistorial {
  estadoAnterior: EstadoPractica | '';
  estadoNuevo: EstadoPractica;
  autor: string;
  fecha: Fecha;
  motivo: string;
}

export interface Incumplimiento {
  descripcion: string;
  reportadoPor: string;
  reportadoEl: Fecha;
}

export interface Anexo {
  id: number;
  nombre: string;
  tipo: 'informe_final' | 'informe_externo';
  archivo: string;
  estado: EstadoAnexo;
  legalizadoPor: string;
  legalizadoEl: Fecha | null;
}

export interface Practica {
  id: number;
  estudiante: string;
  estado: EstadoPractica;
  tipo: TipoPractica;
  subtipo: Subtipo;
  esAyudantia: boolean;
  entidad: string;
  tutorAcademico: string;
  tutorEntidad: string;
  proyectoVinculacion: string;
  periodo: string;
  carrera: string;
  horasRequeridas: number;
  semanaActual: number;
  plan: PlanActividades;
  reportes: ReporteSemanal[];
  informeFinal: InformeFinal | null;
  informeExterno: InformeExterno | null;
  evaluacion: Evaluacion | null;
  resultado: ResultadoPractica | '';
  historial: EntradaHistorial[];
  incumplimientos: Incumplimiento[];
  anexos: Anexo[];
}

export interface AlertaPractica {
  tipo: TipoAlerta;
  detalle: string;
  fecha: Fecha;
  practicaId: number;
}

export interface EntidadReceptora {
  id: number;
  nombre: string;
  instrumento: InstrumentoEntidad;
  referencia: string;
  vigenciaDesde: Fecha;
  vigenciaHasta: Fecha;
  estadoAprobacion: AprobacionEntidad;
}
