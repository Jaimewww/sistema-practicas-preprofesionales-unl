import { Injectable } from '@angular/core';
import { Observable, map, timer } from 'rxjs';
import { ApiError } from '../../core/api/envelope';
import { diasHabilesEntre, fecha, HOY, PLAZO_REVISION_DIAS, PRACTICAS_DE_EJEMPLO, TUTOR_ACADEMICO } from '../../core/demo';
import type { EntradaHistorial, Evaluacion, Fecha, Practica, ReporteSemanal, TipoRevision } from '../../core/demo';
import { TutorAcademicoApi } from './tutor-academico.api';
import type { AccionRevision, DatosEvaluacion, DetallePractica, EstadoRevision, Pendiente, ResultadoEvaluacion, Revision } from './tutor-academico.model';

interface Referencia {
  practica: number;
  semana: number | null;
}

/** Claves de `?r=` de cada pantalla de revisión (las del prototipo) y la práctica o semana que abren. */
const REPORTES: Record<string, Referencia> = {
  d7: { practica: 3, semana: 7 },
  l8: { practica: 1, semana: 8 },
  d8: { practica: 3, semana: 8 },
  l5: { practica: 1, semana: 5 },
  l6: { practica: 1, semana: 6 },
};
const PLANES: Record<string, Referencia> = {
  a4: { practica: 4, semana: null },
  a4d: { practica: 4, semana: null },
  l1: { practica: 1, semana: null },
};
const INFORMES: Record<string, Referencia> = {
  v6: { practica: 6, semana: null },
  v6d: { practica: 6, semana: null },
  m5: { practica: 5, semana: null },
};
const REFERENCIAS: Record<TipoRevision, Record<string, Referencia>> = { reporte: REPORTES, plan: PLANES, informe: INFORMES };

/** Clave que se abre cuando la URL no trae `?r=` o trae una que no existe. */
export const CLAVE_POR_DEFECTO: Record<TipoRevision, string> = { reporte: 'd7', plan: 'a4', informe: 'v6' };

interface Decision {
  estado: Exclude<EstadoRevision, 'en_revision'>;
  observacion: string;
  por: string;
  el: Fecha;
}

/** Variantes de ejemplo «devuelto»: el mismo documento ya decidido por el tutor. */
const VARIANTES_DEVUELTO: Record<string, Decision> = {
  'plan:a4d': { estado: 'devuelto', observacion: 'Indique cuántas horas dedicará a cada actividad y las fechas de la capacitación al personal del GAD.', por: TUTOR_ACADEMICO, el: fecha(2026, 6, 2) },
  'informe:v6d': { estado: 'devuelto', observacion: 'El resumen no menciona los resultados del módulo de inventario. Agréguelos y vuelva a presentar el informe.', por: TUTOR_ACADEMICO, el: fecha(2026, 6, 4) },
};

/** Actividades y evidencias de reportes ya decididos que `core/demo` no detalla. */
const DETALLE_REPORTE: Record<string, { actividades: string[]; evidencias: string[] }> = {
  '1:5': { actividades: ['Calificación de talleres de Programación.'], evidencias: ['talleres-semana-5.pdf'] },
  '1:6': { actividades: ['Apoyo en laboratorios de Programación.'], evidencias: ['laboratorio-semana-6.pdf'] },
};

const PORCENTAJE_INICIAL: Record<number, number> = { 5: 75, 6: 70 };

const TUTORADOS: readonly Practica[] = PRACTICAS_DE_EJEMPLO.filter((p) => p.tutorAcademico === TUTOR_ACADEMICO);

/** Plan, informe o reporte de una práctica; el reporte lleva su semana. */
const documento = (tipo: TipoRevision, practica: number, semana: number | null): string => [tipo, practica, semana].filter((x) => x !== null).join(':');

