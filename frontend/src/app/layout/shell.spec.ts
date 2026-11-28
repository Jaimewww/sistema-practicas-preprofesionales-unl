import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { DEMO_MODE } from '../core/auth/dashboard.guard';
import { SesionService } from '../core/auth/sesion.service';
import { Shell } from './shell';

@Component({ template: '<p class="pagina-de-prueba">contenido</p>' })
class Pagina {}

describe('Shell', () => {
  async function montar(url = '/reportes/nuevo') {
    TestBed.configureTestingModule({
      imports: [Shell],
      providers: [
        provideRouter([
          { path: 'reportes/nuevo', component: Pagina, title: 'Registrar horas · Prácticas UNL' },
          { path: 'entidad-receptora', component: Pagina, title: 'Tablero · Prácticas UNL' },
        ]),
      ],
    });
    const harness = await RouterTestingHarness.create();
    await harness.navigateByUrl(url);
    const fixture = TestBed.createComponent(Shell);
    await fixture.whenStable();
    fixture.detectChanges();
    return { fixture, vista: fixture.nativeElement as HTMLElement };
  }

  it('pinta el menú lateral con sus enlaces', async () => {
    const { vista } = await montar();
    const enlaces = [...vista.querySelectorAll('aside a')].map((a) => a.textContent?.trim());
    expect(enlaces).toEqual(['Menú Principal', 'Tablero', 'Mis prácticas']);
    expect(vista.querySelector('aside a[href="/estudiante/mis-practicas"]')).not.toBeNull();
    expect(vista.querySelector('.etiqueta')?.textContent).toBe('Módulo académico');
    expect(vista.querySelector('.marca__texto')?.textContent).toContain('Siaaf');
  });

  it('muestra la mascota con su texto alternativo', async () => {
    const { vista } = await montar();
    const oso = vista.querySelector('.oso__cuerpo');
    expect(oso?.getAttribute('alt')).toBe('Mascota UNL: oso con suéter rojo y libro');
    expect(oso?.getAttribute('src')).toBe('/img/oso-cuerpo.png');
    const brazo = vista.querySelector('.oso__brazo');
    expect(brazo?.getAttribute('aria-hidden')).toBe('true');
    expect(brazo?.getAttribute('src')).toBe('/img/oso-brazo.png');
  });

  it('muestra el logo de la UNL con su texto alternativo y sin onda en el banner', async () => {
    const { vista } = await montar();
    const logo = vista.querySelector('.unl img');
    expect(logo?.getAttribute('alt')).toBe('Universidad Nacional de Loja');
    expect(logo?.getAttribute('src')).toBe('/img/logo-unl.png');
    expect(vista.querySelector('.onda')).toBeNull();
    expect(vista.querySelector('app-pagina-banner svg.onda, app-pagina-banner > svg')).toBeNull();
  });

  it('pone el título del sistema, el pie y el banner con el título de la ruta', async () => {
    const { vista } = await montar();
    expect(vista.querySelector('h1')?.textContent).toBe(
      'Sistema de Información Académico, Administrativo y Financiero',
    );
    expect(vista.querySelector('.titulo')?.textContent).toBe('Registrar horas');
    expect(vista.querySelector('.migas')?.textContent).toContain('Inicio');
    expect(vista.querySelector('footer')?.textContent).toContain(
      '2026 © Sistema de Información Académico, Administrativo y Financiero · Universidad Nacional de Loja',
    );
  });

  it('el menú de usuario ofrece «Iniciar sesión» hacia /login', async () => {
    const { fixture, vista } = await montar();
    expect(vista.querySelector('.usuario__menu')).toBeNull();
    (vista.querySelector('.usuario__boton') as HTMLButtonElement).click();
    fixture.detectChanges();
    const enlace = vista.querySelector('.usuario__menu a[href="/login"]');
    expect(enlace?.textContent).toBe('Iniciar sesión');
  });

  it('el botón de hamburguesa abre y cierra la barra lateral', async () => {
    const { fixture, vista } = await montar();
    const boton = vista.querySelector('.menu-boton') as HTMLButtonElement;
    expect(boton.getAttribute('aria-expanded')).toBe('false');
    boton.click();
    fixture.detectChanges();
    expect(boton.getAttribute('aria-expanded')).toBe('true');
    expect(vista.querySelector('.shell')?.classList.contains('abierto')).toBe(true);
    (vista.querySelector('.velo') as HTMLButtonElement).click();
    fixture.detectChanges();
    expect(vista.querySelector('.shell')?.classList.contains('abierto')).toBe(false);
  });

  it('con notificaciones pinta el contador de la campana', async () => {
    const { vista } = await montar();
    expect(vista.querySelector('.campana b')?.textContent?.trim()).toBe('3');
  });

  it('sin notificaciones no pinta el contador de la campana', async () => {
    const { vista } = await montar('/entidad-receptora');
    expect(vista.querySelector('.campana b')).toBeNull();
  });

  it('el menú lateral cambia con el rol de la URL', async () => {
    const { vista } = await montar('/entidad-receptora');
    const enlaces = [...vista.querySelectorAll('aside a')].map((a) => a.textContent?.trim());
    expect(enlaces).toEqual(['Menú Principal', 'Tablero', 'Catálogo de entidades', 'Convenios']);
    expect(vista.querySelector('.usuario__nombre')?.textContent).toContain('Rectorado UNL');
  });

  it('en modo real muestra la cuenta y el tablero del perfil, sin campana ni selector demo', async () => {
    TestBed.configureTestingModule({
      imports: [Shell],
      providers: [
        provideRouter([
          { path: 'coordinador', component: Pagina, title: 'Tablero · Prácticas UNL' },
        ]),
        { provide: DEMO_MODE, useValue: false },
        {
          provide: SesionService,
          useValue: {
            perfil: () => ({ nombre: 'Ada Lovelace', rol: 'coordinador' }),
            autenticado: () => true,
          },
        },
      ],
    });
    const harness = await RouterTestingHarness.create();
    await harness.navigateByUrl('/coordinador');
    const fixture = TestBed.createComponent(Shell);
    await fixture.whenStable();
    fixture.detectChanges();
    const vista = fixture.nativeElement as HTMLElement;

    expect(vista.querySelector('.usuario__nombre')?.textContent).toContain('Ada Lovelace');
    expect(vista.querySelector('.avatar')?.textContent?.trim()).toBe('AL');
    expect(vista.querySelector('.campana b')).toBeNull();
    expect(vista.querySelector('aside a[href="/coordinador/practicas"]')).not.toBeNull();
    (vista.querySelector('.usuario__boton') as HTMLButtonElement).click();
    fixture.detectChanges();
    expect(vista.querySelector('.usuario__menu')?.textContent).not.toContain(
      'Cambiar de rol (demo)',
    );
  });
});
