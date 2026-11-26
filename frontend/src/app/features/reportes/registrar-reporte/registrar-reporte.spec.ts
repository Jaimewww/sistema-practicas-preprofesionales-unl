import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReportesApi } from '../reportes.api';
import { ReportesMock } from '../reportes.mock';
import { RegistrarReporte } from './registrar-reporte';

describe('RegistrarReporte (E4) contra el mock', () => {
  const esperar = async (fixture: ComponentFixture<RegistrarReporte>) => {
    await new Promise((r) => setTimeout(r, 0)); // deja salir la respuesta del mock (timer)
    await fixture.whenStable();
    fixture.detectChanges();
  };

  async function crear() {
    const fixture = TestBed.createComponent(RegistrarReporte);
    fixture.detectChanges();
    await esperar(fixture);
    return fixture;
  }

  async function enviar(fixture: ComponentFixture<RegistrarReporte>, semana: number, horas: number) {
    fixture.componentInstance.form.setValue({ semana, horas_reportadas: horas });
    // true: salta la validación del frontend para probar que el backend valida igual
    fixture.componentInstance.enviar(true);
    await esperar(fixture);
    return fixture.nativeElement as HTMLElement;
  }

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [RegistrarReporte],
      providers: [{ provide: ReportesApi, useFactory: () => Object.assign(new ReportesMock(), { demoraMs: 0 }) }],
    });
  });

  it('201: confirma semana, horas, estado «en revisión» y fecha', async () => {
    const vista = await enviar(await crear(), 1, 12);
    const aviso = vista.querySelector('.aviso-exito[role=status]');
    const texto = aviso?.textContent ?? '';
    expect(texto).toContain('Reporte enviado');
    expect(aviso?.querySelectorAll('dd')[0].textContent).toBe('1');
    expect(aviso?.querySelectorAll('dd')[1].textContent).toBe('12');
    expect(aviso?.querySelectorAll('dd')[2].textContent).toBe('en revisión');
    expect(aviso?.querySelectorAll('dd')[3].textContent).toMatch(/^\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}$/);
    expect(vista.querySelector('.aviso-info')).toBeNull();
  });

  it('201 con más de 40 horas: avisa que el tutor lo revisará', async () => {
    const vista = await enviar(await crear(), 2, 50);
    expect(vista.querySelector('.aviso-exito')).not.toBeNull();
    expect(vista.querySelector('.aviso-info')?.textContent).toContain('el tutor lo revisará');
  });

  it('409: la misma semana otra vez muestra «Ya enviaste esa semana»', async () => {
    const fixture = await crear();
    await enviar(fixture, 1, 12);
    const vista = await enviar(fixture, 1, 12);
    expect(vista.querySelector('.aviso-exito')).toBeNull();
    expect(vista.querySelector('.aviso-error[role=alert]')?.textContent).toContain(
      'Ya enviaste esa semana.',
    );
  });

  it('400: muestra el error del campo', async () => {
    const vista = await enviar(await crear(), 1, 200);
    expect(vista.querySelector('[role=alert]')?.textContent).toContain('Una semana tiene 168 horas');
  });

  it('mientras envía, el botón queda deshabilitado y dice «Enviando…»', async () => {
    const fixture = await crear();
    fixture.componentInstance.form.setValue({ semana: 1, horas_reportadas: 12 });
    fixture.componentInstance.enviar();
    fixture.detectChanges();
    const boton = (fixture.nativeElement as HTMLElement).querySelector<HTMLButtonElement>('button[type=submit]')!;
    expect(boton.disabled).toBe(true);
    expect(boton.textContent).toContain('Enviando…');
    await esperar(fixture);
    expect(boton.disabled).toBe(false);
  });

  it('muestra las horas acumuladas al cargar', async () => {
    const vista = (await crear()).nativeElement as HTMLElement;
    expect(vista.querySelector('[data-horas=validadas]')?.textContent).toContain('96');
    expect(vista.querySelector('[data-horas=en-revision]')?.textContent).toContain('12');
    expect(vista.querySelector('[data-horas=faltantes]')?.textContent).toContain('144');
  });

  it('vuelve a pedir las horas tras un 201', async () => {
    const fixture = await crear();
    const api = TestBed.inject(ReportesApi);
    const espia = vi.spyOn(api, 'horas');
    await enviar(fixture, 3, 10);
    expect(espia).toHaveBeenCalledWith(1);
  });

  it('contador: «+» en horas incrementa el control y «−» se deshabilita en el mínimo', async () => {
    const fixture = await crear();
    const vista = fixture.nativeElement as HTMLElement;
    const menos = vista.querySelector<HTMLButtonElement>('button[aria-label="Disminuir horas"]')!;
    const mas = vista.querySelector<HTMLButtonElement>('button[aria-label="Aumentar horas"]')!;
    const control = fixture.componentInstance.form.controls.horas_reportadas;
    control.setValue(1);
    fixture.detectChanges();
    expect(menos.disabled).toBe(true);
    expect(menos.type).toBe('button');
    mas.click();
    fixture.detectChanges();
    expect(control.value).toBe(2);
    expect(menos.disabled).toBe(false);
    expect(vista.querySelector<HTMLInputElement>('#horas')?.type).toBe('number');
    control.setValue(168);
    fixture.detectChanges();
    expect(mas.disabled).toBe(true);
  });

  it('contador de semana: respeta el mínimo 1 y el máximo 52', async () => {
    const fixture = await crear();
    const vista = fixture.nativeElement as HTMLElement;
    const control = fixture.componentInstance.form.controls.semana;
    vista.querySelector<HTMLButtonElement>('button[aria-label="Aumentar semana"]')!.click();
    expect(control.value).toBe(2);
    control.setValue(52);
    fixture.detectChanges();
    expect(vista.querySelector<HTMLButtonElement>('button[aria-label="Aumentar semana"]')!.disabled).toBe(true);
    control.setValue(1);
    fixture.detectChanges();
    expect(vista.querySelector<HTMLButtonElement>('button[aria-label="Disminuir semana"]')!.disabled).toBe(true);
  });
  it('contador: también se puede escribir el valor con el teclado', async () => {
    const fixture = await crear();
    const vista = fixture.nativeElement as HTMLElement;
    const entrada = vista.querySelector<HTMLInputElement>('#horas')!;
    expect(entrada.readOnly).toBe(false);
    entrada.value = '40';
    entrada.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    expect(fixture.componentInstance.form.controls.horas_reportadas.value).toBe(40);
  });

  it('con horas 200 el frontend no llama al servidor y marca el campo', async () => {
    const fixture = await crear();
    fixture.componentInstance.form.setValue({ semana: 1, horas_reportadas: 200 });
    fixture.componentInstance.enviar();
    await esperar(fixture);
    const vista = fixture.nativeElement as HTMLElement;
    expect(fixture.componentInstance.estado().tipo).toBe('inicial');
    expect(vista.querySelector('.campo--error')?.textContent).toContain('168 horas');
  });

  it('409 práctica no en curso: deshabilita el envío', async () => {
    const fixture = TestBed.createComponent(RegistrarReporte);
    fixture.componentRef.setInput('practicaId', 409);
    fixture.detectChanges();
    await esperar(fixture);
    const vista = await enviar(fixture, 1, 12);
    expect(vista.querySelector('.aviso-error')?.textContent).toContain('La práctica no está en curso.');
    expect(vista.querySelector<HTMLButtonElement>('button[type=submit]')?.disabled).toBe(true);
  });

  it('404: indica volver al selector', async () => {
    const fixture = TestBed.createComponent(RegistrarReporte);
    fixture.componentRef.setInput('practicaId', 404);
    fixture.detectChanges();
    await esperar(fixture);
    const vista = await enviar(fixture, 1, 12);
    expect(vista.querySelector('.aviso-error')?.textContent).toContain('No encontramos esa práctica.');
    expect(vista.querySelector('.aviso-error')?.textContent).toContain('selector');
  });
});
