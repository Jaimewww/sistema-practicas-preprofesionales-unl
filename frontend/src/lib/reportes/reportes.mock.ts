import { ApiError } from '../api/envelope';
import type { HorasPractica, Reporte, ReporteCrear, ReportesApi } from './tipos';

const espera = (ms: number) => new Promise((r) => setTimeout(r, ms));

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
export class ReportesMock implements ReportesApi {
  private enviados = new Set<string>();
  private siguienteId = 1;

  async crear(practicaId: number, cuerpo: ReporteCrear): Promise<Reporte> {
    await espera(600);
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

  async horas(_practicaId: number): Promise<HorasPractica> {
    await espera(300);
    return {
      horas_validadas: 96,
      horas_en_revision: 12,
      horas_requeridas: 240,
      horas_faltantes: 144,
      semana_en_revision: true,
    };
  }
}
