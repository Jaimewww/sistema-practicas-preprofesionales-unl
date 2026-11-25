/**
 * Sesión JWT del frontend.            RESPONSABLE: Jaime (F-003)
 *
 * Endpoints: POST /auth/token/ -> data {access, refresh};
 *            POST /auth/token/refresh/ -> nuevo par (el refresh rota);
 *            POST /auth/logout/ con {refresh} y el access vigente.
 *
 * El esqueleto solo deja la firma que usa `http.ts`. Jaime implementa
 * `iniciarSesion`, `refrescar` y `cerrarSesion` y decide dónde guardar los tokens.
 */

let accessToken: string | null = null;

export function obtenerAccessToken(): string | null {
  return accessToken;
}

export function guardarTokens(access: string | null): void {
  accessToken = access;
}

export async function iniciarSesion(_usuario: string, _clave: string): Promise<void> {
  throw new Error('Pendiente (Jaime): POST /auth/token/ y guardar el par de tokens.');
}

export async function cerrarSesion(): Promise<void> {
  throw new Error('Pendiente (Jaime): POST /auth/logout/ y limpiar la sesión.');
}
