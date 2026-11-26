import { Routes } from '@angular/router';
import { TableroTutorAcademico } from './tablero-tutor-academico';

/**
 * Rutas de «Tutor académico» (prefijo `/tutor-academico`). Las pantallas del rol van en `children` con su
 * `data: { titulo, migas }`; los servicios del rol (`*Api` → `*Mock`) van en `providers` del padre.
 */
export const RUTAS_TUTOR_ACADEMICO: Routes = [
  {
    path: '',
    providers: [], // aquí: { provide: XApi, useClass: XMock }
    children: [
      {
        path: '',
        component: TableroTutorAcademico,
        title: 'Tablero · Prácticas UNL',
        data: { titulo: 'Tablero', migas: [{ texto: 'Inicio' }], foto: true },
      },
    ],
  },
];
