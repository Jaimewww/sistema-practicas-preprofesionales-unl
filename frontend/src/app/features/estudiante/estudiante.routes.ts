import { Routes } from '@angular/router';
import { NuevoReporte } from '../reportes/nuevo-reporte';
import { TableroEstudiante } from './tablero-estudiante';

/**
 * Rutas de «Estudiante» (prefijo `/estudiante`). Las pantallas del rol van en `children` con su
 * `data: { titulo, migas }`; los servicios del rol (`*Api` → `*Mock`) van en `providers` del padre.
 */
export const RUTAS_ESTUDIANTE: Routes = [
  {
    path: '',
    providers: [], // aquí: { provide: XApi, useClass: XMock }
    children: [
      {
        path: '',
        component: TableroEstudiante,
        title: 'Tablero · Prácticas UNL',
        data: { titulo: 'Tablero', migas: [{ texto: 'Inicio' }], foto: true },
      },
      // E4 reutiliza el componente existente (también sigue en /reportes/nuevo).
      { path: 'reportes/nuevo', component: NuevoReporte, title: 'Registrar horas · Prácticas UNL', data: { titulo: 'Registrar horas', migas: [{ texto: 'Inicio', enlace: '/estudiante' }, { texto: 'Prácticas' }, { texto: 'Registrar horas' }] } },
    ],
  },
];
