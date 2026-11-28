import { Observable } from 'rxjs';
import type { FilaAnexo, ResumenSecretaria } from './secretaria.model';

/**
 * Contrato de datos del rol secretaría; se usa como token de inyección.
 * Hoy lo implementa `SecretariaMock` (el backend aún no expone estas pantallas). Los errores
 * llegan como `ApiError` y se pintan con `EstadoUi`.
 */
export abstract class SecretariaApi {
  abstract resumen(): Observable<ResumenSecretaria>;
  /** Los anexos de cierre de las prácticas en revisión final o cerradas. */
  abstract anexos(): Observable<FilaAnexo[]>;
  abstract anexo(id: number): Observable<FilaAnexo>;
  /** Legaliza el anexo y registra quién y cuándo. Es de una sola vez (RF-20): si ya está legalizado, falla. */
  abstract legalizar(id: number): Observable<FilaAnexo>;
}
