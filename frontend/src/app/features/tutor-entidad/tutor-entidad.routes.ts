import { Routes } from '@angular/router';
import { ConfirmarReporte } from './confirmar-reporte';
import { InformeExterno } from './informe-externo';
import { MisPracticantes } from './mis-practicantes';
import { ReportarIncumplimiento } from './reportar-incumplimiento';
import { ReportesPorConfirmar } from './reportes-por-confirmar';
import { TableroTutorEntidad } from './tablero-tutor-entidad';
import { TutorEntidadApi } from './tutor-entidad.api';
import { TutorEntidadMock } from './tutor-entidad.mock';

const INICIO = { texto: 'Inicio', enlace: '/tutor-entidad' };
const PRACTICAS = { texto: 'Prácticas' };
const PRACTICANTES = { texto: 'Mis practicantes', enlace: '/tutor-entidad/practicantes' };
const POR_CONFIRMAR = { texto: 'Reportes por confirmar', enlace: '/tutor-entidad/reportes-por-confirmar' };

/**
 * Rutas de «Tutor de la entidad» (prefijo `/tutor-entidad`). Las pantallas del rol van en `children` con su
 * `data: { titulo, migas }`; `TutorEntidadApi` → `TutorEntidadMock` va en `providers` del padre (rol solo con datos simulados).
 */
export const RUTAS_TUTOR_ENTIDAD: Routes = [
  {
    path: '',
    providers: [{ provide: TutorEntidadApi, useClass: TutorEntidadMock }],
    children: [
      {
        path: '',
        component: TableroTutorEntidad,
        title: 'Tablero · Prácticas UNL',
        data: { titulo: 'Tablero', migas: [{ texto: 'Inicio' }], foto: true },
      },
      {
        path: 'practicantes',
        component: MisPracticantes,
        title: 'Mis practicantes · Prácticas UNL',
        data: { titulo: 'Mis practicantes', migas: [INICIO, PRACTICAS, { texto: 'Mis practicantes' }] },
      },
      {
        path: 'reportes-por-confirmar',
        component: ReportesPorConfirmar,
        title: 'Reportes por confirmar · Prácticas UNL',
        data: { titulo: 'Reportes por confirmar', migas: [INICIO, PRACTICAS, { texto: 'Reportes por confirmar' }] },
      },
      {
        path: 'confirmar-reporte',
        component: ConfirmarReporte,
        title: 'Confirmar reporte · Prácticas UNL',
        data: { titulo: 'Confirmar reporte', migas: [INICIO, PRACTICAS, POR_CONFIRMAR, { texto: 'Confirmar reporte' }] },
      },
      {
        path: 'informe-externo',
        component: InformeExterno,
        title: 'Informe externo · Prácticas UNL',
        data: { titulo: 'Informe externo', migas: [INICIO, PRACTICAS, PRACTICANTES, { texto: 'Informe externo' }] },
      },
      {
        path: 'incumplimiento',
        component: ReportarIncumplimiento,
        title: 'Reportar incumplimiento · Prácticas UNL',
        data: { titulo: 'Reportar incumplimiento', migas: [INICIO, PRACTICAS, PRACTICANTES, { texto: 'Reportar incumplimiento' }] },
      },
    ],
  },
];
