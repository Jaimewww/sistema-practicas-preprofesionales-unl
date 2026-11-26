import { Routes } from '@angular/router';
import { TableroTutorEntidad } from './tablero-tutor-entidad';

/**
 * Rutas de «Tutor de la entidad» (prefijo `/tutor-entidad`). Las pantallas del rol van en `children` con su
 * `data: { titulo, migas }`; los servicios del rol (`*Api` → `*Mock`) van en `providers` del padre.
 */
export const RUTAS_TUTOR_ENTIDAD: Routes = [
  {
    path: '',
    providers: [], // aquí: { provide: XApi, useClass: XMock }
    children: [
      {
        path: '',
        component: TableroTutorEntidad,
        title: 'Tablero · Prácticas UNL',
        data: { titulo: 'Tablero', migas: [{ texto: 'Inicio' }], foto: true },
      },
    ],
  },
];
