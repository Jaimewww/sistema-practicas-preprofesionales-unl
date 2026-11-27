import { Routes } from '@angular/router';
import { Alertas } from './alertas';
import { CerrarPractica } from './cerrar-practica';
import { Configuracion } from './configuracion';
import { Consolidado } from './consolidado';
import { CoordinadorApi } from './coordinador.api';
import { CoordinadorMock } from './coordinador.mock';
import { SuspenderCancelar } from './suspender-cancelar';
import { PracticaHistorial } from './practica-historial';
import { PracticaLayout } from './practica-layout';
import { PracticaResumen } from './practica-resumen';
import { PracticasCarrera } from './practicas-carrera';
import { TableroCoordinador } from './tablero-coordinador';

const INICIO = { texto: 'Inicio', enlace: '/coordinador' };
const PRACTICAS = { texto: 'Prácticas de la carrera', enlace: '/coordinador/practicas' };
const PRACTICA = { texto: 'Práctica', enlace: '/coordinador/practica' };

/**
 * Rutas de «Coordinador» (prefijo `/coordinador`). Las pantallas del rol van en `children` con su
 * `data: { titulo, migas }`; los servicios del rol (`*Api` → `*Mock`) van en `providers` del padre.
 */
export const RUTAS_COORDINADOR: Routes = [
  {
    path: '',
    providers: [{ provide: CoordinadorApi, useClass: CoordinadorMock }],
    children: [
      {
        path: '',
        component: TableroCoordinador,
        title: 'Tablero · Prácticas UNL',
        data: { titulo: 'Tablero', migas: [{ texto: 'Inicio' }], foto: true },
      },
      {
        path: 'practicas',
        component: PracticasCarrera,
        title: 'Prácticas de la carrera · Prácticas UNL',
        data: { titulo: 'Prácticas de la carrera', migas: [INICIO, { texto: 'Prácticas' }, { texto: 'Prácticas de la carrera' }] },
      },
      {
        path: 'alertas',
        component: Alertas,
        title: 'Alertas · Prácticas UNL',
        data: { titulo: 'Alertas', migas: [INICIO, { texto: 'Prácticas' }, { texto: 'Alertas' }] },
      },
      {
        path: 'practica',
        component: PracticaLayout,
        children: [
          {
            path: '',
            component: PracticaResumen,
            title: 'Práctica · Prácticas UNL',
            data: { titulo: 'Práctica', migas: [INICIO, PRACTICAS, { texto: 'Práctica' }] },
          },
          {
            path: 'historial',
            component: PracticaHistorial,
            title: 'Historial de la práctica · Prácticas UNL',
            data: { titulo: 'Historial de la práctica', migas: [INICIO, PRACTICAS, PRACTICA, { texto: 'Historial' }] },
          },
        ],
      },
      {
        path: 'cerrar',
        component: CerrarPractica,
        title: 'Cerrar práctica · Prácticas UNL',
        data: { titulo: 'Cerrar práctica', migas: [INICIO, PRACTICAS, PRACTICA, { texto: 'Cerrar' }] },
      },
      {
        path: 'suspender-cancelar',
        component: SuspenderCancelar,
        title: 'Suspender o cancelar práctica · Prácticas UNL',
        data: { titulo: 'Suspender o cancelar práctica', migas: [INICIO, PRACTICAS, PRACTICA, { texto: 'Suspender o cancelar' }] },
      },
      {
        path: 'consolidado',
        component: Consolidado,
        title: 'Consolidado · Prácticas UNL',
        data: { titulo: 'Consolidado de la carrera', migas: [INICIO, { texto: 'Prácticas' }, { texto: 'Consolidado' }] },
      },
      {
        path: 'configuracion',
        component: Configuracion,
        title: 'Configuración · Prácticas UNL',
        data: { titulo: 'Configuración de la carrera', migas: [INICIO, { texto: 'Prácticas' }, { texto: 'Configuración' }] },
      },
    ],
  },
];
