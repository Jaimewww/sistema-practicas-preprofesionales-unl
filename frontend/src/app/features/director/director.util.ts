import { inject, Signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute } from '@angular/router';
import { catchError, distinctUntilChanged, map, Observable, of, startWith, switchMap } from 'rxjs';
import { estadoDeError } from '../../core/errores';
import { cargando, exito, vacio, type EstadoUi } from '../../core/estado-ui';
import { RESULTADO_PRACTICA, type Practica, type ResultadoPractica, type Subtipo } from '../../core/demo';
import type { TipoInsignia } from '../../shared/ui';

/** Práctica que se muestra cuando la URL no trae `?p=`: la pasantía aprobada del prototipo. */
export const CIERRE_POR_DEFECTO = 8;

/** Convierte un flujo de la API en el flujo de `EstadoUi` que pintan las pantallas. */
export function aEstado<T>(origen: Observable<T>, esVacio: (datos: T) => boolean = () => false): Observable<EstadoUi<T>> {
  return origen.pipe(
    map((datos) => (esVacio(datos) ? vacio<T>() : exito(datos))),
    catchError((e: unknown) => of(estadoDeError<T>(e))),
    startWith(cargando<T>()),
  );
}

/** Id de `?p=`; sin parámetro o inválido, el cierre por defecto. */
export function idCierre(valor: string | null): number {
  const n = Number(valor);
  return Number.isInteger(n) && n > 0 ? n : CIERRE_POR_DEFECTO;
}

/** Signal con el id de `?p=` de la URL actual. */
export const cierreActual = (): Signal<number> => {
  const ruta = inject(ActivatedRoute);
  return toSignal(ruta.queryParamMap.pipe(map((q) => idCierre(q.get('p'))), distinctUntilChanged()), { initialValue: CIERRE_POR_DEFECTO });
};

/** Carga el cierre de `?p=` y vuelve a cargarlo si cambia. */
export function estadoPorCierre(cargar: (id: number) => Observable<Practica>): Signal<EstadoUi<Practica>> {
  const ruta = inject(ActivatedRoute);
  const flujo = ruta.queryParamMap.pipe(
    map((q) => idCierre(q.get('p'))),
    distinctUntilChanged(),
    switchMap((id) => aEstado(cargar(id))),
  );
  return toSignal(flujo, { initialValue: cargando<Practica>() });
}

export const textoResultado = (r: ResultadoPractica | ''): string => (r ? RESULTADO_PRACTICA[r] : 'Sin resultado');
export const tipoResultado = (r: ResultadoPractica | ''): TipoInsignia => (r === 'aprobada' ? 'ok' : r === 'no_aprobada' ? 'bad' : 'warn');

const SUBTIPOS: Record<Subtipo, string> = { '': '', ayudantia_docencia: 'Ayudantía de docencia', ayudantia_investigacion: 'Ayudantía de investigación', pasantia: 'Pasantía' };

export const textoTipo = (p: Pick<Practica, 'tipo'>): string => (p.tipo === 'laboral' ? 'Laboral' : 'Comunitaria');
/** `Laboral: Pasantía` o `Comunitaria`. */
export const textoTipoLargo = (p: Pick<Practica, 'tipo' | 'subtipo'>): string => (SUBTIPOS[p.subtipo] ? `${textoTipo(p)}: ${SUBTIPOS[p.subtipo]}` : textoTipo(p));

/** Entidad y proyecto de la práctica, sin partes vacías: `GAD Municipal · Alfabetización digital`. */
export const detalleEntidad = (p: Pick<Practica, 'entidad' | 'proyectoVinculacion'>): string => [p.entidad, p.proyectoVinculacion].filter(Boolean).join(' · ');
