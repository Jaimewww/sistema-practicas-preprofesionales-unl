import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { Kpi } from './kpi';
import { KpiGrid } from './kpi-grid';

@Component({
  imports: [Kpi, KpiGrid],
  template: `<app-kpi-grid [tres]="true"><app-kpi etiqueta="Prácticas" [valor]="150" nota="en la carrera" /><app-kpi etiqueta="Alertas" [valor]="7" [alerta]="true" /></app-kpi-grid>`,
})
class Anfitrion {}

describe('Kpi y KpiGrid', () => {
  it('muestra etiqueta, valor y nota, y marca la variante de alerta', () => {
    const fixture = TestBed.createComponent(Anfitrion);
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    const [a, b] = [...el.querySelectorAll('app-kpi')];
    expect(a.querySelector('small')?.textContent).toBe('Prácticas');
    expect(a.querySelector('strong')?.textContent).toBe('150');
    expect(a.querySelector('span')?.textContent).toBe('en la carrera');
    expect(a.classList.contains('alerta')).toBe(false);
    expect(b.classList.contains('alerta')).toBe(true);
    expect(b.querySelector('span')).toBeNull();
    expect(el.querySelector('app-kpi-grid')?.classList.contains('tres')).toBe(true);
  });
});
