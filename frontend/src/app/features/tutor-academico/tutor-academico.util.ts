import { inject, Signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Params } from '@angular/router';
import { catchError, distinctUntilChanged, map, Observable, of, startWith, switchMap } from 'rxjs';
import { estadoDeError } from '../../core/errores';
import { cargando, exito, vacio, type EstadoUi } from '../../core/estado-ui';
import { avanceDe, ESTADO_PRACTICA, ESTADO_REPORTE, ESTADOS_SOLO_LECTURA, formatoFecha } from '../../core/demo';
import type { EstadoPractica, EstadoReporte, Practica, TipoRevision } from '../../core/demo';
import type { TipoInsignia } from '../../shared/ui';
import type { EstadoRevision } from './tutor-academico.model';

/** Convierte un flujo de la API en el flujo de `EstadoUi` que pintan las pantallas. */
export function aEstado<T>(origen: Observable<T>, esVacio: (datos: T) => boolean = () => false): Observable<EstadoUi<T>> {
  return origen.pipe(
    map((datos) => (esVacio(datos) ? vacio<T>() : exito(datos))),
    catchError((e: unknown) => of(estadoDeError<T>(e))),
    startWith(cargando<T>()),
  );
}

/** Estado de una carga que depende de un parámetro de consulta (`?r=`, `?p=`); contexto de inyección. */
export function estadoPorParametro<T>(parametro: string, pedir: (valor: string) => Observable<T>, esVacio?: (datos: T) => boolean): Signal<EstadoUi<T>> {
  return toSignal(
    inject(ActivatedRoute).queryParamMap.pipe(
      map((q) => q.get(parametro) ?? ''),
      distinctUntilChanged(),
      switchMap((valor) => aEstado(pedir(valor), esVacio)),
    ),
    { initialValue: cargando<T>() },
  );
}

/** `?r=` / `?p=` para los enlaces; la clave por defecto no lo lleva. */
export const parametro = (nombre: string, clave: string | number, porDefecto: string | number): Params | undefined => (String(clave) === String(porDefecto) ? undefined : { [nombre]: clave });

const minusculas = (t: string): string => t.charAt(0) + t.slice(1).toLowerCase();

/** `MENDIETA SARANGO LUCIANA BELÉN` → `Luciana Mendieta`. */
export function nombreCorto(nombre: string): string {
  const [apellido, , primero] = nombre.split(' ');
  return `${minusculas(primero ?? apellido)} ${minusculas(apellido)}`;
}

/** `MENDIETA SARANGO LUCIANA BELÉN` → `Luciana`. */
export const primerNombre = (nombre: string): string => minusculas(nombre.split(' ')[2] ?? nombre);

const SUBTIPO: Record<string, string> = { ayudantia_docencia: 'Ayudantía de docencia', ayudantia_investigacion: 'Ayudantía de investigación', pasantia: 'Pasantía' };

/** `Ayudantía de docencia`, `Pasantía`; sin subtipo, el tipo de práctica. */
export const subtipoTexto = (p: Practica): string => SUBTIPO[p.subtipo] ?? (p.tipo === 'laboral' ? 'Práctica laboral' : 'Práctica comunitaria');

/** `Laboral: Ayudantía de docencia`, `Comunitaria`. */
export const descripcionPractica = (p: Practica): string => (p.tipo === 'laboral' ? `Laboral: ${SUBTIPO[p.subtipo] ?? 'Práctica laboral'}` : 'Comunitaria');

/** `Práctica laboral (ayudantía de docencia) en Universidad…`. */
export function practicaEnEntidad(p: Practica): string {
  if (p.tipo === 'comunitaria') return `Práctica comunitaria en ${p.entidad}`;
  const subtipo = SUBTIPO[p.subtipo];
  return `Práctica laboral${subtipo ? ` (${subtipo.toLowerCase()})` : ''} en ${p.entidad}`;
}

export const nombrePropio = (nombre: string): string => nombre.toLowerCase().replace(/(^|\s)(\S)/g, (_, espacio: string, letra: string) => espacio + letra.toUpperCase());

