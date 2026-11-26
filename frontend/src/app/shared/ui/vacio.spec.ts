import { TestBed } from '@angular/core/testing';
import { Vacio } from './vacio';

describe('Vacio', () => {
  it('muestra el título y el texto', () => {
    const fixture = TestBed.createComponent(Vacio);
    fixture.componentRef.setInput('titulo', 'Sin resultados');
    fixture.componentRef.setInput('texto', 'Cambie los filtros.');
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('strong')?.textContent).toBe('Sin resultados');
    expect(el.textContent).toContain('Cambie los filtros.');
  });
});
