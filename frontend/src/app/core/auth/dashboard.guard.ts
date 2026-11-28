import { InjectionToken, inject } from '@angular/core';
import { Router, type CanActivateChildFn } from '@angular/router';
import { environment } from '../../../environments/environment';
import { accountMenu, rutaTablero } from '../../layout/menu-roles';
import { SesionService } from './sesion.service';

export const DEMO_MODE = new InjectionToken<boolean>('Demo mode', {
  factory: () => environment.useMock,
});

/** Client-side navigation only. The API still enforces all permissions. */
export const dashboardGuard: CanActivateChildFn = (route) => {
  if (inject(DEMO_MODE)) return true;

  const router = inject(Router);
  const session = inject(SesionService);
  const profile = session.perfil();
  const menu = profile && session.autenticado() ? accountMenu(profile.rol) : undefined;
  if (!menu) return router.createUrlTree(['/login']);

  const section = route.pathFromRoot[2];
  if (section?.data['role'] === menu.clave || section?.url[0]?.path === menu.prefijo) return true;
  return router.createUrlTree([rutaTablero(menu)]);
};
