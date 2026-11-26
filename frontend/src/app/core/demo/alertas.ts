import { CONFIGURACION_CARRERA, ESTADOS_ACTIVOS, ESTADOS_SOLO_LECTURA, HOY, type ConfiguracionCarrera } from './constantes';
import { diasHabilesEntre, sumarDias, sumarDiasHabiles } from './fechas';
import type { Fecha } from './fechas';
import { avanceDe } from './horas';
import type { AlertaPractica, Practica, TipoAlerta } from './modelos';

/** Documentos de la práctica que esperan revisión, con su etiqueta y fecha de envío. */
export function documentosEnRevision(p: Practica): Array<{ etiqueta: string; enviadoEl: Fecha }> {
  const docs: Array<{ etiqueta: string; enviadoEl: Fecha }> = [];
  if (p.plan.estado === 'en_revision' && p.plan.enviadoEl) docs.push({ etiqueta: 'Plan de actividades', enviadoEl: p.plan.enviadoEl });
  for (const r of p.reportes) if (r.estado === 'en_revision' && r.enviadoEl) docs.push({ etiqueta: `Semana ${r.semana}`, enviadoEl: r.enviadoEl });
  if (p.informeFinal?.estado === 'en_revision') docs.push({ etiqueta: 'Informe final', enviadoEl: p.informeFinal.enviadoEl });
  return docs;
}

/** Alertas activas de una práctica (RF-07, CU-03), calculadas contra `HOY`. */
export function alertasDe(p: Practica, config: ConfiguracionCarrera = CONFIGURACION_CARRERA): AlertaPractica[] {
  if (ESTADOS_SOLO_LECTURA.includes(p.estado)) return [];
  const alertas: AlertaPractica[] = [];
  const nueva = (tipo: TipoAlerta, detalle: string, fecha: Fecha) => alertas.push({ tipo, detalle, fecha, practicaId: p.id });

  for (const r of p.reportes) {
    if (r.estado !== 'sin_reporte') continue;
    const limite = sumarDias(r.hasta, config.plazoReporteDias);
    if (HOY > limite) nueva('reporte_no_enviado', `La semana ${r.semana} se cerró sin reporte.`, limite);
  }
  for (const doc of documentosEnRevision(p)) {
    const dias = diasHabilesEntre(doc.enviadoEl, HOY);
    if (dias > config.plazoRevisionDias) {
      nueva('revision_pendiente', `${doc.etiqueta}: ${dias} días hábiles de espera (el plazo es de ${config.plazoRevisionDias}).`, sumarDiasHabiles(doc.enviadoEl, config.plazoRevisionDias));
    }
  }
  const avance = avanceDe(p, config.umbralRezago);
  if (ESTADOS_ACTIVOS.includes(p.estado) && avance.rezagada) {
    nueva('rezago', `${avance.validadas + avance.enRevision} h de las ${avance.minimas} h mínimas del ${config.umbralRezago} %.`, HOY);
  }
  for (const inc of p.incumplimientos) nueva('incumplimiento', inc.descripcion, inc.reportadoEl);
  return alertas;
}

/** De la más reciente a la más vieja. */
export const ordenarAlertas = (alertas: AlertaPractica[]): AlertaPractica[] =>
  [...alertas].sort((a, b) => (a.fecha === b.fecha ? b.practicaId - a.practicaId : a.fecha < b.fecha ? 1 : -1));