/** Estado que tiene hoy el documento (el de `core/demo`, o el de la decisión ya tomada). */
function estadoDelDocumento(p: Practica, tipo: TipoRevision, semana: number | null) {
  if (tipo === 'plan') return { estado: p.plan.estado, enviadoEl: p.plan.enviadoEl, observacion: p.plan.observacion, por: p.plan.validadoPor, el: p.plan.validadoEl };
  if (tipo === 'informe') {
    const i = p.informeFinal;
    return i ? { estado: i.estado, enviadoEl: i.enviadoEl, observacion: i.observacion, por: i.validadoPor, el: i.validadoEl } : null;
  }
  const r = p.reportes.find((x) => x.semana === semana);
  return r ? { estado: r.estado, enviadoEl: r.enviadoEl, observacion: r.observacion, por: r.validadoPor, el: r.validadoEl } : null;
}

/** La práctica con una decisión ya aplicada: horas, estado del plan o del informe. */
function conDecision(p: Practica, tipo: TipoRevision, semana: number | null, d: Decision): Practica {
  if (tipo === 'plan') {
    const plan = { ...p.plan, estado: d.estado, observacion: d.observacion, validadoPor: d.por, validadoEl: d.el };
    if (d.estado === 'validado' && p.estado === 'asignada') {
      const entrada: EntradaHistorial = { estadoAnterior: 'asignada', estadoNuevo: 'en_curso', autor: d.por, fecha: d.el, motivo: '' };
      return { ...p, plan, estado: 'en_curso', historial: [...p.historial, entrada] };
    }
    return { ...p, plan };
  }
  if (tipo === 'informe' && p.informeFinal) {
    return { ...p, informeFinal: { ...p.informeFinal, estado: d.estado, observacion: d.observacion, validadoPor: d.por, validadoEl: d.el } };
  }
  if (tipo === 'reporte') {
    const reportes = p.reportes.map((r): ReporteSemanal => (r.semana === semana ? { ...r, estado: d.estado, observacion: d.observacion, validadoPor: d.por, validadoEl: d.el } : r));
    return { ...p, reportes };
  }
  return p;
}

/** Mock en memoria: las prácticas que tutoriza Roberto Paredes y las decisiones que toma en la sesión. */
@Injectable()
export class TutorAcademicoMock extends TutorAcademicoApi {
  /** Espera simulada por defecto; los tests la ponen en 0 para no esperar. */
  static demoraPorDefecto = 400;
  demoraMs = TutorAcademicoMock.demoraPorDefecto;
  private readonly decisiones = new Map<string, Decision>();
  private readonly evaluaciones = new Map<number, Evaluacion>();

  tutorados(): Observable<Practica[]> {
    return this.responder(() => TUTORADOS.map((p) => this.vigente(p.id)));
  }

  pendientes(): Observable<Pendiente[]> {
    return this.responder(() => {
      const lista: Pendiente[] = [];
      for (const base of TUTORADOS) {
        const p = this.vigente(base.id);
        for (const tipo of ['plan', 'reporte', 'informe'] as const) {
          for (const [clave, ref] of Object.entries(REFERENCIAS[tipo])) {
            if (ref.practica !== p.id || this.esVariante(tipo, clave)) continue;
            const doc = estadoDelDocumento(p, tipo, ref.semana);
            if (!doc || doc.estado !== 'en_revision' || !doc.enviadoEl) continue;
            const dias = diasHabilesEntre(doc.enviadoEl, HOY);
            const horas = ref.semana === null ? 0 : (p.reportes.find((r) => r.semana === ref.semana)?.horas ?? 0);
            lista.push({
              tipo,
              clave,
              practica: p,
              semana: ref.semana,
              detalle: ref.semana === null ? '' : `Semana ${ref.semana} · ${horas} h`,
              enviadoEl: doc.enviadoEl,
              dias,
              fueraDePlazo: dias > PLAZO_REVISION_DIAS,
            });
          }
        }
      }
      return lista.sort((a, b) => a.enviadoEl.localeCompare(b.enviadoEl) || a.practica.id - b.practica.id || (a.semana ?? 0) - (b.semana ?? 0));
    });
  }

