import { Routes } from '@angular/router';
import { Login } from './features/auth/login/login';
import { Inicio } from './features/inicio/inicio';
import { NuevoReporte } from './features/reportes/nuevo-reporte';

export const routes: Routes = [
  { path: '', component: Inicio, title: 'Prácticas UNL' },
  { path: 'login', component: Login, title: 'Iniciar sesión · Prácticas UNL' },
  { path: 'reportes/nuevo', component: NuevoReporte, title: 'Registrar horas · Prácticas UNL' },
  { path: 'estudiante', loadChildren: () => import('./features/estudiante/estudiante.routes').then((m) => m.RUTAS_ESTUDIANTE) },
  { path: 'tutor-academico', loadChildren: () => import('./features/tutor-academico/tutor-academico.routes').then((m) => m.RUTAS_TUTOR_ACADEMICO) },
  { path: 'tutor-entidad', loadChildren: () => import('./features/tutor-entidad/tutor-entidad.routes').then((m) => m.RUTAS_TUTOR_ENTIDAD) },
  { path: 'coordinador', loadChildren: () => import('./features/coordinador/coordinador.routes').then((m) => m.RUTAS_COORDINADOR) },
  { path: 'director', loadChildren: () => import('./features/director/director.routes').then((m) => m.RUTAS_DIRECTOR) },
  { path: 'secretaria', loadChildren: () => import('./features/secretaria/secretaria.routes').then((m) => m.RUTAS_SECRETARIA) },
  { path: 'analista', loadChildren: () => import('./features/analista/analista.routes').then((m) => m.RUTAS_ANALISTA) },
  { path: 'entidad-receptora', loadChildren: () => import('./features/entidad-receptora/entidad-receptora.routes').then((m) => m.RUTAS_ENTIDAD_RECEPTORA) },
  { path: '**', redirectTo: '' },
];
