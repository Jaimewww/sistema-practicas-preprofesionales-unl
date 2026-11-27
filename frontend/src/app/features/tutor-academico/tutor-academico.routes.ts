import { Routes } from '@angular/router';
import { EvaluacionFinal } from './evaluacion-final';
import { Pendientes } from './pendientes';
import { PracticaTutorado } from './practica';
import { RevisarInforme } from './revisar-informe';
import { RevisarPlan } from './revisar-plan';
import { RevisarReporte } from './revisar-reporte';
import { TableroTutorAcademico } from './tablero-tutor-academico';
import { TutorAcademicoApi } from './tutor-academico.api';
import { TutorAcademicoMock } from './tutor-academico.mock';
import { Tutorados } from './tutorados';

const INICIO = { texto: 'Inicio', enlace: '/tutor-academico' };
const PENDIENTES = { texto: 'Pendientes de revisión', enlace: '/tutor-academico/pendientes' };
const TUTORADOS = { texto: 'Mis tutorados', enlace: '/tutor-academico/tutorados' };
const PRACTICA = { texto: 'Práctica del tutorado', enlace: '/tutor-academico/practica' };

/**
 * Rutas de «Tutor académico» (prefijo `/tutor-academico`). Las pantallas del rol van en `children` con su
 * `data: { titulo, migas }`; `TutorAcademicoApi` → `TutorAcademicoMock` va en `providers` del padre.
 * Los parámetros de consulta eligen la variante: `r` (revisión) y `p` (práctica, evaluación).
 */
export const RUTAS_TUTOR_ACADEMICO: Routes = [
  {
    path: '',
    providers: [{ provide: TutorAcademicoApi, useClass: TutorAcademicoMock }],
    children: [
      {
        path: '',
        component: TableroTutorAcademico,
        title: 'Tablero · Prácticas UNL',
        data: { titulo: 'Tablero', migas: [{ texto: 'Inicio' }], foto: true },
      },
      {
        path: 'pendientes',
        component: Pendientes,
        title: 'Pendientes de revisión · Prácticas UNL',
        data: { titulo: 'Pendientes de revisión', migas: [INICIO, { texto: 'Prácticas' }, { texto: 'Pendientes de revisión' }] },
      },
      {
        path: 'revisar/reporte',
        component: RevisarReporte,
        title: 'Revisar reporte semanal · Prácticas UNL',
        data: { titulo: 'Revisar reporte semanal', migas: [INICIO, PENDIENTES, { texto: 'Reporte semanal' }] },
      },
      {
        path: 'revisar/plan',
        component: RevisarPlan,
        title: 'Revisar plan de actividades · Prácticas UNL',
        data: { titulo: 'Revisar plan de actividades', migas: [INICIO, PENDIENTES, { texto: 'Plan de actividades' }] },
      },
      {
        path: 'revisar/informe',
        component: RevisarInforme,
        title: 'Revisar informe final · Prácticas UNL',
        data: { titulo: 'Revisar informe final', migas: [INICIO, PENDIENTES, { texto: 'Informe final' }] },
      },
      {
        path: 'tutorados',
        component: Tutorados,
        title: 'Mis tutorados · Prácticas UNL',
        data: { titulo: 'Mis tutorados', migas: [INICIO, { texto: 'Prácticas' }, { texto: 'Mis tutorados' }] },
      },
      {
        path: 'practica',
        component: PracticaTutorado,
        title: 'Práctica del tutorado · Prácticas UNL',
        data: { titulo: 'Práctica del tutorado', migas: [INICIO, TUTORADOS, { texto: 'Práctica del tutorado' }] },
      },
      {
        path: 'evaluacion',
        component: EvaluacionFinal,
        title: 'Evaluación final · Prácticas UNL',
        data: { titulo: 'Evaluación final', migas: [INICIO, TUTORADOS, PRACTICA, { texto: 'Evaluación final' }] },
      },
    ],
  },
];
