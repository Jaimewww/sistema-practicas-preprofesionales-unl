import { Injectable } from '@angular/core';
import { Observable, map, timer } from 'rxjs';
import { ApiError } from '../../core/api/envelope';
import { ESTADOS_VIGENTES, fecha, HOY, PRACTICAS_DE_EJEMPLO, TUTOR_ENTIDAD } from '../../core/demo';
import type { Practica } from '../../core/demo';
import { TutorEntidadApi } from './tutor-entidad.api';
import type { ArchivoInforme, Confirmacion, RegistroIncumplimiento, RegistroInformeExterno, ReporteConfirmable } from './tutor-entidad.model';
import { errorDeArchivo } from './tutor-entidad.util';

/** Letra de cada practicante en el `?r=` del prototipo (`l8` = Luciana, semana 8; `d7` = Diego, semana 7). */
const LETRA: Record<number, string> = { 1: 'l', 3: 'd' };
/** Confirmaciones que ya existían en los datos de ejemplo (Diego · semana 8, confirmada el 02/06/2026). */
const CONFIRMADAS_ANTES: Record<string, Confirmacion> = { d8: { por: TUTOR_ENTIDAD, el: fecha(2026, 6, 2) } };

export const codigoDeReporte = (practicaId: number, semana: number): string => `${LETRA[practicaId] ?? 'p' + practicaId + '-'}${semana}`;

/** Mock en memoria: la tutora de la entidad de la demostración (Martha Celi) y sus dos practicantes. */
@Injectable()
export class TutorEntidadMock extends TutorEntidadApi {
  /** Espera simulada por defecto; los tests la ponen en 0 para no esperar. */
  static demoraPorDefecto = 400;
  demoraMs = TutorEntidadMock.demoraPorDefecto;

  private readonly confirmadas = new Map<string, Confirmacion>(Object.entries(CONFIRMADAS_ANTES));
  private readonly informes = new Map<number, RegistroInformeExterno & { valoracion: string }>();
  private readonly incumplimientos = new Map<number, Practica['incumplimientos']>();

  practicantes(): Observable<Practica[]> {
    return this.responder(() => this.misPracticantes());
  }

  reportesPorConfirmar(): Observable<ReporteConfirmable[]> {
    return this.responder(() => this.todosLosReportes().filter((r) => r.reporte.confirmadoPorEntidad === false && !r.confirmacion));
  }

  reporte(codigo: string): Observable<ReporteConfirmable> {
    return this.responder(() => this.buscarReporte(codigo));
  }

  confirmarReporte(codigo: string): Observable<Confirmacion> {
    return this.responder(() => {
      const r = this.buscarReporte(codigo);
      if (r.confirmacion) throw new ApiError(409, 'reporte_ya_confirmado', 'El reporte ya está confirmado.');
      if (r.reporte.estado === 'devuelto') throw new ApiError(409, 'reporte_devuelto', 'El reporte fue devuelto con observación: el practicante debe corregirlo.');
      const confirmacion: Confirmacion = { por: TUTOR_ENTIDAD, el: HOY };
      this.confirmadas.set(codigo, confirmacion);
      return confirmacion;
    });
  }

  registrarInformeExterno(practicaId: number, valoracion: string, archivo: ArchivoInforme): Observable<RegistroInformeExterno> {
    return this.responder(() => {
      this.buscarPracticante(practicaId);
      const errores: Record<string, string[]> = {};
      if (!valoracion.trim()) errores['valoracion'] = ['Describa la valoración del desempeño.'];
      const errorArchivo = errorDeArchivo(archivo);
      if (errorArchivo) errores['archivo'] = [errorArchivo];
      if (Object.keys(errores).length) throw new ApiError(400, 'validacion', 'Datos inválidos.', errores);
      const registro = { registradoPor: TUTOR_ENTIDAD, registradoEl: HOY, archivo: archivo.nombre };
      this.informes.set(practicaId, { ...registro, valoracion: valoracion.trim() });
      return registro;
    });
  }

  reportarIncumplimiento(practicaId: number, descripcion: string): Observable<RegistroIncumplimiento> {
    return this.responder(() => {
      const practica = this.buscarPracticante(practicaId);
      if (!descripcion.trim()) throw new ApiError(400, 'validacion', 'Datos inválidos.', { descripcion: ['Describa el incumplimiento.'] });
      const nuevo = { descripcion: descripcion.trim(), reportadoPor: TUTOR_ENTIDAD, reportadoEl: HOY };
      this.incumplimientos.set(practicaId, [...(this.incumplimientos.get(practicaId) ?? []), nuevo]);
      return { reportadoPor: nuevo.reportadoPor, reportadoEl: nuevo.reportadoEl, avisadoA: practica.tutorAcademico };
    });
  }

  private responder<T>(obtener: () => T): Observable<T> {
    return timer(this.demoraMs).pipe(map(obtener));
  }

  /** Prácticas laborales vigentes cuyo tutor de la entidad es la tutora de la demostración, con lo registrado en esta sesión. */
  private misPracticantes(): Practica[] {
    return PRACTICAS_DE_EJEMPLO.filter((p) => p.tutorEntidad === TUTOR_ENTIDAD && p.tipo === 'laboral' && ESTADOS_VIGENTES.includes(p.estado)).map((p) => {
      const informe = this.informes.get(p.id);
      return {
        ...p,
        informeExterno: informe ? { registradoPor: informe.registradoPor, registradoEl: informe.registradoEl, valoracion: informe.valoracion, archivo: informe.archivo } : p.informeExterno,
        incumplimientos: [...p.incumplimientos, ...(this.incumplimientos.get(p.id) ?? [])],
      };
    });
  }

  private buscarPracticante(id: number): Practica {
    const practica = this.misPracticantes().find((p) => p.id === id);
    if (!practica) throw new ApiError(404, 'no_encontrado', 'No encontrado.');
    return practica;
  }

  /** Todos los reportes enviados de sus practicantes; la confirmación sale de los datos o de esta sesión. */
  private todosLosReportes(): ReporteConfirmable[] {
    return this.misPracticantes().flatMap((practica) =>
      practica.reportes
        .filter((r) => r.estado !== 'sin_reporte')
        .map((reporte) => {
          const codigo = codigoDeReporte(practica.id, reporte.semana);
          const previa = this.confirmadas.get(codigo);
          const confirmacion = previa ?? (reporte.confirmadoPorEntidad ? { por: TUTOR_ENTIDAD, el: reporte.validadoEl ?? reporte.enviadoEl ?? HOY } : null);
          return { codigo, practica, reporte, confirmacion };
        }),
    );
  }

  private buscarReporte(codigo: string): ReporteConfirmable {
    const r = this.todosLosReportes().find((x) => x.codigo === codigo);
    if (!r) throw new ApiError(404, 'no_encontrado', 'No existe ese reporte.');
    return r;
  }
}
