import { TestBed } from '@angular/core/testing';
import { Pasos } from './pasos';

describe('Pasos', () => {
  it('lista los pasos con símbolo oculto y el estado como texto', () => {
    const fixture = TestBed.createComponent(Pasos);
    fixture.componentRef.setInput('pasos', [
      { estado: 'done', titulo: 'Plan validado', detalle: '10/04/2026' },
      { estado: 'bad', titulo: 'Semana 7' },
      { estado: 'now', titulo: 'Semana 8' },
      { estado: 'pendiente', titulo: 'Informe final' },
    ]);
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    const items = [...el.querySelectorAll('li')];
    expect(items.map((li) => li.className)).toEqual(['done', 'bad', 'now', 'pendiente']);
    expect(items.map((li) => li.querySelector('.punto')?.textContent)).toEqual(['✓', '!', '●', '·']);
    expect(items[0].querySelector('.punto')?.getAttribute('aria-hidden')).toBe('true');
    expect(items[1].querySelector('.sr-only')?.textContent).toBe('(Con observación)');
    expect(items[0].querySelector('.detalle')?.textContent).toBe('10/04/2026');
    expect(items[1].querySelector('.detalle')).toBeNull();
    expect(el.querySelector('ol')).not.toBeNull();
  });
});
