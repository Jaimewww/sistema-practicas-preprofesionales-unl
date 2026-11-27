import { catchError, map, Observable, of, startWith } from 'rxjs';
import { estadoDeError } from '../../core/errores';
import { cargando, exito, vacio, type EstadoUi } from '../../core/estado-ui';
import { ESTADO_PRACTICA, ESTADO_REPORTE, formatoFecha } from '../../core/demo';
import type { EstadoReporte, Fecha, Practica, Subtipo } from '../../core/demo';
import type { TipoInsignia } from '../../shared/ui';

/** Tamaño máximo del informe externo (RNF-05). */
export const MAXIMO_MB = 5;
export const MAXIMO_BYTES = MAXIMO_MB * 1024 * 1024;

/** Convierte un flujo de la API en el flujo de `EstadoUi` que pintan las pantallas. */
export function aEstado<T>(origen: Observable<T>, esVacio: (datos: T) => boolean = () => false): Observable<EstadoUi<T>> {
  return origen.pipe(
    map((datos) => (esVacio(datos) ? vacio<T>() : exito(datos))),
    catchError((e: unknown) => of(estadoDeError<T>(e))),
    startWith(cargando<T>()),
  );
}

/** `MENDIETA SARANGO LUCIANA BELÉN` → `Luciana Mendieta` (primer nombre y primer apellido). */
export function nombreCorto(completo: string): string {
  const [apellido = '', , nombre = ''] = completo.split(' ');
  const propio = (t: string) => t.charAt(0) + t.slice(1).toLowerCase();
  return `${propio(nombre)} ${propio(apellido)}`.trim();
}

const SUBTIPO: Record<Subtipo, string> = {
  '': '',
  ayudantia_docencia: 'ayudantía de docencia',
  ayudantia_investigacion: 'ayudantía de investigación',
  pasantia: 'pasantía',
};
/** `ayudantía de docencia` (en minúscula, para frases). */
export const subtipoTexto = (p: Practica): string => SUBTIPO[p.subtipo];
/** `Ayudantía de docencia`. */
export const subtipoTitulo = (p: Practica): string => {
  const t = subtipoTexto(p);
  return t.charAt(0).toUpperCase() + t.slice(1);
};
/** `Laboral: Ayudantía de docencia`. */
export const textoPracticaLarga = (p: Practica): string => `Laboral: ${subtipoTitulo(p)}`;
export const textoEstadoPractica = (p: Practica): string => ESTADO_PRACTICA[p.estado];

export function tipoEstadoPractica(p: Practica): TipoInsignia {
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

export function tipoRevision(estado: EstadoReporte): TipoInsignia {
  return ({ validado: 'ok', en_revision: 'warn', devuelto: 'bad', sin_reporte: 'warn' } as const)[estado];
}
export const textoRevision = (estado: EstadoReporte): string => ESTADO_REPORTE[estado];

/** `18/05/2026 - 24/05/2026`, como en el prototipo. */
export const rango = (r: { desde: Fecha; hasta: Fecha }): string => `${formatoFecha(r.desde)} - ${formatoFecha(r.hasta)}`;

/** `1,2 MB` → texto con coma decimal; redondea hacia arriba a un decimal. */
export const megas = (bytes: number): string => (Math.ceil((bytes / 1048576) * 10) / 10).toString().replace('.', ',');

/** Mensaje de error del archivo del informe externo, o `null` si es un PDF válido. */
export function errorDeArchivo(a: { nombre: string; bytes: number } | null): string | null {
  if (!a) return 'Adjunte el informe firmado en PDF.';
  if (!/\.pdf$/i.test(a.nombre)) return `«${a.nombre}»: solo se admiten archivos PDF.`;
  if (a.bytes > MAXIMO_BYTES) return `«${a.nombre}» pesa ${megas(a.bytes)} MB y supera el máximo de ${MAXIMO_MB} MB por archivo.`;
  return null;
}

/** Id de práctica de `?p=`, o `null` si falta o no es un entero positivo. */
export function idDeParametro(valor: string | null): number | null {
  const n = Number(valor);
  return valor && Number.isInteger(n) && n > 0 ? n : null;
}
