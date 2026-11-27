import { Observable } from 'rxjs';
import type { Practica } from '../../core/demo';

/**
 * Contrato de datos del director de carrera; se usa como token de inyección.
 * El rol solo consulta: no hay operaciones que modifiquen datos. Los errores llegan como `ApiError`.
 */
export abstract class DirectorApi {
  /** Las prácticas cerradas de la carrera del director, con su resultado. */
  abstract cierres(): Observable<Practica[]>;
  /** El cierre de una práctica cerrada de la carrera (404 si no existe o no está cerrada). */
  abstract cierre(id: number): Observable<Practica>;
}
