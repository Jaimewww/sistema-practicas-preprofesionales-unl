import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter, Router } from '@angular/router';
import { of } from 'rxjs';
import { routes } from '../app.routes';
import { App } from '../app';
import { DEMO_MODE } from '../core/auth/dashboard.guard';
import { SesionService } from '../core/auth/sesion.service';
import { ApiClient } from '../core/api/api-client';
import { Login } from '../features/auth/login/login';
import { accountMenu } from '../layout/menu-roles';

type Perfil = { nombre: string; rol: string } | null;
const EST: Perfil = { nombre: 'Luciana Mendieta', rol: 'estudiante' };
const COORD: Perfil = { nombre: 'Coordinador de Computación', rol: 'coordinador' };
const fake = (perfil: Perfil) => ({
  perfil: () => perfil,
  autenticado: () => !!perfil,
  iniciarSesion: () => of(undefined),
  cargarPerfil: () => of(perfil ?? undefined),
  limpiarSesion: () => undefined,
  refrescar: () => of(undefined),
  cerrarSesion: () => of(undefined),
});

async function app(perfil: Perfil, demo = false) {
  TestBed.resetTestingModule();
  TestBed.configureTestingModule({
    imports: [App],
    providers: [
      provideRouter(routes),
      provideHttpClient(),
      { provide: DEMO_MODE, useValue: demo },
      { provide: SesionService, useValue: fake(perfil) },
    ],
  });
  const fixture = TestBed.createComponent(App);
  fixture.detectChanges();
  return { fixture, router: TestBed.inject(Router) };
}

describe('S1/S2 guard real: deep links propias y cruce de roles', () => {
  it.each([
    '/estudiante',
    '/estudiante/mis-practicas',
    '/estudiante/plan',
    '/estudiante/practica',
    '/estudiante/practica/plan',
    '/estudiante/reportes/nuevo',
    '/reportes/nuevo',
  ])('estudiante conserva %s', async (url) => {
    const { router } = await app(EST);
    await router.navigateByUrl(url);
    expect(router.url).toBe(url);
  });

  it.each([['/coordinador'], ['/tutor-academico']])(
    'estudiante en %s -> /estudiante (sin bucle)',
    async (url) => {
      const { router } = await app(EST);
      await router.navigateByUrl(url);
      expect(router.url).toBe('/estudiante');
    },
  );

  it.each(['/estudiante/mis-practicas', '/reportes/nuevo', '/'])(
    'coordinador en %s -> /coordinador',
    async (url) => {
      const { router } = await app(COORD);
      await router.navigateByUrl(url);
      expect(router.url).toBe('/coordinador');
    },
  );

  it.each([
    'estudiante',
    'tutor_academico',
    'tutor_entidad',
    'coordinador',
    'director',
    'secretaria',
  ])('rol %s alcanza su tablero', async (rol) => {
    const menu = accountMenu(rol)!;
    expect(menu).toBeDefined();
    const { router } = await app({ nombre: 'Prueba', rol });
    await router.navigateByUrl(`/${menu.prefijo}`);
    expect(router.url).toBe(`/${menu.prefijo}`);
  });

  it.each(['/estudiante', '/estudiante/mis-practicas', '/reportes/nuevo', '/', '/coordinador'])(
    'sin sesión, %s -> /login',
    async (url) => {
      const { router } = await app(null);
      await router.navigateByUrl(url);
      expect(router.url).toBe('/login');
    },
  );
});

describe('S3 demo: guard no rebota', () => {
  it.each(['/estudiante/mis-practicas', '/coordinador', '/secretaria', '/reportes/nuevo'])(
    'demo sin sesión abre %s',
    async (url) => {
      const { router } = await app(null, true);
      await router.navigateByUrl(url);
      expect(router.url).toBe(url);
    },
  );

  it('demo pinta la persona de demostración del rol', async () => {
    const { fixture, router } = await app(null, true);
    await router.navigateByUrl('/coordinador');
    fixture.detectChanges();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('.usuario__nombre')?.textContent,
    ).toContain('Coordinador de Computación');
  });
});

