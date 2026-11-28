import { catchError, map, Observable, of, startWith } from 'rxjs';
import { estadoDeError } from '../../core/errores';
import { cargando, exito, vacio, type EstadoUi } from '../../core/estado-ui';
import { etiquetaEstadoPractica } from '../../core/demo';
import type { Anexo, Practica } from '../../core/demo';
import type { TipoInsignia } from '../../shared/ui';

/** Convierte un flujo de la API en el flujo de `EstadoUi` que pintan las pantallas. */
export function aEstado<T>(origen: Observable<T>, esVacio: (datos: T) => boolean = () => false): Observable<EstadoUi<T>> {
  return origen.pipe(
    map((datos) => (esVacio(datos) ? vacio<T>() : exito(datos))),
    catchError((e: unknown) => of(estadoDeError<T>(e))),
    startWith(cargando<T>()),
  );
}

/** Color del estado del anexo; el texto y el ícono van siempre con él. */
export const tipoAnexo = (a: Pick<Anexo, 'estado'>): TipoInsignia => (a.estado === 'legalizado' ? 'ok' : 'warn');

export const textoTipo = (p: Pick<Practica, 'tipo'>): string => (p.tipo === 'laboral' ? 'Laboral' : 'Comunitaria');

export const textoEstadoPractica = (p: Practica): string => etiquetaEstadoPractica(p);

/** Id de anexo de `?a=`; sin parámetro o inválido, `null`. */
export function idAnexo(valor: string | null): number | null {
  const n = Number(valor);
  return valor !== null && Number.isInteger(n) && n > 0 ? n : null;
}
