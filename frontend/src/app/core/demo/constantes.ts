import { fecha } from './fechas';
import type { EstadoAnexo, EstadoPractica, EstadoReporte, ResultadoPractica, TipoAlerta, TipoRevision } from './modelos';

export const TOTAL_SEMANAS = 16;
/** Porcentaje de las horas esperadas por debajo del cual una práctica está rezagada (RF-12). */
export const UMBRAL_REZAGO = 80;
export const PRIMERA_SEMANA = fecha(2026, 4, 6);
/** «Hoy» de la demostración: todas las fechas relativas se calculan contra esta. */
export const HOY = fecha(2026, 6, 5);
/** Semana de la tarjeta de periodo del marco (la de la práctica laboral de la estudiante). */
export const SEMANA_ACTUAL = 9;

export const PERIODO = 'MAR.26-AGO.26 GRADO';
export const PERIODO_ANTERIOR = 'SEP.25-ENE.26 GRADO';
export const CARRERA = 'FEIRNNR - COMPUTACIÓN - PRESENCIAL - Régimen 2019 - CICLO 4A';
export const CARRERAS_OTRAS = [
  'FEIRNNR - ELECTRÓNICA - PRESENCIAL - Régimen 2019 - CICLO 4A',
  'FEIRNNR - AGROFORESTAL - PRESENCIAL - Régimen 2019 - CICLO 4A',
] as const;

/** Días hábiles que tiene el tutor para revisar (RF-12). */
export const PLAZO_REVISION_DIAS = 5;
/** Días tras cerrar la semana para reportar. */
export const PLAZO_REPORTE_DIAS = 3;
/** RNF-04: el panel del coordinador se mide con 150 prácticas de su carrera. */
export const CANTIDAD_PRACTICAS_CARRERA = 150;

export interface ConfiguracionCarrera {
  carrera: string;
  horasLaboral: number;
  horasComunitaria: number;
  horasLaboralDistancia: number;
  horasComunitariaDistancia: number;
  plazoReporteDias: number;
  plazoRevisionDias: number;
  umbralRezago: number;
}

export const CONFIGURACION_CARRERA: ConfiguracionCarrera = {
  carrera: CARRERA,
  horasLaboral: 160,
  horasComunitaria: 96,
  horasLaboralDistancia: 256,
  horasComunitariaDistancia: 144,
  plazoReporteDias: PLAZO_REPORTE_DIAS,
  plazoRevisionDias: PLAZO_REVISION_DIAS,
  umbralRezago: UMBRAL_REZAGO,
};

export const ESTADO_REPORTE: Record<EstadoReporte, string> = {
  validado: 'Validado',
  en_revision: 'En revisión',
  devuelto: 'Devuelto con observación',
  sin_reporte: 'Sin reporte',
};

export const ESTADO_ANEXO: Record<EstadoAnexo, string> = {
  pendiente: 'Pendiente de legalización',
  legalizado: 'Legalizado',
};

export const ESTADO_PRACTICA: Record<EstadoPractica, string> = {
  asignada: 'Asignada',
  en_curso: 'En curso',
  en_revision_final: 'En revisión final',
  suspendida: 'Suspendida',
  cancelada: 'Cancelada',
  cerrada: 'Cerrada',
};

export const RESULTADO_PRACTICA: Record<ResultadoPractica, string> = {
  aprobada: 'Aprobada',
  no_aprobada: 'No aprobada',
};

/** Estados en los que la práctica ya no admite cambios. */
export const ESTADOS_SOLO_LECTURA: readonly EstadoPractica[] = ['suspendida', 'cancelada', 'cerrada'];
/** Estados en los que se evalúa el rezago (CU-03, alternativa 1a). */
export const ESTADOS_ACTIVOS: readonly EstadoPractica[] = ['en_curso'];
/** Una práctica sigue vigente mientras no se haya cerrado ni cancelado. */
export const ESTADOS_VIGENTES: readonly EstadoPractica[] = ['asignada', 'en_curso', 'en_revision_final', 'suspendida'];

export const TIPO_REVISION: Record<TipoRevision, string> = {
  plan: 'Plan de actividades',
  reporte: 'Reporte semanal',
  informe: 'Informe final',
};

export const TIPOS_ALERTA: Record<TipoAlerta, string> = {
  reporte_no_enviado: 'No reportó en plazo',
  revision_pendiente: 'Revisión vencida',
  rezago: 'Horas rezagadas',
  incumplimiento: 'Incumplimiento reportado',
};
