import type { ApiError } from './api/envelope';

/**
 * Estado de una operación en la interfaz. Contrato entre Melissa (componente)
 * e Ivett (estados y errores): el componente solo pinta según `tipo`.
 */
export type EstadoUi<T> =
  | { tipo: 'inicial' }
  | { tipo: 'cargando' }
  | { tipo: 'exito'; datos: T }
  | { tipo: 'vacio' }
  | { tipo: 'error'; error: ApiError; mensaje: string };

export const inicial = <T>(): EstadoUi<T> => ({ tipo: 'inicial' });
export const cargando = <T>(): EstadoUi<T> => ({ tipo: 'cargando' });
export const exito = <T>(datos: T): EstadoUi<T> => ({ tipo: 'exito', datos });
export const vacio = <T>(): EstadoUi<T> => ({ tipo: 'vacio' });
