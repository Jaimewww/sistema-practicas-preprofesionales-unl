import { Observable } from 'rxjs';
import type { Practica, TipoRevision } from '../../core/demo';
import type { AccionRevision, DatosEvaluacion, DetallePractica, Pendiente, ResultadoEvaluacion, Revision } from './tutor-academico.model';

/**
 * Contrato de datos del rol tutor académico; se usa como token de inyección.
 * Las pantallas solo conocen esta clase: hoy la implementa `TutorAcademicoMock` (el backend aún no
 * expone estas pantallas). Los errores llegan como `ApiError` y se pintan con `EstadoUi`.
 */
export abstract class TutorAcademicoApi {
  /** Las prácticas en las que la persona es tutora académica. */
  abstract tutorados(): Observable<Practica[]>;
  /** Planes, reportes e informes en revisión, del más antiguo al más nuevo. */
  abstract pendientes(): Observable<Pendiente[]>;
  /** T2: un plan, reporte o informe; `clave` es el valor de `?r=`. */
  abstract revision(tipo: TipoRevision, clave: string): Observable<Revision>;
  /** Valida o devuelve; devolver exige una observación. Entrega la revisión ya decidida. */
  abstract decidir(tipo: TipoRevision, clave: string, accion: AccionRevision, observacion: string): Observable<Revision>;
  /** T4: la práctica de un tutorado; `clave` es el valor de `?p=`. */
  abstract practica(clave: string): Observable<DetallePractica>;
  /** T5: datos para la evaluación final. */
  abstract evaluacion(practicaId: number): Observable<DatosEvaluacion>;
  /** Registra la evaluación final; sin los informes exigidos falla con `ApiError`. */
  abstract registrarEvaluacion(practicaId: number, porcentaje: number): Observable<ResultadoEvaluacion>;
}
