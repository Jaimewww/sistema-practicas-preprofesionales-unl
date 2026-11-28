import { Injectable } from '@angular/core';
import { map, Observable, timer } from 'rxjs';
import { ApiError } from '../../core/api/envelope';
import { HOY, PRACTICAS_CARRERA, SECRETARIA } from '../../core/demo';
import type { Anexo } from '../../core/demo';
import { SecretariaApi } from './secretaria.api';
import type { FilaAnexo, ResumenSecretaria } from './secretaria.model';

/** Mock en memoria sobre `core/demo`: las legalizaciones de la sesión viven en el servicio. */
@Injectable()
export class SecretariaMock extends SecretariaApi {
  /** Espera simulada por defecto; los tests la ponen en 0 para no esperar. */
  static demoraPorDefecto = 400;
  demoraMs = SecretariaMock.demoraPorDefecto;
  /** Anexos legalizados en esta sesión (id → anexo ya legalizado). */
  private readonly legalizados = new Map<number, Anexo>();

  private filas(): FilaAnexo[] {
    return PRACTICAS_CARRERA.flatMap((practica) => practica.anexos.map((a) => ({ anexo: this.legalizados.get(a.id) ?? a, practica })));
  }

  private buscar(id: number): FilaAnexo {
    const fila = this.filas().find((f) => f.anexo.id === id);
    if (!fila) throw new ApiError(404, 'no_encontrado', 'No existe el anexo solicitado.');
    return fila;
  }

  resumen(): Observable<ResumenSecretaria> {
    return this.responder(() => {
      const filas = this.filas();
      const pendientes = filas.filter((f) => f.anexo.estado === 'pendiente');
      return {
        porLegalizar: pendientes.length,
        legalizados: filas.length - pendientes.length,
        practicasConAnexos: new Set(filas.map((f) => f.practica.id)).size,
        siguientes: pendientes.slice(0, 4),
      };
    });
  }

  anexos(): Observable<FilaAnexo[]> {
    return this.responder(() => this.filas());
  }

  anexo(id: number): Observable<FilaAnexo> {
    return this.responder(() => this.buscar(id));
  }

  legalizar(id: number): Observable<FilaAnexo> {
    return this.responder(() => {
      const fila = this.buscar(id);
      if (fila.anexo.estado === 'legalizado') throw new ApiError(409, 'anexo_legalizado', 'Este anexo ya fue legalizado. No se puede modificar (RF-20).');
      this.legalizados.set(id, { ...fila.anexo, estado: 'legalizado', legalizadoPor: SECRETARIA, legalizadoEl: HOY });
      return this.buscar(id);
    });
  }

  private responder<T>(obtener: () => T): Observable<T> {
    return timer(this.demoraMs).pipe(map(obtener));
  }
}