  revision(tipo: TipoRevision, clave: string): Observable<Revision> {
    return this.responder(() => this.revisionDe(tipo, this.claveValida(tipo, clave)));
  }

  decidir(tipo: TipoRevision, clave: string, accion: AccionRevision, observacion: string): Observable<Revision> {
    return this.responder(() => {
      const k = this.claveValida(tipo, clave);
      const actual = this.revisionDe(tipo, k);
      if (actual.estado !== 'en_revision') {
        throw new ApiError(409, 'revision_ya_decidida', 'Este documento ya no está en revisión.');
      }
      if (accion === 'devolver' && !observacion.trim()) {
        throw new ApiError(400, 'validacion', 'La devolución exige una observación', { observacion: ['La devolución exige una observación'] });
      }
      const ref = REFERENCIAS[tipo][k];
      this.decisiones.set(documento(tipo, ref.practica, ref.semana), {
        estado: accion === 'validar' ? 'validado' : 'devuelto',
        observacion: observacion.trim(),
        por: TUTOR_ACADEMICO,
        el: HOY,
      });
      return this.revisionDe(tipo, k);
    });
  }

  practica(clave: string): Observable<DetallePractica> {
    return this.responder(() => {
      if (clave === 'ro') return this.suspendida();
      const id = clave === '' ? 1 : Number(clave);
      const practica = this.vigente(id);
      const claveReportes: Record<number, string> = {};
      for (const [k, ref] of Object.entries(REPORTES)) if (ref.practica === id && ref.semana !== null) claveReportes[ref.semana] = k;
      const buscar = (tabla: Record<string, Referencia>): string | null => Object.entries(tabla).find(([k, ref]) => ref.practica === id && !this.esVariante(tabla === PLANES ? 'plan' : 'informe', k))?.[0] ?? null;
      return { practica, soloLectura: false, claveReportes, clavePlan: buscar(PLANES), claveInforme: buscar(INFORMES) };
    });
  }

  evaluacion(practicaId: number): Observable<DatosEvaluacion> {
    return this.responder(() => {
      const practica = this.vigente(practicaId);
      const faltantes: string[] = [];
      if (practica.informeFinal?.estado !== 'validado') faltantes.push('el informe final del estudiante revisado');
      if (!practica.informeExterno) faltantes.push('el informe externo');
      return { practica, faltantes, porcentajeInicial: practica.evaluacion?.porcentaje ?? PORCENTAJE_INICIAL[practicaId] ?? 70, evaluacion: practica.evaluacion };
    });
  }

  registrarEvaluacion(practicaId: number, porcentaje: number): Observable<ResultadoEvaluacion> {
    return this.responder(() => {
      const practica = this.vigente(practicaId);
      if (practica.estado !== 'en_revision_final') {
        throw new ApiError(409, 'practica_no_en_revision_final', 'La evaluación final se registra cuando la práctica está en revisión final.');
      }
      if (practica.evaluacion) throw new ApiError(409, 'evaluacion_ya_registrada', 'La evaluación final de esta práctica ya está registrada.');
      const faltantes: string[] = [];
      if (practica.informeFinal?.estado !== 'validado') faltantes.push('el informe final del estudiante revisado');
      if (!practica.informeExterno) faltantes.push('el informe externo');
      if (faltantes.length) {
        throw new ApiError(409, 'faltan_requisitos', `No se puede registrar la evaluación final: falta ${faltantes.join(' y ')}.`);
      }
      if (!Number.isFinite(porcentaje) || porcentaje < 0 || porcentaje > 100) {
        throw new ApiError(400, 'validacion', 'Datos inválidos.', { porcentaje: ['Ingrese un porcentaje de 0 a 100.'] });
      }
      const evaluacion: Evaluacion = { porcentaje, resultado: porcentaje >= 70 ? 'aprobada' : 'no_aprobada', registradoPor: TUTOR_ACADEMICO, registradoEl: HOY };
      this.evaluaciones.set(practicaId, evaluacion);
      return { ...evaluacion };
    });
  }

