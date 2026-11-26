import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';
import type { Practica } from './practica.model';
import { PracticasApi } from './practicas.api';

/**
 * Servicio real.            RESPONSABLE: Doménica (F-001)
 *
 * Implementar con ApiClient: GET /practicas/ (lista visible para el usuario).
 */
@Injectable()
export class PracticasHttp extends PracticasApi {
  protected readonly api = inject(ApiClient);

  listar(): Observable<Practica[]> {
    return this.api.get<Practica[]>('/practicas/');
  }
}
