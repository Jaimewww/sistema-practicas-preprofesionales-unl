import { ESTADOS_VIGENTES, HOY } from './constantes';
import type { Fecha } from './fechas';
import { fecha } from './fechas';
import type { AprobacionEntidad, EntidadReceptora, InstrumentoEntidad, Practica } from './modelos';
import { PRACTICAS_CARRERA } from './sinteticas';

export const INSTRUMENTOS: Record<InstrumentoEntidad, string> = { convenio: 'Convenio', carta: 'Carta de compromiso' };
export const ESTADO_APROBACION: Record<AprobacionEntidad, string> = { aprobado: 'Aprobado', pendiente: 'Pendiente de aprobación' };

/** Catálogo consultivo (N1) y convenios (N2): son la misma lista; el instrumento y la vigencia son datos de ejemplo. */
export const ENTIDADES: readonly EntidadReceptora[] = [
  { id: 1, nombre: 'Universidad Nacional de Loja - Carrera de Computación', instrumento: 'convenio', referencia: 'CONV-2025-014', vigenciaDesde: fecha(2025, 1, 15), vigenciaHasta: fecha(2027, 12, 31), estadoAprobacion: 'aprobado' },
  { id: 2, nombre: 'Junta Parroquial de San Lucas', instrumento: 'carta', referencia: 'CC-2026-003', vigenciaDesde: fecha(2026, 1, 12), vigenciaHasta: fecha(2026, 12, 31), estadoAprobacion: 'aprobado' },
  { id: 3, nombre: 'Soluciones Informáticas del Sur Cía. Ltda.', instrumento: 'convenio', referencia: 'CONV-2026-002', vigenciaDesde: fecha(2026, 2, 1), vigenciaHasta: fecha(2028, 1, 31), estadoAprobacion: 'aprobado' },
  // Venció el 31/03/2026 y sus prácticas siguen en curso: la consulta deja ver el desfase.
  { id: 4, nombre: 'Agroindustrias del Norte Cía. Ltda.', instrumento: 'convenio', referencia: 'CONV-2025-031', vigenciaDesde: fecha(2025, 4, 1), vigenciaHasta: fecha(2026, 3, 31), estadoAprobacion: 'aprobado' },
  { id: 5, nombre: 'GAD Parroquial de Vilcabamba', instrumento: 'carta', referencia: 'CC-2026-011', vigenciaDesde: fecha(2026, 1, 20), vigenciaHasta: fecha(2027, 1, 19), estadoAprobacion: 'pendiente' },
  // Solo tuvo una práctica comunitaria, ya cerrada: N1 muestra el estado vacío.
  { id: 6, nombre: 'GAD Municipal de Catamayo', instrumento: 'convenio', referencia: 'CONV-2024-019', vigenciaDesde: fecha(2024, 7, 1), vigenciaHasta: fecha(2026, 6, 30), estadoAprobacion: 'aprobado' },
];

/** ¿El instrumento está vigente en `en` (por defecto, hoy)? */
export const estaVigente = (e: EntidadReceptora, en: Fecha = HOY): boolean => e.vigenciaDesde <= en && en <= e.vigenciaHasta;

/** N1 detalle: prácticas aún vigentes de la entidad. */
export const practicasVigentesDeLaEntidad = (nombre: string, practicas: readonly Practica[] = PRACTICAS_CARRERA): Practica[] =>
  practicas.filter((p) => p.entidad === nombre && ESTADOS_VIGENTES.includes(p.estado));