describe('S4/S5 login real, sesión en memoria y armazón', () => {
  function loginCon(perfil: Perfil) {
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      imports: [App],
      providers: [
        provideRouter(routes),
        provideHttpClient(),
        { provide: DEMO_MODE, useValue: false },
        {
          provide: ApiClient,
          useValue: {
            post: (r: string) =>
              r === '/auth/token/' ? of({ access: 'a1', refresh: 'r1' }) : of(undefined),
            get: () => of(perfil),
          },
        },
      ],
    });
    return { router: TestBed.inject(Router), sesion: TestBed.inject(SesionService) };
  }

  it('la sesión sobrevive a la navegación y el armazón muestra la cuenta real', async () => {
    const { router, sesion } = loginCon({ nombre: 'Luciana Mendieta', rol: 'estudiante' });
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    await new Promise<void>((r) => sesion.iniciarSesion('u', 'c').subscribe(() => r()));
    await new Promise<void>((r) => sesion.cargarPerfil().subscribe(() => r()));
    expect(sesion.autenticado()).toBe(true);
    await router.navigateByUrl('/estudiante/mis-practicas');
    expect(router.url).toBe('/estudiante/mis-practicas');
    await router.navigateByUrl('/coordinador');
    expect(router.url).toBe('/estudiante');
    fixture.detectChanges();
    const vista = fixture.nativeElement as HTMLElement;
    expect(vista.querySelector('.usuario__nombre')?.textContent).toContain('Luciana Mendieta');
    expect(vista.querySelector('.campana b')).toBeNull();
  });

  it.each([
    ['estudiante', '/estudiante'],
    ['tutor_academico', '/tutor-academico'],
    ['tutor_entidad', '/tutor-entidad'],
    ['coordinador', '/coordinador'],
    ['director', '/director'],
    ['secretaria', '/secretaria'],
  ])('el login del rol %s navega a %s', async (rol, destino) => {
    const { router } = loginCon({ nombre: 'Prueba', rol });
    const fixture = TestBed.createComponent(Login);
    fixture.detectChanges();
    fixture.componentInstance.form.setValue({ usuario: 'u', clave: 'c' });
    fixture.componentInstance.enviar();
    for (let i = 0; i < 20 && router.url !== destino; i++)
      await new Promise((r) => setTimeout(r, 10));
    expect(router.url).toBe(destino);
  });

  it('rol sin tablero: no navega, avisa y limpia la sesión', async () => {
    const { router, sesion } = loginCon({ nombre: 'Analista', rol: 'analista' });
    const fixture = TestBed.createComponent(Login);
    fixture.detectChanges();
    fixture.componentInstance.form.setValue({ usuario: 'u', clave: 'c' });
    fixture.componentInstance.enviar();
    await new Promise((r) => setTimeout(r, 50));
    fixture.detectChanges();
    expect(router.url).toBe('/');
    expect((fixture.nativeElement as HTMLElement).textContent).toContain(
      'no tiene un tablero habilitado',
    );
    expect(sesion.autenticado()).toBe(false);
  });
});

describe('S6 colisiones y banner', () => {
  it('sin rutas duplicadas y /login fuera del tablero', () => {
    const hijos = routes.find((r) => r.path === '' && r.component)!.children!;
    const paths = hijos.map((r) => r.path);
    expect(new Set(paths).size).toBe(paths.length);
    expect(paths).not.toContain('login');
    expect(routes[0].path).toBe('login');
  });

  it('el banner usa la foto JPG', async () => {
    const { fixture, router } = await app(null, true);
    await router.navigateByUrl('/coordinador');
    fixture.detectChanges();
    expect(
      (fixture.nativeElement as HTMLElement)
        .querySelector('.banner--foto img.escena')
        ?.getAttribute('src'),
    ).toBe('/img/campus-unl.jpg');
  });
});
