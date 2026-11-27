import { inject, Signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Params } from '@angular/router';
import { catchError, distinctUntilChanged, map, Observable, of, startWith, switchMap } from 'rxjs';
import { estadoDeError } from '../../core/errores';
import { cargando, exito, vacio, type EstadoUi } from '../../core/estado-ui';
import { etiquetaEstadoPractica, TIPOS_ALERTA } from '../../core/demo';
import type { ConfiguracionCarrera, EstadoPractica, Practica, Subtipo, TipoAlerta } from '../../core/demo';
import type { TipoInsignia } from '../../shared/ui';

/** Práctica que se muestra cuando la URL no trae `?p=`: la que espera el cierre (como en el prototipo). */
export const PRACTICA_POR_DEFECTO = 7;

/** Convierte un flujo de la API en el flujo de `EstadoUi` que pintan las pantallas. */
export function aEstado<T>(origen: Observable<T>, esVacio: (datos: T) => boolean = () => false): Observable<EstadoUi<T>> {
  return origen.pipe(
    map((datos) => (esVacio(datos) ? vacio<T>() : exito(datos))),
    catchError((e: unknown) => of(estadoDeError<T>(e))),
    startWith(cargando<T>()),
  );
}

/** Id de práctica de `?p=`; sin parámetro o inválido, `PRACTICA_POR_DEFECTO`. */
export function idPractica(valor: string | null): number {
  const n = Number(valor);
  return Number.isInteger(n) && n > 0 ? n : PRACTICA_POR_DEFECTO;
}

/** Parámetros de un enlace a una práctica (siempre llevan `?p=`; `estado` es el de la demostración). */
export const paramsPractica = (id: number, extra: Params = {}): Params => ({ p: id, ...extra });

/** `?p=` actual como señal; llamar en un contexto de inyección. */
export function practicaActual(): Signal<number> {
  const ruta = inject(ActivatedRoute);
  return toSignal(ruta.queryParamMap.pipe(map((q) => idPractica(q.get('p')))), { initialValue: idPractica(ruta.snapshot.queryParamMap.get('p')) });
}

/** Estado de una carga que depende de `?p=`; llamar en un contexto de inyección. */
export function estadoPorPractica<T>(pedir: (id: number) => Observable<T>): Signal<EstadoUi<T>> {
  return toSignal(
    inject(ActivatedRoute).queryParamMap.pipe(
      map((q) => idPractica(q.get('p'))),
      distinctUntilChanged(),
      switchMap((id) => aEstado(pedir(id))),
    ),
    { initialValue: cargando<T>() },
  );
}

const ESTADOS: readonly EstadoPractica[] = ['asignada', 'en_curso', 'en_revision_final', 'suspendida', 'cancelada', 'cerrada'];

export const esEstado = (valor: string | null): boolean => ESTADOS.some((e) => e === valor);

/** Estado de la demostración de `?estado=`; si no es válido, el de la práctica. */
export function estadoDemo(valor: string | null, real: EstadoPractica): EstadoPractica {
  return ESTADOS.find((e) => e === valor) ?? real;
}

/** `MENDIETA SARANGO LUCIANA` → `Mendieta Sarango Luciana`. */
export const nombrePropio = (nombre: string): string => nombre.toLowerCase().replace(/(^|\s)(\S)/g, (_, espacio: string, letra: string) => espacio + letra.toUpperCase());

export const textoTipo = (p: Pick<Practica, 'tipo'>): string => (p.tipo === 'laboral' ? 'Laboral' : 'Comunitaria');

const SUBTIPOS: Record<Subtipo, string> = { '': '', ayudantia_docencia: 'Ayudantía de docencia', ayudantia_investigacion: 'Ayudantía de investigación', pasantia: 'Pasantía' };

/** `Laboral · Pasantía` o `Comunitaria`. */
export const componente = (p: Pick<Practica, 'tipo' | 'subtipo'>): string => [textoTipo(p), SUBTIPOS[p.subtipo]].filter(Boolean).join(' · ');