  private responder<T>(obtener: () => T): Observable<T> {
    return timer(this.demoraMs).pipe(map(obtener));
  }

  private claveValida(tipo: TipoRevision, clave: string): string {
    return REFERENCIAS[tipo][clave] ? clave : CLAVE_POR_DEFECTO[tipo];
  }

  private esVariante(tipo: TipoRevision, clave: string): boolean {
    return `${tipo}:${clave}` in VARIANTES_DEVUELTO;
  }

  /** La práctica con el detalle de reportes, las decisiones y la evaluación de la sesión aplicados. */
  private vigente(id: number): Practica {
    const base = TUTORADOS.find((p) => p.id === id);
    if (!base) throw new ApiError(404, 'no_encontrado', 'No encontrado.');
    let p: Practica = {
      ...base,
      reportes: base.reportes.map((r) => {
        const extra = DETALLE_REPORTE[`${id}:${r.semana}`];
        return extra && !r.actividades.length ? { ...r, ...extra } : r;
      }),
    };
    for (const tipo of ['plan', 'informe'] as const) {
      const d = this.decisiones.get(documento(tipo, id, null));
      if (d) p = conDecision(p, tipo, null, d);
    }
    for (const r of base.reportes) {
      const d = this.decisiones.get(documento('reporte', id, r.semana));
      if (d) p = conDecision(p, 'reporte', r.semana, d);
    }
    const evaluacion = this.evaluaciones.get(id);
    return evaluacion ? { ...p, evaluacion } : p;
  }

  private revisionDe(tipo: TipoRevision, clave: string): Revision {
    const ref = REFERENCIAS[tipo][clave];
    let practica = this.vigente(ref.practica);
    const decidida = this.decisiones.has(documento(tipo, ref.practica, ref.semana));
    const variante = VARIANTES_DEVUELTO[`${tipo}:${clave}`];
    if (variante && !decidida) practica = conDecision(practica, tipo, ref.semana, variante);
    const doc = estadoDelDocumento(practica, tipo, ref.semana);
    if (!doc) throw new ApiError(404, 'no_encontrado', 'No existe ese documento para la práctica.');
    const enRevision = doc.estado === 'en_revision' || doc.estado === 'sin_reporte';
    const dias = enRevision && doc.enviadoEl ? diasHabilesEntre(doc.enviadoEl, HOY) : null;
    return {
      tipo,
      clave,
      practica,
      semana: ref.semana,
      estado: enRevision ? 'en_revision' : (doc.estado as Revision['estado']),
      enviadoEl: doc.enviadoEl,
      dias,
      plazo: PLAZO_REVISION_DIAS,
      fueraDePlazo: dias !== null && dias > PLAZO_REVISION_DIAS,
      decididoPor: enRevision ? '' : doc.por,
      decididoEl: enRevision ? null : doc.el,
      observacion: doc.observacion,
    };
  }

  /** Variante de ejemplo de la práctica 1 suspendida por la coordinación (solo lectura). */
  private suspendida(): DetallePractica {
    const base = this.vigente(1);
    const historial: EntradaHistorial[] = [
      { estadoAnterior: '', estadoNuevo: 'asignada', autor: 'SISTEMA', fecha: fecha(2026, 4, 6), motivo: '' },
      { estadoAnterior: 'asignada', estadoNuevo: 'en_curso', autor: TUTOR_ACADEMICO, fecha: fecha(2026, 4, 10), motivo: '' },
      { estadoAnterior: 'en_curso', estadoNuevo: 'suspendida', autor: 'MENDOZA ARÉVALO CARLOS ANDRÉS', fecha: fecha(2026, 5, 20), motivo: 'licencia de la persona practicante' },
    ];
    return { practica: { ...base, estado: 'suspendida', historial }, soloLectura: true, claveReportes: {}, clavePlan: null, claveInforme: null };
  }
}
