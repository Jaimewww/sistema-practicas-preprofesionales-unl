import { Observable } from 'rxjs';
import type { ConfiguracionCarrera } from '../../core/demo';
import type { DetallePractica, FilaAlerta, FilaConsolidado, FilaPractica, ResumenCarrera } from './coordinador.model';

/**
 * Contrato de datos del rol coordinador; se usa como token de inyección.
 * Hoy lo implementa `CoordinadorMock` (el backend aún no expone estas pantallas). Los errores
 * llegan como `ApiError` y se pintan con `EstadoUi`.
 */
export abstract class CoordinadorApi {
  abstract resumen(): Observable<ResumenCarrera>;
  /** Las prácticas de la carrera (RF-06). */
  abstract practicas(): Observable<FilaPractica[]>;
  abstract alertas(): Observable<FilaAlerta[]>;
  abstract practica(id: number): Observable<DetallePractica>;
  /** Suspende una práctica en curso; el motivo es obligatorio (RF-13). */
  abstract suspender(id: number, motivo: string): Observable<DetallePractica>;
  /** Cancela una práctica suspendida; el motivo es obligatorio (RF-13). */
  abstract cancelar(id: number, motivo: string): Observable<DetallePractica>;
  abstract reanudar(id: number): Observable<DetallePractica>;
  /** Cierra la práctica conservando el resultado de la evaluación (RF-09). */
  abstract cerrar(id: number, evaluacion: number): Observable<DetallePractica>;
  abstract consolidado(): Observable<FilaConsolidado[]>;
  abstract configuracion(): Observable<ConfiguracionCarrera>;
  abstract guardarConfiguracion(config: ConfiguracionCarrera): Observable<ConfiguracionCarrera>;
}
