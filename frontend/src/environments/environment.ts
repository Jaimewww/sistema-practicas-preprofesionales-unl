/**
 * Configuración por defecto (`npm start`): datos simulados.
 *
 * useMock=true hace que todos los servicios usen el mock: así cada integrante
 * trabaja su parte sin backend ni login. `npm run start:real` reemplaza este
 * archivo por environment.real.ts (ver angular.json, fileReplacements).
 */
export const environment = {
  apiBaseUrl: 'http://localhost:8000/api/v1',
  useMock: true,
};
