import { TestBed } from '@angular/core/testing';
import { BarraHoras } from './barra-horas';

function montar(entradas: Record<string, unknown>) {
  const fixture = TestBed.createComponent(BarraHoras);
  for (const [k, v] of Object.entries(entradas)) fixture.componentRef.setInput(k, v);
  fixture.detectChanges();
  return fixture.nativeElement as HTMLElement;
}

describe('BarraHoras', () => {
  it('describe las horas en aria-label y dibuja los tramos', () => {
    const el = montar({ validadas: 96, enRevision: 16, requeridas: 240, esperadas: 135 });
    expect(el.querySelector('[role=img]')?.getAttribute('aria-label')).toBe('96 h validadas y 16 h en revisión de 240 h requeridas. Esperadas a la fecha: 135 h');
    expect((el.querySelector('.v') as HTMLElement).style.width).toBe('40%');
    expect((el.querySelector('.e') as HTMLElement).style.left).toBe('56.25%');
    expect(el.querySelector('.leyenda')?.textContent).toContain('Requeridas: 240 h');
  });

  it('sin esperadas no hay marca ni su entrada en la leyenda; la leyenda se puede ocultar', () => {
    const el = montar({ validadas: 10, enRevision: 0, requeridas: 100, leyenda: false });
    expect(el.querySelector('.e')).toBeNull();
    expect(el.querySelector('.leyenda')).toBeNull();
  });

  it('el tramo en revisión no pasa del 100 %', () => {
    const el = montar({ validadas: 90, enRevision: 50, requeridas: 100 });
    expect((el.querySelector('.r') as HTMLElement).style.width).toBe('10%');
  });
});