export function tipoPractica(estado: EstadoPractica): TipoInsignia {
  switch (estado) {
    case 'cerrada':
      return 'ok';
    case 'cancelada':
    case 'suspendida':
      return 'bad';
    case 'en_revision_final':
      return 'warn';
    default:
      return 'info';
  }
}
export const textoPractica = (estado: EstadoPractica): string => ESTADO_PRACTICA[estado];

export function tipoReporte(estado: EstadoReporte): TipoInsignia {
  return { validado: 'ok', en_revision: 'warn', devuelto: 'bad', sin_reporte: 'bad' }[estado] as TipoInsignia;
}
export const textoReporte = (estado: EstadoReporte): string => ESTADO_REPORTE[estado];

export const tipoRevision = (estado: EstadoRevision): TipoInsignia => ({ validado: 'ok', en_revision: 'warn', devuelto: 'bad' })[estado] as TipoInsignia;
export const textoRevision = (estado: EstadoRevision): string => ({ validado: 'Validado', en_revision: 'En revisión', devuelto: 'Devuelto con observación' })[estado];

/** «Confirmado», «Por confirmar» o «—» (sin reporte). */
export const confirmacion = (c: boolean | null): { tipo: TipoInsignia; texto: string } | null => (c === null ? null : c ? { tipo: 'ok', texto: 'Confirmado' } : { tipo: 'warn', texto: 'Por confirmar' });

/** Una práctica en curso con horas por debajo del mínimo. */
export const rezagada = (p: Practica): boolean => p.estado === 'en_curso' && avanceDe(p).rezagada;

export type ClaveAvance = 'rezagada' | 'aldia' | 'otro';
export const claveAvance = (p: Practica): ClaveAvance => (p.estado !== 'en_curso' ? 'otro' : avanceDe(p).rezagada ? 'rezagada' : 'aldia');

/** Insignia del avance de horas en «Mis tutorados». */
export function avanceTexto(p: Practica): { tipo: TipoInsignia; texto: string } {
  const clave = claveAvance(p);
  if (clave === 'rezagada') return { tipo: 'bad', texto: 'Rezagada' };
  if (clave === 'aldia') return { tipo: 'ok', texto: 'Al día' };
  if (p.plan.estado !== 'validado') return { tipo: 'info', texto: 'Sin plan aprobado' };
  if (avanceDe(p).validadas >= p.horasRequeridas) return { tipo: 'ok', texto: 'Horas completas' };
  return { tipo: 'info', texto: ESTADO_PRACTICA[p.estado] };
}

/** El texto del aviso de las prácticas que ya no admiten cambios (suspendida, cancelada, cerrada). */
export function avisoSoloLectura(p: Practica): { titulo: string; texto: string } | null {
  if (!ESTADOS_SOLO_LECTURA.includes(p.estado)) return null;
  const entrada = [...p.historial].reverse().find((e) => e.estadoNuevo === p.estado);
  const verbo = { suspendida: 'suspendió', cancelada: 'canceló', cerrada: 'cerró' }[p.estado as 'suspendida'];
  const estado = ESTADO_PRACTICA[p.estado].toLowerCase();
  const cuando = entrada ? ` el ${formatoFecha(entrada.fecha)}` : '';
  const motivo = entrada?.motivo ? ` por ${entrada.motivo}` : '';
  return { titulo: `Práctica ${estado}: solo lectura.`, texto: `Ejemplo del estado (la coordinación ${verbo} la práctica${cuando}${motivo}). No admite revisiones ni evaluación.` };
}

/** `25/05/2026 - 31/05/2026`. */
export const rangoLargo = (r: { desde: string; hasta: string }): string => `${formatoFecha(r.desde)} - ${formatoFecha(r.hasta)}`;

/** Ruta de la pantalla que revisa un plan, reporte o informe. */
export const rutaRevision = (tipo: TipoRevision): string => `/tutor-academico/revisar/${tipo}`;

/** Listo para la evaluación final: en revisión final, con el informe validado y el externo registrado. */
export const listoParaEvaluar = (p: Practica): boolean => p.estado === 'en_revision_final' && p.informeFinal?.estado === 'validado' && !!p.informeExterno && !p.evaluacion;
