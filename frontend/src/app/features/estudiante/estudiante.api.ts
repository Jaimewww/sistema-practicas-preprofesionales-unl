import { Observable } from 'rxjs';
import type { Practica } from '../../core/demo';
import type { ActividadPlan, PlanDetalle, PlanEditable, ReporteDetalle } from './estudiante.model';

/**
 * Contrato de datos del rol estudiante; se usa como token de inyección.
 * Las pantallas solo conocen esta clase: hoy la implementa `EstudianteMock` (el backend aún no
 * expone estas pantallas). Los errores llegan como `ApiError` y se pintan con `EstadoUi`.
 */
export abstract class EstudianteApi {
  /** Las prácticas de la estudiante (laboral y comunitaria son registros separados). */
  abstract misPracticas(): Observable<Practica[]>;
  abstract practica(id: number): Observable<Practica>;
  abstract plan(practicaId: number): Observable<PlanDetalle>;
  abstract planEditable(practicaId: number): Observable<PlanEditable>;
  /** Envía una nueva versión del plan a revisión del tutor académico. */
  abstract enviarPlan(practicaId: number, actividades: ActividadPlan[]): Observable<void>;
  abstract reporte(practicaId: number, semana: number): Observable<ReporteDetalle>;
  /** Presenta el informe final (solo con la práctica en revisión final). */
  abstract presentarInforme(practicaId: number, resumen: string, archivo: string): Observable<void>;
}
