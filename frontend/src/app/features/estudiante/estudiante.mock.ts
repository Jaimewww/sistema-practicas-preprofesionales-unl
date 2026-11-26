import { Injectable } from '@angular/core';
import { Observable, map, timer } from 'rxjs';
import { ApiError } from '../../core/api/envelope';
import { fecha, HOY, PRACTICAS_DE_LA_ESTUDIANTE, TUTOR_ACADEMICO } from '../../core/demo';
import type { Practica, ReporteSemanal } from '../../core/demo';
import { EstudianteApi } from './estudiante.api';
import type { ActividadPlan, EvidenciaReporte, PlanDetalle, PlanEditable, ReporteDetalle, VersionPlan } from './estudiante.model';

/** Herramientas y entregables de ejemplo, en el orden de las actividades del plan de cada práctica. */
const DETALLE_PLAN: Record<number, ReadonlyArray<readonly [string, string]>> = {
  1: [
    ['Rúbricas y hoja de cálculo de notas.', 'Actas de calificación de cada taller.'],
    ['Aula virtual y guías de ejercicios.', 'Registro de asistencia a las tutorías.'],
    ['Editor de texto y repositorio del curso.', 'Guías de laboratorio listas para usar.'],
  ],
  2: [
    ['Teléfonos de los participantes y proyector.', 'Registro de asistencia a los talleres.'],
    ['Editor de texto e impresora.', 'Guías impresas para los participantes.'],
  ],
};

const OBSERVACION_V1 = 'Detalle las herramientas y los entregables de cada actividad.';

/** Mock en memoria: la estudiante de la demostración con su práctica laboral y su comunitaria. */
@Injectable()
export class EstudianteMock extends EstudianteApi {
  /** Espera simulada por defecto; los tests la ponen en 0 para no esperar. */
  static demoraPorDefecto = 400;
  demoraMs = EstudianteMock.demoraPorDefecto;
  /** Planes que la estudiante envió en esta sesión (quedan «en revisión»). */
  private readonly enviados = new Map<number, ActividadPlan[]>();

  misPracticas(): Observable<Practica[]> {
    return this.responder(() => [...PRACTICAS_DE_LA_ESTUDIANTE]);
  }

  practica(id: number): Observable<Practica> {
    return this.responder(() => this.buscar(id));
  }

  plan(practicaId: number): Observable<PlanDetalle> {
    return this.responder(() => {
      const practica = this.buscar(practicaId);
      const enviado = this.enviados.get(practicaId);
      const base = this.versionesPrevias(practica);
      const vigentes: VersionPlan[] = [
        ...base,
        { numero: base.length + 1, estado: 'aprobada', enviadaEl: practica.plan.enviadoEl ?? fecha(2026, 4, 9), decididaEl: practica.plan.validadoEl, decididaPor: practica.plan.validadoPor, observacion: '' },
      ];
      if (enviado) {
        const versiones: VersionPlan[] = [...vigentes, { numero: vigentes.length + 1, estado: 'en_revision', enviadaEl: HOY, decididaEl: null, decididaPor: '', observacion: '' }];
        return { practica, version: versiones.length, estado: 'en_revision', decididoPor: '', decididoEl: null, actividades: enviado, versiones };
      }
      const versiones = vigentes;
      return {
        practica,
        version: versiones.length,
        estado: practica.plan.estado,
        decididoPor: practica.plan.validadoPor,
        decididoEl: practica.plan.validadoEl,
        actividades: this.actividades(practica),
        versiones,
      };
    });
  }

  planEditable(practicaId: number): Observable<PlanEditable> {
    return this.responder(() => {
      const practica = this.buscar(practicaId);
      const versiones = this.versionesPrevias(practica);
      const devuelta = versiones.find((v) => v.estado === 'devuelta');
      return {
        practica,
        version: versiones.length + 1,
        observacion: devuelta?.decididaEl ? { texto: devuelta.observacion, autor: devuelta.decididaPor, fecha: devuelta.decididaEl } : null,
        versiones,
        // Sin versión devuelta no hay nada que corregir: el formulario empieza vacío.
        actividades: devuelta ? this.actividades(practica) : [],
      };
    });
  }

