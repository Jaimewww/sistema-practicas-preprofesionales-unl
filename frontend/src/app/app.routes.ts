import { dashboardGuard } from './core/auth/dashboard.guard';
import { Shell } from './layout/shell';
import { Routes } from '@angular/router';
import { Login } from './features/auth/login/login';
import { Inicio } from './features/inicio/inicio';
import { NuevoReporte } from './features/reportes/nuevo-reporte';

const dashboardRoutes: Routes = [
  { path: '', component: Inicio, title: 'Prácticas UNL' },
  {
    path: 'reportes/nuevo',
    data: { role: 'estudiante' },
    component: NuevoReporte,
    title: 'Registrar horas · Prácticas UNL',
  },
  {
    path: 'estudiante',
    loadChildren: () =>
      import('./features/estudiante/estudiante.routes').then((m) => m.RUTAS_ESTUDIANTE),
  },
  {
    path: 'tutor-academico',
    loadChildren: () =>
      import('./features/tutor-academico/tutor-academico.routes').then(
        (m) => m.RUTAS_TUTOR_ACADEMICO,
      ),
  },
  {
    path: 'tutor-entidad',
    loadChildren: () =>
      import('./features/tutor-entidad/tutor-entidad.routes').then((m) => m.RUTAS_TUTOR_ENTIDAD),
  },
  {
    path: 'coordinador',
    loadChildren: () =>
      import('./features/coordinador/coordinador.routes').then((m) => m.RUTAS_COORDINADOR),
  },
  {
    path: 'director',
    loadChildren: () => import('./features/director/director.routes').then((m) => m.RUTAS_DIRECTOR),
  },
  {
    path: 'secretaria',
    loadChildren: () =>
      import('./features/secretaria/secretaria.routes').then((m) => m.RUTAS_SECRETARIA),
  },
  {
    path: 'analista',
    loadChildren: () => import('./features/analista/analista.routes').then((m) => m.RUTAS_ANALISTA),
  },
  {
    path: 'entidad-receptora',
    loadChildren: () =>
      import('./features/entidad-receptora/entidad-receptora.routes').then(
        (m) => m.RUTAS_ENTIDAD_RECEPTORA,
      ),
  },
  { path: '**', redirectTo: '' },
];

/** `/login` fuera del tablero; el resto cuelga del `Shell` y pasa por el guard de rol. */
export const routes: Routes = [
  { path: 'login', component: Login, title: 'Iniciar sesión · Prácticas UNL' },
  { path: '', component: Shell, canActivateChild: [dashboardGuard], children: dashboardRoutes },
];
