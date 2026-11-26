import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { Shell } from './shell';

@Component({ template: '<p class="pagina-de-prueba">contenido</p>' })
class Pagina {}

describe('Shell', () => {
  async function montar() {
    TestBed.configureTestingModule({
      imports: [Shell],
      providers: [provideRouter([{ path: 'reportes/nuevo', component: Pagina, title: 'Registrar horas · Prácticas UNL' }])],
    });
    const harness = await RouterTestingHarness.create();
    await harness.navigateByUrl('/reportes/nuevo');
    const fixture = TestBed.createComponent(Shell);
    await fixture.whenStable();
    fixture.detectChanges();
    return { fixture, vista: fixture.nativeElement as HTMLElement };
  }

  it('pinta el menú lateral con sus enlaces', async () => {
    const { vista } = await montar();
    const enlaces = [...vista.querySelectorAll('aside a')].map((a) => a.textContent?.trim());
    expect(enlaces).toEqual(['Menú Principal', 'Tablero', 'Registrar horas']);
    expect(vista.querySelector('aside a[href="/reportes/nuevo"]')).not.toBeNull();
    expect(vista.querySelector('.etiqueta')?.textContent).toBe('Módulo académico');
    expect(vista.querySelector('.marca__texto')?.textContent).toContain('Siaaf');
  });

  it('muestra la mascota con su texto alternativo', async () => {
    const { vista } = await montar();
    const oso = vista.querySelector('.mascota img');
    expect(oso?.getAttribute('alt')).toBe('Mascota UNL: oso con suéter rojo y libro');
    expect(oso?.getAttribute('src')).toBe('/img/mascota-unl.png');
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
    expect(vista.querySelector('h1')?.textContent).toBe('Sistema de Información Académico, Administrativo y Financiero');
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
    const enlace = vista.querySelector('.usuario__menu a');
    expect(enlace?.textContent).toBe('Iniciar sesión');
    expect(enlace?.getAttribute('href')).toBe('/login');
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

  it('sin notificaciones no pinta el contador de la campana', async () => {
    const { vista } = await montar();
    expect(vista.querySelector('.campana b')).toBeNull();
  });
});
