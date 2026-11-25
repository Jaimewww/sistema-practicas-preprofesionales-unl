import type { Practica, PracticasApi } from './tipos';

/**
 * Servicio real.            RESPONSABLE: Doménica (F-001)
 *
 * Implementar con `pedir` de ../api/http: GET /practicas/ (lista visible para el usuario).
 */
export class PracticasHttp implements PracticasApi {
  async listar(): Promise<Practica[]> {
    throw new Error('Pendiente (Doménica): GET /practicas/.');
  }
}
