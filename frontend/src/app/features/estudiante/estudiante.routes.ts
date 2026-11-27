import type { Provider, Type } from '@angular/core';
import { Routes } from '@angular/router';
import { environment } from '../../../environments/environment';
import { NuevoReporte } from '../reportes/nuevo-reporte';
import { EstudianteApi } from './estudiante.api';
import { EstudianteMock } from './estudiante.mock';
import { InformeFinal } from './informe-final';
import { MisPracticas } from './mis-practicas';
import { PlanActividades } from './plan-actividades';
import { PlanActividadesReal } from './plan-actividades-real';
import { PlanInformeHttp } from './plan-informe.http';
import { PracticaLayout } from './practica-layout';
import { PracticaPlan } from './practica-plan';
import { PracticaPlanReal } from './practica-plan-real';
import { PracticaReportes } from './practica-reportes';
import { PracticaResumen } from './practica-resumen';
import { ReporteSemana } from './reporte-semanal';
import { TableroEstudiante } from './tablero-estudiante';

const INICIO = { texto: 'Inicio', enlace: '/estudiante' };
const PRACTICAS = { texto: 'Mis prácticas', enlace: '/estudiante/mis-practicas' };
const MI_PRACTICA = { texto: 'Mi práctica', enlace: '/estudiante/practica' };

/** `npm start` (demo) conserva la pantalla del prototipo; `start:real` usa la que habla con el API. */
const pantalla = (useMock: boolean, demo: Type<unknown>, real: Type<unknown>): Type<unknown> =>
  useMock ? demo : real;

/**
 * Rutas de «Estudiante» (prefijo `/estudiante`). Las pantallas del rol van en `children` con su
 * `data: { titulo, migas }`; `EstudianteApi` → `EstudianteMock` sigue en `providers` del padre
 * porque las pantallas del prototipo que todavía no tienen variante real lo inyectan.
 *
 * Plan de actividades y la pestaña Plan ya tienen variante real (C-09): cada entrada conserva
 * su `path`, título y migas y elige el componente con `environment.useMock`. En modo real cada
 * una provee `PlanInformeHttp`, el adaptador que habla con el API; en modo simulado no se provee
 * nada y la pantalla es la de siempre. Ninguna otra entrada cambia.
 */
export function rutasEstudiante(useMock: boolean): Routes {
  const planInforme: Provider[] = useMock ? [] : [PlanInformeHttp];
  return [
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
          data: {
            titulo: 'Mis prácticas',
            migas: [INICIO, { texto: 'Prácticas' }, { texto: 'Mis prácticas' }],
          },
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
              component: pantalla(useMock, PracticaPlan, PracticaPlanReal),
              providers: planInforme,
              title: 'Plan de la práctica · Prácticas UNL',
              data: {
                titulo: 'Plan de actividades',
                migas: [INICIO, PRACTICAS, MI_PRACTICA, { texto: 'Plan' }],
              },
            },
            {
              path: 'reportes',
              component: PracticaReportes,
              title: 'Reportes semanales · Prácticas UNL',
              data: {
                titulo: 'Reportes semanales',
                migas: [INICIO, PRACTICAS, MI_PRACTICA, { texto: 'Reportes semanales' }],
              },
            },
          ],
        },
        {
          path: 'plan',
          component: pantalla(useMock, PlanActividades, PlanActividadesReal),
          providers: planInforme,
          title: 'Plan de actividades · Prácticas UNL',
          data: {
            titulo: 'Plan de actividades',
            migas: [INICIO, PRACTICAS, MI_PRACTICA, { texto: 'Plan de actividades' }],
          },
        },
        // E4 reutiliza el componente existente (también sigue en /reportes/nuevo).
        {
          path: 'reportes/nuevo',
          component: NuevoReporte,
          title: 'Registrar horas · Prácticas UNL',
          data: {
            titulo: 'Registrar horas',
            migas: [
              { texto: 'Inicio', enlace: '/estudiante' },
              { texto: 'Prácticas' },
              { texto: 'Registrar horas' },
            ],
          },
        },
        {
          path: 'reporte',
          component: ReporteSemana,
          title: 'Reporte semanal · Prácticas UNL',
          data: {
            titulo: 'Reporte semanal',
            migas: [INICIO, PRACTICAS, MI_PRACTICA, { texto: 'Reporte semanal' }],
          },
        },
        {
          path: 'informe-final',
          component: InformeFinal,
          title: 'Informe final · Prácticas UNL',
          data: {
            titulo: 'Informe final',
            migas: [INICIO, PRACTICAS, MI_PRACTICA, { texto: 'Informe final' }],
          },
        },
      ],
    },
  ];
}

/** Configuración activa: la que consume `app.routes.ts` con el lazy loading de `/estudiante`. */
export const RUTAS_ESTUDIANTE: Routes = rutasEstudiante(environment.useMock);
