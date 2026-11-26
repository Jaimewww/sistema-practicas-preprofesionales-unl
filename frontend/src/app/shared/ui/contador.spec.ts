import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { Contador } from './contador';

@Component({
  imports: [ReactiveFormsModule, Contador],
  template: `<app-contador [formControl]="control" etiqueta="horas" idControl="horas" unidad="h" [min]="1" [max]="10" [paso]="2" />`,
})
class Anfitrion {
  control = new FormControl<number | null>(5);
}

describe('Contador', () => {
  function montar() {
    const fixture = TestBed.createComponent(Anfitrion);
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    const menos = el.querySelector<HTMLButtonElement>('button[aria-label="Disminuir horas"]')!;
    const mas = el.querySelector<HTMLButtonElement>('button[aria-label="Aumentar horas"]')!;
    const entrada = el.querySelector<HTMLInputElement>('#horas')!;
    return { fixture, control: fixture.componentInstance.control, menos, mas, entrada, el };
  }

  it('lee el valor del control y expone etiquetas accesibles y unidad', () => {
    const { entrada, menos, mas, el } = montar();
    expect(entrada.value).toBe('5');
    expect(entrada.type).toBe('number');
    expect(entrada.getAttribute('aria-label')).toBe('horas');
    expect(menos.type).toBe('button');
    expect(mas.type).toBe('button');
    expect(el.querySelector('.unidad')?.textContent).toBe('h');
  });

  it('+ y − mueven el control de a «paso»', () => {
    const { fixture, control, menos, mas } = montar();
    mas.click();
    fixture.detectChanges();
    expect(control.value).toBe(7);
    menos.click();
    menos.click();
    expect(control.value).toBe(3);
  });

  it('no pasa de [min, max] y deshabilita el botón del límite', () => {
    const { fixture, control, menos, mas } = montar();
    mas.click();
    mas.click();
    mas.click();
    fixture.detectChanges();
    expect(control.value).toBe(10);
    expect(mas.disabled).toBe(true);
    control.setValue(1);
    fixture.detectChanges();
    expect(menos.disabled).toBe(true);
    menos.click();
    expect(control.value).toBe(1);
  });

  it('se puede escribir: emite el número tecleado y al terminar lo ajusta al rango', () => {
    const { fixture, control, entrada } = montar();
    entrada.value = '8';
    entrada.dispatchEvent(new Event('input'));
    expect(control.value).toBe(8);
    entrada.value = '99';
    entrada.dispatchEvent(new Event('input'));
    expect(control.value).toBe(99);
    entrada.dispatchEvent(new Event('change'));
    fixture.detectChanges();
    expect(control.value).toBe(10);
    expect(entrada.value).toBe('10');
    entrada.value = '';
    entrada.dispatchEvent(new Event('input'));
    expect(control.value).toBeNull();
    entrada.dispatchEvent(new Event('change'));
    expect(control.value).toBe(1);
  });

  it('un control deshabilitado deshabilita botones y campo', () => {
    const { fixture, control, menos, mas, entrada } = montar();
    control.disable();
    fixture.detectChanges();
    expect([menos.disabled, mas.disabled, entrada.disabled]).toEqual([true, true, true]);
  });
});
