import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { Pestanas } from './pestanas';

@Component({ template: '' })
class Vacia {}

@Component({
  imports: [Pestanas],
  template: `<app-pestanas etiqueta="Secciones de la práctica" [items]="items" />`,
})
class Anfitrion {
  items = [
    { texto: 'Resumen', enlace: '/estudiante/practica' },
    { texto: 'Plan', enlace: '/estudiante/practica/plan' },
  ];
}

describe('Pestanas', () => {
  it('enlaza con el router y marca solo la pestaña activa con aria-current', async () => {
    TestBed.configureTestingModule({
      providers: [provideRouter([{ path: 'estudiante/practica', component: Vacia }, { path: 'estudiante/practica/plan', component: Vacia }])],
    });
    await RouterTestingHarness.create('/estudiante/practica/plan');
    const fixture = TestBed.createComponent(Anfitrion);
    await fixture.whenStable();
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('ul')?.getAttribute('aria-label')).toBe('Secciones de la práctica');
    const enlaces = [...el.querySelectorAll('a')];
    expect(enlaces.map((a) => a.getAttribute('href'))).toEqual(['/estudiante/practica', '/estudiante/practica/plan']);
    expect(enlaces.map((a) => a.getAttribute('aria-current'))).toEqual([null, 'page']);
  });
});
