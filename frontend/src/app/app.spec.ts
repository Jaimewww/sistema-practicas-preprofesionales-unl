import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { App } from './app';

describe('App', () => {
  it('muestra la navegación a las tres rutas', async () => {
    TestBed.configureTestingModule({ imports: [App], providers: [provideRouter([])] });
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const enlaces = [...(fixture.nativeElement as HTMLElement).querySelectorAll('nav a')];
    expect(enlaces.map((a) => a.textContent?.trim())).toEqual(['Inicio', 'Iniciar sesión', 'Registrar horas']);
  });
});
