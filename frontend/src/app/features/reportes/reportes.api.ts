import type { Observable } from 'rxjs';
import type { HorasPractica, Reporte, ReporteCrear } from './reporte.model';

/**
 * Lo que el componente necesita del servicio. Es una clase abstracta para usarla
 * como token de inyección: app.config.ts decide si se inyecta ReportesHttp o
 * ReportesMock según environment.useMock. Los componentes hacen
 * `inject(ReportesApi)`, nunca inyectan la clase concreta.
 */
export abstract class ReportesApi {
  abstract crear(practicaId: number, cuerpo: ReporteCrear): Observable<Reporte>;
  abstract horas(practicaId: number): Observable<HorasPractica>;
}
