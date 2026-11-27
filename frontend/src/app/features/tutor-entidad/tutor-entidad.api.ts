import { Observable } from 'rxjs';
import type { Practica } from '../../core/demo';
import type { ArchivoInforme, Confirmacion, RegistroIncumplimiento, RegistroInformeExterno, ReporteConfirmable } from './tutor-entidad.model';

/**
 * Contrato de datos del rol tutor de la entidad; se usa como token de inyección.
 * Las pantallas solo conocen esta clase: hoy la implementa `TutorEntidadMock` (el backend aún no
 * expone estas pantallas). Los errores llegan como `ApiError` y se pintan con `EstadoUi`.
 */
export abstract class TutorEntidadApi {
  /** Practicantes de práctica laboral a cargo de la tutora (la comunitaria no tiene tutor de la entidad). */
  abstract practicantes(): Observable<Practica[]>;
  /** Reportes semanales que la tutora aún no confirma. */
  abstract reportesPorConfirmar(): Observable<ReporteConfirmable[]>;
  /** Un reporte (por confirmar, ya confirmado o devuelto) por su código de URL, p. ej. `l8`. */
  abstract reporte(codigo: string): Observable<ReporteConfirmable>;
  /** Confirma que el practicante hizo las actividades; queda registrado quién y cuándo. */
  abstract confirmarReporte(codigo: string): Observable<Confirmacion>;
  /** Registra el informe final del tutor de la entidad (valoración y PDF firmado de hasta 5 MB). */
  abstract registrarInformeExterno(practicaId: number, valoracion: string, archivo: ArchivoInforme): Observable<RegistroInformeExterno>;
  /** Reporta un incumplimiento del practicante y avisa a su tutor académico. */
  abstract reportarIncumplimiento(practicaId: number, descripcion: string): Observable<RegistroIncumplimiento>;
}
