import { Routes } from '@angular/router';
import { TableroSecretaria } from './tablero-secretaria';

/**
 * Rutas de «Secretaría de carrera» (prefijo `/secretaria`). Las pantallas del rol van en `children` con su
 * `data: { titulo, migas }`; los servicios del rol (`*Api` → `*Mock`) van en `providers` del padre.
 */
export const RUTAS_SECRETARIA: Routes = [
  {
    path: '',
    providers: [], // aquí: { provide: XApi, useClass: XMock }
    children: [
      {
        path: '',
        component: TableroSecretaria,
        title: 'Tablero · Prácticas UNL',
        data: { titulo: 'Tablero', migas: [{ texto: 'Inicio' }], foto: true },
      },
    ],
  },
];
