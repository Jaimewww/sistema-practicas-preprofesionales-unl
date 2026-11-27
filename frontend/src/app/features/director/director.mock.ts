import { Injectable } from '@angular/core';
import { Observable, map, timer } from 'rxjs';
import { ApiError } from '../../core/api/envelope';
import { PRACTICAS_CARRERA } from '../../core/demo';
import type { Practica } from '../../core/demo';
import { DirectorApi } from './director.api';

/** Mock en memoria sobre los datos de demostración de la carrera. */
@Injectable()
export class DirectorMock extends DirectorApi {
  /** Espera simulada por defecto; los tests la ponen en 0 para no esperar. */
  static demoraPorDefecto = 400;
  demoraMs = DirectorMock.demoraPorDefecto;

  cierres(): Observable<Practica[]> {
    return this.responder(() => PRACTICAS_CARRERA.filter((p) => p.estado === 'cerrada'));
  }

  cierre(id: number): Observable<Practica> {
    return this.responder(() => {
      const practica = PRACTICAS_CARRERA.find((p) => p.id === id && p.estado === 'cerrada');
      if (!practica) throw new ApiError(404, 'no_encontrado', 'No encontrado.');
      return practica;
    });
  }

  private responder<T>(obtener: () => T): Observable<T> {
    return timer(this.demoraMs).pipe(map(obtener));
  }
}
