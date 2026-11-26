import { TestBed } from '@angular/core/testing';
import { Insignia } from './insignia';

describe('Insignia', () => {
  it.each(['ok', 'warn', 'bad', 'info'] as const)('«%s» pinta ícono oculto y el texto, no solo color', (tipo) => {
    const fixture = TestBed.createComponent(Insignia);
    fixture.componentRef.setInput('tipo', tipo);
    fixture.componentRef.setInput('texto', 'Al día');
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    expect(el.classList.contains(`insignia--${tipo}`)).toBe(true);
    expect(el.querySelector('svg')?.getAttribute('aria-hidden')).toBe('true');
    expect(el.textContent?.trim()).toBe('Al día');
  });
});
