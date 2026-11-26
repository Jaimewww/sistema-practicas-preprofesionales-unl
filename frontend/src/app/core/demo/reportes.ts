import { ESTADO_REPORTE, PRIMERA_SEMANA } from './constantes';
import { sumarDias } from './fechas';
import type { EstadoReporte, InformeFinal, PlanActividades, ReporteSemanal } from './modelos';
import { TUTOR_ACADEMICO } from './personas';
import type { Fecha } from './fechas';

/** Lunes y domingo de la semana `semana` (la 1 empieza el 06/04/2026). */
export function fechasDeSemana(semana: number): { desde: Fecha; hasta: Fecha } {
  const desde = sumarDias(PRIMERA_SEMANA, (semana - 1) * 7);
  return { desde, hasta: sumarDias(desde, 6) };
}

/** Un reporte semanal; `validadoPor` solo se completa si ya hubo decisión. */
export function reporte(semana: number, horas: number, estado: EstadoReporte, extra: Partial<ReporteSemanal> = {}, tutor = TUTOR_ACADEMICO): ReporteSemanal {
  const { desde, hasta } = fechasDeSemana(semana);
  const decidido = estado === 'validado' || estado === 'devuelto';
  return {
    semana,
    desde,
    hasta,
    horas,
    estado,
    observacion: '',
    validadoPor: decidido ? tutor : '',
    validadoEl: decidido ? sumarDias(hasta, 3) : null,
    confirmadoPorEntidad: null,
    enviadoEl: estado === 'sin_reporte' ? null : sumarDias(hasta, 1),
    actividades: [],
    evidencias: [],
    ...extra,
  };
}

export const validado = (semana: number, horas: number, extra: Partial<ReporteSemanal> = {}, tutor = TUTOR_ACADEMICO): ReporteSemanal =>
  reporte(semana, horas, 'validado', extra, tutor);

/** Un plan enviado en `fecha`; si ya se decidió, esa es también la fecha de decisión. */
export function plan(estado: PlanActividades['estado'], actividades: string[], fecha: Fecha, tutor = TUTOR_ACADEMICO): PlanActividades {
  const decidido = estado !== 'en_revision';
  return { estado, enviadoEl: fecha, validadoPor: decidido ? tutor : '', validadoEl: decidido ? fecha : null, observacion: '', actividades };
}

export function informeFinal(estado: InformeFinal['estado'], enviadoEl: Fecha, archivo: string, extra: Partial<InformeFinal> = {}): InformeFinal {
  return {
    estado,
    enviadoEl,
    validadoPor: '',
    validadoEl: null,
    observacion: '',
    resumen: 'Resumen de las actividades cumplidas, los resultados obtenidos y las horas acreditadas en la pasantía.',
    archivo,
    ...extra,
  };
}

export const etiquetaEstadoReporte = (e: EstadoReporte): string => ESTADO_REPORTE[e];
