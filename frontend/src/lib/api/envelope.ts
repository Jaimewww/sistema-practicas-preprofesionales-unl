/**
 * Contrato universal de respuesta del API (ADR 0012, docs/api.md §2).
 *
 * Toda respuesta con cuerpo de /api/v1/ llega envuelta así:
 *   {"success": true, "message": "", "data": {}, "errors": null, "meta": {}}
 * Las respuestas 204 llegan sin cuerpo.
 */

/** Errores que no son de validación: `{detail, code}`. */
export interface ErrorDeDominio {
  detail: string;
  code: string;
}

/** Errores de validación (400): `{campo: [mensajes]}`. */
export type ErroresDeCampo = Record<string, string[]>;

export interface Envelope<T> {
  success: boolean;
  message: string;
  data: T;
  errors: ErrorDeDominio | ErroresDeCampo | null;
  meta: Record<string, unknown>;
}

/** Error normalizado que lanza `http.ts` ante cualquier respuesta no 2xx. */
export class ApiError extends Error {
  constructor(
    /** Código HTTP; 0 si no hubo respuesta (red caída, CORS bloqueado). */
    readonly status: number,
    /** `errors.code` del envelope, o `validacion` / `sin_conexion`. */
    readonly code: string,
    readonly detail: string,
    /** Solo en 400: mensajes por campo, tal cual los manda el serializer. */
    readonly campos: ErroresDeCampo = {},
  ) {
    super(detail);
    this.name = 'ApiError';
  }
}

export function esErrorDeDominio(errors: Envelope<unknown>['errors']): errors is ErrorDeDominio {
  return (
    errors !== null &&
    typeof (errors as ErrorDeDominio).code === 'string' &&
    typeof (errors as ErrorDeDominio).detail === 'string'
  );
}
