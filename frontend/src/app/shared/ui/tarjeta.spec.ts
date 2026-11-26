import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { Tarjeta } from './tarjeta';

@Component({
  imports: [Tarjeta],
  template: `<app-tarjeta titulo="Avance" sub="Solo horas validadas" [span]="7"><button acciones>Exportar</button><p class="cuerpo">Contenido</p></app-tarjeta>`,
})
class Anfitrion {}

describe('Tarjeta', () => {
  it('titula la sección, proyecta acciones y cuerpo, y aplica la clase de columnas', () => {
    const fixture = TestBed.createComponent(Anfitrion);
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    const seccion = el.querySelector('section')!;
    const titulo = el.querySelector('h3')!;
    expect(seccion.getAttribute('aria-labelledby')).toBe(titulo.id);
    expect(titulo.textContent).toBe('Avance');
    expect(el.querySelector('.sub')?.textContent).toBe('Solo horas validadas');
    expect(el.querySelector('.acciones button')?.textContent).toBe('Exportar');
    expect(el.querySelector('.cuerpo')?.textContent).toBe('Contenido');
    expect(el.querySelector('app-tarjeta')?.classList.contains('span-7')).toBe(true);
  });
});
