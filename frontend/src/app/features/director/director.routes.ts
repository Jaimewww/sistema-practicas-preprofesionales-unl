import { Routes } from '@angular/router';
import { CierreHistorial } from './cierre-historial';
import { CierreLayout } from './cierre-layout';
import { CierreResumen } from './cierre-resumen';
import { Cierres } from './cierres';
import { DirectorApi } from './director.api';
import { DirectorMock } from './director.mock';
import { TableroDirector } from './tablero-director';

const INICIO = { texto: 'Inicio', enlace: '/director' };
const CIERRES = { texto: 'Cierres de mi carrera', enlace: '/director/cierres' };

/**
 * Rutas de «Director de carrera» (prefijo `/director`). Las pantallas del rol van en `children` con su
 * `data: { titulo, migas }`; `DirectorApi` → `DirectorMock` va en `providers` del padre.
 */
export const RUTAS_DIRECTOR: Routes = [
  {
    path: '',
    providers: [{ provide: DirectorApi, useClass: DirectorMock }],
    children: [
      {
        path: '',
        component: TableroDirector,
        title: 'Tablero · Prácticas UNL',
        data: { titulo: 'Tablero', migas: [{ texto: 'Inicio' }], foto: true },
      },
      {
        path: 'cierres',
        component: Cierres,
        title: 'Cierres de mi carrera · Prácticas UNL',
        data: { titulo: 'Cierres de mi carrera', migas: [INICIO, { texto: 'Cierres de mi carrera' }] },
      },
      // Datos del cierre y pestañas (Resumen / Historial) en el marco; `?p=` elige la práctica.
      {
        path: 'cierre',
        component: CierreLayout,
        children: [
          {
            path: '',
            component: CierreResumen,
            title: 'Detalle del cierre · Prácticas UNL',
            data: { titulo: 'Detalle del cierre', migas: [INICIO, CIERRES, { texto: 'Detalle del cierre' }] },
          },
          {
            path: 'historial',
            component: CierreHistorial,
            title: 'Historial del cierre · Prácticas UNL',
            data: { titulo: 'Historial del cierre', migas: [INICIO, CIERRES, { texto: 'Historial' }] },
          },
        ],
      },
    ],
  },
];
