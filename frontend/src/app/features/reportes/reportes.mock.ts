import { Injectable } from '@angular/core';
import { Observable, map, timer } from 'rxjs';
import { ApiError } from '../../core/api/envelope';
import type { HorasPractica, Reporte, ReporteCrear } from './reporte.model';
import { ReportesApi } from './reportes.api';

/**
 * Mock con las mismas respuestas que el backend real, para trabajar sin servidor.
 *
 * Escenarios (ver README):
 *   practicaId 404          -> 404 no_encontrado
 *   practicaId 409          -> 409 practica_no_en_curso
 *   semana ya enviada       -> 409 semana_duplicada
 *   horas fuera de 1..168   -> 400 en horas_reportadas
 *   horas > 40              -> 201 con requiere_revision: true
 */
@Injectable()
export class ReportesMock extends ReportesApi {
  private readonly enviados = new Set<string>();
  private siguienteId = 1;
  /** Milisegundos de espera simulada; los tests lo ponen en 0. */
  demoraMs = 600;

  crear(practicaId: number, cuerpo: ReporteCrear): Observable<Reporte> {
    return timer(this.demoraMs).pipe(map(() => this.responder(practicaId, cuerpo)));
  }

  horas(_practicaId: number): Observable<HorasPractica> {
    return timer(this.demoraMs / 2).pipe(
      map(() => ({
        horas_validadas: 96,
        horas_en_revision: 12,
        horas_requeridas: 240,
        horas_faltantes: 144,
        semana_en_revision: true,
      })),
    );
  }

  private responder(practicaId: number, cuerpo: ReporteCrear): Reporte {
    if (practicaId === 404) {
      throw new ApiError(404, 'no_encontrado', 'No se encontró el recurso solicitado.');
    }
    if (practicaId === 409) {
      throw new ApiError(409, 'practica_no_en_curso', 'La práctica no está en curso.');
    }
    if (cuerpo.horas_reportadas < 1 || cuerpo.horas_reportadas > 168) {
      throw new ApiError(400, 'validacion', 'Datos inválidos.', {
        horas_reportadas: ['Una semana tiene 168 horas: no se pueden reportar más.'],
      });
    }
    const clave = `${practicaId}-${cuerpo.semana}`;
    if (this.enviados.has(clave)) {
      throw new ApiError(409, 'semana_duplicada', 'Ya existe un reporte para esa semana.');
    }
    this.enviados.add(clave);
    return {
      id: this.siguienteId++,
      practica_id: practicaId,
      ...cuerpo,
      estado: 'en_revision',
      requiere_revision: cuerpo.horas_reportadas > 40,
      fecha_registro: new Date().toISOString(),
    };
  }
}
