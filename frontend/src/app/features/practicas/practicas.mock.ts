import { Injectable } from '@angular/core';
import { Observable, map, timer } from 'rxjs';
import type { Practica } from './practica.model';
import { PracticasApi } from './practicas.api';

/** Dos prácticas de ejemplo; la 409 simula una práctica que ya no está en curso. */
@Injectable()
export class PracticasMock extends PracticasApi {
  listar(): Observable<Practica[]> {
    return timer(400).pipe(
      map(() => [
        { id: 1, estudiante_id: 7, tipo: 'practica_laboral', subtipo: 'empresa', estado: 'en_curso', horas_requeridas: 240 },
        { id: 409, estudiante_id: 7, tipo: 'servicio_comunitario', subtipo: 'proyecto', estado: 'cerrada', horas_requeridas: 160 },
      ]),
    );
  }
}
