import type { HorasPractica, Reporte, ReporteCrear, ReportesApi } from './tipos';

/**
 * Servicio real contra /api/v1/.            RESPONSABLE: Alejandro (F-002)
 *
 * Implementar con `pedir` de ../api/http:
 *   crear -> POST /practicas/{practicaId}/reportes/ con exactamente {semana, horas_reportadas}
 *   horas -> GET  /practicas/{practicaId}/horas/
 */
export class ReportesHttp implements ReportesApi {
  async crear(_practicaId: number, _cuerpo: ReporteCrear): Promise<Reporte> {
    throw new Error('Pendiente (Alejandro): POST /practicas/{id}/reportes/.');
  }

  async horas(_practicaId: number): Promise<HorasPractica> {
    throw new Error('Pendiente (Alejandro): GET /practicas/{id}/horas/.');
  }
}
