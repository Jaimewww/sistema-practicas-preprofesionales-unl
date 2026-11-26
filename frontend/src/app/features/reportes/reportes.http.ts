import { Injectable, inject } from '@angular/core';
import type { Observable } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';
import type { HorasPractica, Reporte, ReporteCrear } from './reporte.model';
import { ReportesApi } from './reportes.api';

/**
 * Servicio real contra /api/v1/.            RESPONSABLE: Alejandro (F-002)
 *
 * Contrato (GET /api/v1/schema/):
 *   crear -> POST /practicas/{practica_id}/reportes/  cuerpo {semana, horas_reportadas} -> 201 Reporte
 *   horas -> GET  /practicas/{practica_id}/horas/                                       -> 200 HorasPractica
 * ApiClient desenvuelve `data` del envelope y apiErrorInterceptor convierte 400/401/403/404/409 en ApiError.
 */
@Injectable()
export class ReportesHttp extends ReportesApi {
  private readonly api = inject(ApiClient);

  crear(practicaId: number, { semana, horas_reportadas }: ReporteCrear): Observable<Reporte> {
    // Solo los dos campos escribibles: si se cuela uno de solo lectura, el serializer responde 400.
    return this.api.post<Reporte>(`/practicas/${practicaId}/reportes/`, { semana, horas_reportadas });
  }

  horas(practicaId: number): Observable<HorasPractica> {
    return this.api.get<HorasPractica>(`/practicas/${practicaId}/horas/`);
  }
}