/** Color del estado; el texto y el ícono van siempre con él. */
export function tipoEstado(p: Pick<Practica, 'estado' | 'resultado'>, estado: EstadoPractica = p.estado): TipoInsignia {
  switch (estado) {
    case 'cerrada':
      return p.resultado === 'no_aprobada' ? 'bad' : 'ok';
    case 'cancelada':
      return 'bad';
    case 'en_revision_final':
    case 'suspendida':
      return 'warn';
    default:
      return 'info';
  }
}

/** Texto del estado, con el resultado si está cerrada: «Cerrada (aprobada)». */
export const textoEstado = (p: Practica, estado: EstadoPractica = p.estado): string => etiquetaEstadoPractica({ ...p, estado });

const TIPO_ALERTA: Record<TipoAlerta, TipoInsignia> = { reporte_no_enviado: 'bad', revision_pendiente: 'warn', rezago: 'bad', incumplimiento: 'bad' };
export const tipoAlerta = (t: TipoAlerta): TipoInsignia => TIPO_ALERTA[t];
export const textoAlerta = (t: TipoAlerta): string => TIPOS_ALERTA[t];

export const CLAVES_ALERTA: readonly TipoAlerta[] = ['reporte_no_enviado', 'revision_pendiente', 'rezago', 'incumplimiento'];

/** Campos numéricos editables de la configuración (C7). */
export type CampoConfiguracion = 'horasLaboral' | 'horasComunitaria' | 'horasLaboralDistancia' | 'horasComunitariaDistancia' | 'plazoReporteDias' | 'plazoRevisionDias' | 'umbralRezago';

const MENOR_A_DISTANCIA = 'Las horas a distancia no pueden ser menores que las presenciales.';

/** Errores de la configuración por campo; vacío si todo es válido (RF-12). */
export function validarConfiguracion(c: Record<CampoConfiguracion, number | null>): Partial<Record<CampoConfiguracion, string>> {
  const errores: Partial<Record<CampoConfiguracion, string>> = {};
  const menorA1 = (v: number | null): boolean => v === null || !Number.isFinite(v) || v < 1;
  for (const campo of ['horasLaboral', 'horasComunitaria', 'horasLaboralDistancia', 'horasComunitariaDistancia'] as const) {
    if (menorA1(c[campo])) errores[campo] = 'Ingrese al menos 1 hora.';
  }
  if (menorA1(c.plazoRevisionDias)) errores.plazoRevisionDias = 'El plazo de revisión debe ser de al menos 1 día hábil.';
  if (c.plazoReporteDias === null || !Number.isFinite(c.plazoReporteDias) || c.plazoReporteDias < 0) errores.plazoReporteDias = 'Ingrese el plazo de reporte en días.';
  if (menorA1(c.umbralRezago) || (c.umbralRezago ?? 0) > 100) errores.umbralRezago = 'El umbral debe estar entre 1 y 100 %.';
  if (!errores.horasLaboral && !errores.horasLaboralDistancia && (c.horasLaboralDistancia ?? 0) < (c.horasLaboral ?? 0)) errores.horasLaboralDistancia = MENOR_A_DISTANCIA;
  if (!errores.horasComunitaria && !errores.horasComunitariaDistancia && (c.horasComunitariaDistancia ?? 0) < (c.horasComunitaria ?? 0)) errores.horasComunitariaDistancia = MENOR_A_DISTANCIA;
  return errores;
}

export const camposDe = (c: ConfiguracionCarrera): Record<CampoConfiguracion, number> => ({
  horasLaboral: c.horasLaboral,
  horasComunitaria: c.horasComunitaria,
  horasLaboralDistancia: c.horasLaboralDistancia,
  horasComunitariaDistancia: c.horasComunitariaDistancia,
  plazoReporteDias: c.plazoReporteDias,
  plazoRevisionDias: c.plazoRevisionDias,
  umbralRezago: c.umbralRezago,
});
