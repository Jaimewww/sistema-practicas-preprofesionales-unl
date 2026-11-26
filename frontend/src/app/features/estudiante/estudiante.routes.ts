import { Routes } from '@angular/router';
import { NuevoReporte } from '../reportes/nuevo-reporte';
import { EstudianteApi } from './estudiante.api';
import { EstudianteMock } from './estudiante.mock';
import { InformeFinal } from './informe-final';
import { MisPracticas } from './mis-practicas';
import { PlanActividades } from './plan-actividades';
import { PracticaLayout } from './practica-layout';
import { PracticaPlan } from './practica-plan';
import { PracticaReportes } from './practica-reportes';
import { PracticaResumen } from './practica-resumen';
import { ReporteSemana } from './reporte-semanal';
import { TableroEstudiante } from './tablero-estudiante';

const INICIO = { texto: 'Inicio', enlace: '/estudiante' };
const PRACTICAS = { texto: 'Mis prácticas', enlace: '/estudiante/mis-practicas' };
const MI_PRACTICA = { texto: 'Mi práctica', enlace: '/estudiante/practica' };

/**
 * Rutas de «Estudiante» (prefijo `/estudiante`). Las pantallas del rol van en `children` con su
 * `data: { titulo, migas }`; el servicio del rol (`EstudianteApi` → `EstudianteMock`) va en `providers`
 * del padre: el backend aún no expone estas pantallas.
 */
export const RUTAS_ESTUDIANTE: Routes = [
  {
    path: '',
    providers: [{ provide: EstudianteApi, useClass: EstudianteMock }],
    children: [
      {
        path: '',
        component: TableroEstudiante,
        title: 'Tablero · Prácticas UNL',
        data: { titulo: 'Tablero', migas: [{ texto: 'Inicio' }], foto: true },
      },
      {
        path: 'mis-practicas',
        component: MisPracticas,
        title: 'Mis prácticas · Prácticas UNL',
        data: { titulo: 'Mis prácticas', migas: [INICIO, { texto: 'Prácticas' }, { texto: 'Mis prácticas' }] },
      },
      // Datos de la práctica y pestañas compartidos por resumen, plan y reportes.
      {
        path: 'practica',
        component: PracticaLayout,
        children: [
          {
            path: '',
            component: PracticaResumen,
            title: 'Mi práctica · Prácticas UNL',
            data: { titulo: 'Mi práctica', migas: [INICIO, PRACTICAS, { texto: 'Mi práctica' }] },
          },
          {
            path: 'plan',
            component: PracticaPlan,
            title: 'Plan de la práctica · Prácticas UNL',
            data: { titulo: 'Plan de actividades', migas: [INICIO, PRACTICAS, MI_PRACTICA, { texto: 'Plan' }] },
          },
          {
            path: 'reportes',
            component: PracticaReportes,
            title: 'Reportes semanales · Prácticas UNL',
            data: { titulo: 'Reportes semanales', migas: [INICIO, PRACTICAS, MI_PRACTICA, { texto: 'Reportes semanales' }] },
          },
        ],
      },
      {
        path: 'plan',
        component: PlanActividades,
        title: 'Plan de actividades · Prácticas UNL',
        data: { titulo: 'Plan de actividades', migas: [INICIO, PRACTICAS, MI_PRACTICA, { texto: 'Plan de actividades' }] },
      },
      // E4 reutiliza el componente existente (también sigue en /reportes/nuevo).
      { path: 'reportes/nuevo', component: NuevoReporte, title: 'Registrar horas · Prácticas UNL', data: { titulo: 'Registrar horas', migas: [{ texto: 'Inicio', enlace: '/estudiante' }, { texto: 'Prácticas' }, { texto: 'Registrar horas' }] } },
      {
        path: 'reporte',
        component: ReporteSemana,
        title: 'Reporte semanal · Prácticas UNL',
        data: { titulo: 'Reporte semanal', migas: [INICIO, PRACTICAS, MI_PRACTICA, { texto: 'Reporte semanal' }] },
      },
      {
        path: 'informe-final',
        component: InformeFinal,
        title: 'Informe final · Prácticas UNL',
        data: { titulo: 'Informe final', migas: [INICIO, PRACTICAS, MI_PRACTICA, { texto: 'Informe final' }] },
      },
    ],
  },
];
