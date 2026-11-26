import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { Aviso } from './aviso';

@Component({ imports: [Aviso], template: `<app-aviso tipo="bad">Falta el motivo</app-aviso><app-aviso tipo="ok">Guardado</app-aviso>` })
class Anfitrion {}

describe('Aviso', () => {
  it('«bad» se anuncia como alerta y el resto como estado; el ícono está oculto', () => {
    const fixture = TestBed.createComponent(Anfitrion);
    fixture.detectChanges();
    const [malo, bueno] = [...(fixture.nativeElement as HTMLElement).querySelectorAll('app-aviso')];
    expect(malo.getAttribute('role')).toBe('alert');
    expect(malo.textContent).toContain('Falta el motivo');
    expect(malo.querySelector('svg')?.getAttribute('aria-hidden')).toBe('true');
    expect(bueno.getAttribute('role')).toBe('status');
  });
});
