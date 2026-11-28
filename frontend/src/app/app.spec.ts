import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter, Router } from '@angular/router';
import { DEMO_MODE } from './core/auth/dashboard.guard';
import { SesionService } from './core/auth/sesion.service';
import { routes } from './app.routes';
import { App } from './app';

describe('App', () => {
  it('renders login outside the dashboard shell', async () => {
    TestBed.configureTestingModule({
      imports: [App],
      providers: [provideRouter(routes), provideHttpClient()],
    });
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    await TestBed.inject(Router).navigateByUrl('/login');
    fixture.detectChanges();
    const view = fixture.nativeElement as HTMLElement;
    expect(view.querySelector('app-login .acceso')).not.toBeNull();
    expect(view.querySelector('app-shell')).toBeNull();
  });

  it('muestra la navegación al inicio, al login y al tablero del estudiante', async () => {
    TestBed.configureTestingModule({
      imports: [App],
      providers: [provideRouter(routes), provideHttpClient()],
    });
    const fixture = TestBed.createComponent(App);
    await TestBed.inject(Router).navigateByUrl('/');
    await fixture.whenStable();
    const vista = fixture.nativeElement as HTMLElement;
    (vista.querySelector('.usuario__boton') as HTMLButtonElement).click();
    fixture.detectChanges();
    const rutas = new Set(
      [...vista.querySelectorAll('a[href]')].map((a) => a.getAttribute('href')),
    );
    expect(rutas).toContain('/');
    expect(rutas).toContain('/login');
    expect(rutas).toContain('/estudiante');
    expect(vista.querySelector('router-outlet')).not.toBeNull();
  });

  it.each([
    [null, '/login'],
    [{ nombre: 'Ada Lovelace', rol: 'coordinador' }, '/coordinador'],
  ] as const)('checks real-mode dashboard access for %j', async (profile, destination) => {
    TestBed.configureTestingModule({
      imports: [App],
      providers: [
        provideRouter(routes),
        provideHttpClient(),
        { provide: DEMO_MODE, useValue: false },
        {
          provide: SesionService,
          useValue: { perfil: () => profile, autenticado: () => !!profile },
        },
      ],
    });
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const router = TestBed.inject(Router);
    await router.navigateByUrl('/estudiante/mis-practicas');
    fixture.detectChanges();
    const view = fixture.nativeElement as HTMLElement;
    expect(router.url).toBe(destination);
    if (profile) {
      expect(view.querySelector('.usuario__nombre')?.textContent).toContain(profile.nombre);
      expect(view.querySelector('.campana b')).toBeNull();
    } else {
      expect(view.querySelector('app-shell')).toBeNull();
    }
  });
});
