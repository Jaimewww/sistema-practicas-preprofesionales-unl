/**
 * Configuración del cliente. Se lee de variables PUBLIC_* (ver .env.example).
 *
 * PUBLIC_USE_MOCK=true hace que todos los servicios usen datos simulados:
 * así cada integrante trabaja su parte sin backend ni login.
 */
export const API_BASE_URL: string =
  import.meta.env.PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1';

export const USE_MOCK: boolean = (import.meta.env.PUBLIC_USE_MOCK ?? 'true') === 'true';
