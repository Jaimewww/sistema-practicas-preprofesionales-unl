import type { EstadoReporte, Evaluacion, Fecha, Practica, ResultadoPractica, TipoRevision } from '../../core/demo';

export type EstadoRevision = 'en_revision' | 'validado' | 'devuelto';
export type AccionRevision = 'validar' | 'devolver';

/** Un plan, reporte o informe de un tutorado que espera la revisión del tutor académico. */
export interface Pendiente {
  tipo: TipoRevision;
  /** Valor de `?r=` de la pantalla que lo revisa. */
  clave: string;
  practica: Practica;
  /** Semana del reporte; `null` en planes e informes. */
  semana: number | null;
  /** «Semana 7 · 8 h» en los reportes; vacío en planes e informes. */
  detalle: string;
  enviadoEl: Fecha;
  /** Días hábiles de espera hasta «hoy». */
  dias: number;
  fueraDePlazo: boolean;
}

/** Lo que muestra T2 de un plan, reporte o informe, con su estado actual y la decisión si ya la hubo. */
export interface Revision {
  tipo: TipoRevision;
  clave: string;
  /** La práctica con las decisiones ya tomadas aplicadas (horas, estado del plan, etc.). */
  practica: Practica;
  semana: number | null;
  estado: EstadoRevision;
  enviadoEl: Fecha | null;
  /** Días hábiles de espera; `null` cuando ya se decidió. */
  dias: number | null;
  plazo: number;
  fueraDePlazo: boolean;
  decididoPor: string;
  decididoEl: Fecha | null;
  observacion: string;
}

/** Un reporte de la tabla de la práctica con el enlace a su pantalla de revisión, si la tiene. */
export interface FilaReporte {
  semana: number;
  estado: EstadoReporte;
  clave: string | null;
}

/** T4: la práctica de un tutorado; `soloLectura` cuando ya no admite revisiones ni evaluación. */
export interface DetallePractica {
  practica: Practica;
  soloLectura: boolean;
  claveReportes: Record<number, string>;
  clavePlan: string | null;
  claveInforme: string | null;
}

/** T5: lo necesario para registrar la evaluación final. */
export interface DatosEvaluacion {
  practica: Practica;
  /** Requisitos que faltan, en minúscula y listos para unir con « y ». */
  faltantes: string[];
  porcentajeInicial: number;
  evaluacion: Evaluacion | null;
}

export interface ResultadoEvaluacion {
  porcentaje: number;
  resultado: ResultadoPractica;
  registradoPor: string;
  registradoEl: Fecha;
}
