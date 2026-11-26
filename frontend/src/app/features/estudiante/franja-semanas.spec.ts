import { TestBed } from '@angular/core/testing';
import { PRACTICAS_DE_LA_ESTUDIANTE } from '../../core/demo';
import { FranjaSemanas } from './ui/franja-semanas';

describe('FranjaSemanas', () => {
  function montar(indice = 0) {
    const fixture = TestBed.createComponent(FranjaSemanas);
    const p = PRACTICAS_DE_LA_ESTUDIANTE[indice];
    fixture.componentRef.setInput('reportes', p.reportes);
    fixture.componentRef.setInput('semanaActual', p.semanaActual);
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  it('dibuja las 16 semanas, cada una con texto accesible además del color', () => {
    const celdas = [...montar().querySelectorAll('ol.semanas li')];
    expect(celdas).toHaveLength(16);
    for (const celda of celdas) {
      expect(celda.querySelector('.sr-only')?.textContent).toMatch(/^Semana \d+: /);
      expect(celda.querySelector('.forma')?.getAttribute('aria-hidden')).toBe('true');
    }
  });

  it('dice el estado de cada semana: validada, devuelta, sin reporte, actual y futura', () => {
    const textos = [...montar().querySelectorAll('ol.semanas .sr-only')].map((n) => n.textContent);
    expect(textos[0]).toBe('Semana 1: Validado');
    expect(textos[4]).toBe('Semana 5: Devuelto con observación');
    expect(textos[7]).toBe('Semana 8: En revisión');
    expect(textos[8]).toBe('Semana 9: Sin reporte (semana actual)');
    expect(textos[15]).toBe('Semana 16: Futura');
  });

  it('la leyenda repite los cinco estados con su símbolo', () => {
    const leyenda = [...montar().querySelectorAll('ul.leyenda li')].map((n) => n.textContent?.replace(/\s+/g, ' ').trim());
    expect(leyenda).toEqual(['✓Validado', '…En revisión', '!Devuelto', '✕Sin reporte', '–Futura']);
  });
});
