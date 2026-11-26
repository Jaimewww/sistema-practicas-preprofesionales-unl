import { Injectable, inject } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';
import type { HorasPractica, Reporte, ReporteCrear } from './reporte.model';
import { ReportesApi } from './reportes.api';

/**
 * Servicio real contra /api/v1/.            RESPONSABLE: Alejandro (F-002)
 *
 * Implementar con ApiClient:
 *   crear -> POST /practicas/{practicaId}/reportes/ con exactamente {semana, horas_reportadas}
 *   horas -> GET  /practicas/{practicaId}/horas/
 */
@Injectable()
export class ReportesHttp extends ReportesApi {
  protected readonly api = inject(ApiClient);

  crear(_practicaId: number, _cuerpo: ReporteCrear): Observable<Reporte> {
    return throwError(() => new Error('Pendiente (Alejandro): POST /practicas/{id}/reportes/.'));
  }

  horas(_practicaId: number): Observable<HorasPractica> {
    return throwError(() => new Error('Pendiente (Alejandro): GET /practicas/{id}/horas/.'));
  }
}
