import type { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';
import type { ErroresDeCampo } from './api/envelope';

/**
 * Validadores del formulario de reportes
 *
 * Devuelven errores con la misma forma que `ApiError.campos`
 * (`{campo: [mensajes]}`), para pintarlos igual que los del servidor.
 * No sustituyen la validación del backend.
 */

const vacio = (v: unknown): boolean => v === null || v === undefined || v === '';

function error(campo: string, mensaje: string): ValidationErrors {
  return { [campo]: [mensaje] };
}

/** Semana: entero ≥ 1. */
export function validarSemana(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const v = control.value;
    if (vacio(v)) return error('semana', 'Indica el número de semana.');
    const n = Number(v);
    if (!Number.isInteger(n)) return error('semana', 'La semana debe ser un número entero.');
    if (n < 1) return error('semana', 'La semana debe ser 1 o mayor.');
    return null;
  };
}

/** Horas: entero entre 1 y 168 (y ≤ `maximo` si es ayudantía). */
export function validarHoras(maximo: () => number | null = () => null): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const v = control.value;
    if (vacio(v)) return error('horas_reportadas', 'Indica las horas de la semana.');
    const n = Number(v);
    if (!Number.isInteger(n)) return error('horas_reportadas', 'Las horas deben ser un número entero.');
    if (n < 1) return error('horas_reportadas', 'Debes reportar al menos 1 hora.');
    if (n > 168) {
      return error('horas_reportadas', 'Una semana tiene 168 horas: no se pueden reportar más.');
    }
    const tope = maximo();
    if (tope !== null && n > tope) {
      return error('horas_reportadas', `Una ayudantía admite como máximo ${tope} horas por semana.`);
    }
    return null;
  };
}

/** Mensajes de un control, con el mismo formato que `ApiError.campos`. */
export function mensajesDeControl(control: AbstractControl): string[] {
  // Angular también agrega sus propios errores (`min`, `max`, `required`) por los atributos
  // del <input>; aquí solo interesan los nuestros, que son listas de mensajes.
  const errores = (control.errors ?? {}) as ErroresDeCampo;
  return Object.values(errores).filter(Array.isArray).flat();
}
