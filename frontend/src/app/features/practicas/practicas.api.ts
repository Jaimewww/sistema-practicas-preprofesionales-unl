import type { Observable } from 'rxjs';
import type { Practica } from './practica.model';

/** Token de inyección del servicio de prácticas (ver ReportesApi). */
export abstract class PracticasApi {
  /** Lista vacía = estado «vacío», no error. */
  abstract listar(): Observable<Practica[]>;
}
