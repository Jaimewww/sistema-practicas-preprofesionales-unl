import { Routes } from '@angular/router';
import { Login } from './features/auth/login/login';
import { Inicio } from './features/inicio/inicio';
import { NuevoReporte } from './features/reportes/nuevo-reporte';

export const routes: Routes = [
  { path: '', component: Inicio, title: 'Prácticas UNL' },
  { path: 'login', component: Login, title: 'Iniciar sesión · Prácticas UNL' },
  { path: 'reportes/nuevo', component: NuevoReporte, title: 'Registrar horas · Prácticas UNL' },
  { path: '**', redirectTo: '' },
];