  enviarPlan(practicaId: number, actividades: ActividadPlan[]): Observable<void> {
    return this.responder(() => {
      this.buscar(practicaId);
      if (!actividades.some((a) => a.descripcion.trim())) {
        throw new ApiError(400, 'validacion', 'Datos inválidos.', { actividades: ['Registre al menos una actividad.'] });
      }
      this.enviados.set(practicaId, actividades);
    });
  }

  reporte(practicaId: number, semana: number): Observable<ReporteDetalle> {
    return this.responder(() => {
      const practica = this.buscar(practicaId);
      const original = practica.reportes.find((r) => r.semana === semana);
      if (!original) throw new ApiError(404, 'no_encontrado', 'No existe un reporte para esa semana.');
      const actividades = original.actividades.length ? original.actividades : this.actividadesDeSemana(practica, original);
      const evidencias: EvidenciaReporte[] = original.estado === 'sin_reporte' ? [] : (original.evidencias.length ? original.evidencias : [`informe-actividades-semana-${semana}.pdf`]).map((nombre) => ({ nombre, tamano: '0,9 MB', version: 1 }));
      return { practica, reporte: { ...original, actividades }, evidencias, tutorEntidad: practica.tutorEntidad };
    });
  }

  presentarInforme(practicaId: number, resumen: string, archivo: string): Observable<void> {
    return this.responder(() => {
      const practica = this.buscar(practicaId);
      if (practica.estado !== 'en_revision_final') {
        throw new ApiError(409, 'practica_no_en_revision_final', 'El informe final se habilita cuando la práctica pasa a revisión final.');
      }
      if (!resumen.trim() || !archivo.trim()) {
        throw new ApiError(400, 'validacion', 'Datos inválidos.', { informe: ['Complete el resumen y adjunte el informe en PDF.'] });
      }
    });
  }

  private responder<T>(obtener: () => T): Observable<T> {
    return timer(this.demoraMs).pipe(map(obtener));
  }

  private buscar(id: number): Practica {
    const practica = PRACTICAS_DE_LA_ESTUDIANTE.find((p) => p.id === id);
    if (!practica) throw new ApiError(404, 'no_encontrado', 'No encontrado.');
    return practica;
  }

  private actividades(practica: Practica): ActividadPlan[] {
    const detalle = DETALLE_PLAN[practica.id] ?? [];
    return practica.plan.actividades.map((descripcion, i) => ({ descripcion, herramientas: detalle[i]?.[0] ?? '', entregable: detalle[i]?.[1] ?? '' }));
  }

  /** La práctica laboral tuvo una versión devuelta antes de la aprobada; la comunitaria no. */
  private versionesPrevias(practica: Practica): VersionPlan[] {
    if (practica.tipo !== 'laboral') return [];
    return [{ numero: 1, estado: 'devuelta', enviadaEl: fecha(2026, 4, 6), decididaEl: fecha(2026, 4, 8), decididaPor: TUTOR_ACADEMICO, observacion: OBSERVACION_V1 }];
  }

  /** Actividades de ejemplo de una semana que aún no las detalla: salen del plan. */
  private actividadesDeSemana(practica: Practica, reporte: ReporteSemanal): string[] {
    if (reporte.estado === 'sin_reporte') return [];
    const plan = practica.plan.actividades;
    const primera = plan[(reporte.semana - 1) % plan.length];
    const segunda = plan[reporte.semana % plan.length];
    return plan.length > 1 ? [`Lunes y martes: ${minuscula(primera)}`, `Miércoles a viernes: ${minuscula(segunda)}`] : [primera];
  }
}

const minuscula = (texto: string): string => texto.charAt(0).toLowerCase() + texto.slice(1);
