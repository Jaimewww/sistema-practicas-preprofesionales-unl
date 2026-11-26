import { TOTAL_SEMANAS, UMBRAL_REZAGO } from './constantes';
import type { Practica } from './modelos';

export const horasValidadas = (p: Pick<Practica, 'reportes'>): number =>
  p.reportes.filter((r) => r.estado === 'validado').reduce((suma, r) => suma + r.horas, 0);

export const horasEnRevision = (p: Pick<Practica, 'reportes'>): number =>
  p.reportes.filter((r) => r.estado === 'en_revision').reduce((suma, r) => suma + r.horas, 0);

/** Horas que ya debería llevar a la semana `semanaActual` (proporcional a las 16 semanas). */
export const horasEsperadas = (requeridas: number, semanaActual: number, totalSemanas = TOTAL_SEMANAS): number =>
  Math.round((requeridas * semanaActual) / totalSemanas);

/** Mínimo para no estar rezagada: el umbral (%) de las horas esperadas. */
export const horasMinimas = (esperadas: number, umbral = UMBRAL_REZAGO): number => Math.round((esperadas * umbral) / 100);

/**
 * Rezagada = horas validadas + en revisión por debajo del mínimo (spec, HU-06 caso 3):
 * lo que está en revisión sí cuenta para no estar rezagada.
 */
export const estaRezagada = (validadas: number, enRevision: number, esperadas: number, umbral = UMBRAL_REZAGO): boolean =>
  validadas + enRevision < horasMinimas(esperadas, umbral);

export interface AvanceHoras {
  validadas: number;
  enRevision: number;
  requeridas: number;
  esperadas: number;
  minimas: number;
  faltantes: number;
  rezagada: boolean;
  pctValidadas: number;
  pctEnRevision: number;
  pctEsperadas: number;
  /** Horas validadas como % de las esperadas. */
  pctCumplimiento: number;
}

const pct = (parte: number, total: number): number => (total > 0 ? Math.round((parte / total) * 100) : 0);

/** Todo el avance de una práctica; `umbral` permite probar la configuración de la carrera (C7). */
export function avanceDe(p: Practica, umbral = UMBRAL_REZAGO): AvanceHoras {
  const validadas = horasValidadas(p);
  const enRevision = horasEnRevision(p);
  const esperadas = horasEsperadas(p.horasRequeridas, p.semanaActual);
  return {
    validadas,
    enRevision,
    requeridas: p.horasRequeridas,
    esperadas,
    minimas: horasMinimas(esperadas, umbral),
    faltantes: p.horasRequeridas - validadas,
    rezagada: estaRezagada(validadas, enRevision, esperadas, umbral),
    pctValidadas: pct(validadas, p.horasRequeridas),
    pctEnRevision: pct(enRevision, p.horasRequeridas),
    pctEsperadas: pct(esperadas, p.horasRequeridas),
    pctCumplimiento: pct(validadas, esperadas),
  };
}

export const rezagada = (p: Practica, umbral = UMBRAL_REZAGO): boolean => avanceDe(p, umbral).rezagada;
