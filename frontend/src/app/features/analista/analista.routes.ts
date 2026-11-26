import { Routes } from '@angular/router';
import { TableroAnalista } from './tablero-analista';

/**
 * Rutas de «Analista de prácticas» (prefijo `/analista`). Las pantallas del rol van en `children` con su
 * `data: { titulo, migas }`; los servicios del rol (`*Api` → `*Mock`) van en `providers` del padre.
 */
export const RUTAS_ANALISTA: Routes = [
  {
    path: '',
    providers: [], // aquí: { provide: XApi, useClass: XMock }
    children: [
      {
        path: '',
        component: TableroAnalista,
        title: 'Tablero · Prácticas UNL',
        data: { titulo: 'Tablero', migas: [{ texto: 'Inicio' }], foto: true },
      },
    ],
  },
];
