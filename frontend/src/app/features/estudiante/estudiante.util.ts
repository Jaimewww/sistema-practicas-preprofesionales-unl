import { inject, Signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Params } from '@angular/router';
import { catchError, distinctUntilChanged, map, Observable, of, startWith, switchMap } from 'rxjs';
import { estadoDeError } from '../../core/errores';
import { cargando, exito, vacio, type EstadoUi } from '../../core/estado-ui';
import { avanceDe, CARRERA, ESTADO_PRACTICA, ESTADO_REPORTE, formatoFecha } from '../../core/demo';
import type { EstadoReporte, Practica, ReporteSemanal } from '../../core/demo';
import type { TipoInsignia } from '../../shared/ui';

/** Práctica que se muestra cuando la URL no trae `?p=`: la laboral. */
export const PRACTICA_POR_DEFECTO = 1;

/** Convierte un flujo de la API en el flujo de `EstadoUi` que pintan las pantallas. */
export function aEstado<T>(origen: Observable<T>, esVacio: (datos: T) => boolean = () => false): Observable<EstadoUi<T>> {
  return origen.pipe(
    map((datos) => (esVacio(datos) ? vacio<T>() : exito(datos))),
    catchError((e: unknown) => of(estadoDeError<T>(e))),
    startWith(cargando<T>()),
  );
}

/** Id de práctica de `?p=`; sin parámetro o inválido, la laboral. */
export function idPractica(valor: string | null): number {
  const n = Number(valor);
  return Number.isInteger(n) && n > 0 ? n : PRACTICA_POR_DEFECTO;
}

/** `?p=` para los enlaces; la práctica por defecto no lo lleva, así las pestañas coinciden con la URL sin parámetros. */
export const paramPractica = (id: number): Params | undefined => (id === PRACTICA_POR_DEFECTO ? undefined : { p: id });

export function tipoReporte(estado: EstadoReporte): TipoInsignia {
  return { validado: 'ok', en_revision: 'warn', devuelto: 'bad', sin_reporte: 'warn' }[estado] as TipoInsignia;
}

/** Texto del estado; en las tablas, «Devuelto» a secas como en el prototipo. */
export const textoReporte = (estado: EstadoReporte, corto = false): string => (corto && estado === 'devuelto' ? 'Devuelto' : ESTADO_REPORTE[estado]);

export function tipoPractica(p: Practica): TipoInsignia {
  switch (p.estado) {
    case 'cerrada':
      return 'ok';
    case 'cancelada':
      return 'bad';
    case 'asignada':
    case 'suspendida':
      return 'warn';
    default:
      return 'info';
  }
}

export const textoPractica = (p: Practica): string => ESTADO_PRACTICA[p.estado];

/** «Al día» o «Rezagada», según las horas validadas y en revisión frente a las esperadas. */
export const rezagada = (p: Practica): boolean => avanceDe(p).rezagada;

/** `MENDIETA SARANGO LUCIANA` → `Mendieta Sarango Luciana`. */
export const nombrePropio = (nombre: string): string => nombre.toLowerCase().replace(/(^|\s)(\S)/g, (_, espacio: string, letra: string) => espacio + letra.toUpperCase());

/** `FEIRNNR - COMPUTACIÓN - PRESENCIAL - Régimen 2019 - CICLO 4A` → `Computación · Presencial · Ciclo 4A`. */
export function carreraCorta(carrera = CARRERA): string {
  const [, nombre, modalidad, , ciclo] = carrera.split(' - ');
  const titulo = (t: string) => t.charAt(0) + t.slice(1).toLowerCase();
  return [titulo(nombre), titulo(modalidad), ciclo.replace(/^CICLO /, 'Ciclo ')].join(' · ');
}

export const textoTipo = (p: Practica): string => (p.tipo === 'laboral' ? 'Laboral' : 'Comunitaria');

/** `06/04 – 12/04` (sin año). */
export const rangoCorto = (r: Pick<ReporteSemanal, 'desde' | 'hasta'>): string => `${formatoFecha(r.desde).slice(0, 5)} – ${formatoFecha(r.hasta).slice(0, 5)}`;
/** `18/05/2026 – 24/05/2026`. */
export const rangoLargo = (r: Pick<ReporteSemanal, 'desde' | 'hasta'>): string => `${formatoFecha(r.desde)} – ${formatoFecha(r.hasta)}`;

const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
/** `25 – 31 de mayo` (o `29 de mayo – 04 de junio` si cruza de mes). */
export function rangoEnLetras(r: Pick<ReporteSemanal, 'desde' | 'hasta'>): string {
  const [, mesD, diaD] = r.desde.split('-');
  const [, mesH, diaH] = r.hasta.split('-');
  const mes = (m: string) => MESES[Number(m) - 1];
  return mesD === mesH ? `${diaD} – ${diaH} de ${mes(mesH)}` : `${diaD} de ${mes(mesD)} – ${diaH} de ${mes(mesH)}`;
}

export type Pendiente = { tipo: 'devuelto' | 'sin_reporte' | 'en_revision'; reporte: ReporteSemanal };

/** Lo que la estudiante tiene pendiente: reportes devueltos, la semana sin reportar y lo que espera validación. */
export function pendientes(p: Practica): Pendiente[] {
  const lista: Pendiente[] = [];
  for (const reporte of p.reportes) {
    if (reporte.estado === 'devuelto') lista.push({ tipo: 'devuelto', reporte });
  }
  for (const reporte of p.reportes) {
    if (reporte.estado === 'sin_reporte' && reporte.semana <= p.semanaActual) lista.push({ tipo: 'sin_reporte', reporte });
  }
  for (const reporte of p.reportes) {
    if (reporte.estado === 'en_revision') lista.push({ tipo: 'en_revision', reporte });
  }
  return lista;
}

export const requierenAccion = (lista: Pendiente[]): Pendiente[] => lista.filter((x) => x.tipo !== 'en_revision');

/** Estado de una carga que depende de `?p=`; llamar en un contexto de inyección (campo del componente). */
export function estadoPorPractica<T>(pedir: (practicaId: number) => Observable<T>, esVacio?: (datos: T) => boolean): Signal<EstadoUi<T>> {
  return toSignal(
    inject(ActivatedRoute).queryParamMap.pipe(
      map((q) => idPractica(q.get('p'))),
      distinctUntilChanged(),
      switchMap((id) => aEstado(pedir(id), esVacio)),
    ),
    { initialValue: cargando<T>() },
  );
}

/** `?p=` actual como señal; contexto de inyección. */
export function practicaActual(): Signal<number> {
  const ruta = inject(ActivatedRoute);
  return toSignal(ruta.queryParamMap.pipe(map((q) => idPractica(q.get('p')))), { initialValue: idPractica(ruta.snapshot.queryParamMap.get('p')) });
}

/** Parámetros de consulta de un enlace al reporte de una semana (E5). */
export const paramsReporte = (practicaId: number, semana: number): Params => ({ s: semana, ...paramPractica(practicaId) });
