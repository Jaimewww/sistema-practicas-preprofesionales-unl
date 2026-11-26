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
    fixture.componentInstance.enviar();
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

  it('409: la misma semana otra vez muestra el mensaje del servidor', async () => {
    const fixture = await crear();
    await enviar(fixture, 1, 12);
    const vista = await enviar(fixture, 1, 12);
    expect(vista.querySelector('.aviso-exito')).toBeNull();
    expect(vista.querySelector('.aviso-error[role=alert]')?.textContent).toContain(
      'La práctica ya tiene un reporte registrado para esa semana.',
    );
  });

  it('400: muestra el error del servidor', async () => {
    const vista = await enviar(await crear(), 1, 200);
    expect(vista.querySelector('[role=alert]')?.textContent).toContain('Datos inválidos.');
  });

  it('mientras envía, el botón queda deshabilitado y dice «Enviando…»', async () => {
    const fixture = await crear();
    fixture.componentInstance.enviar();
    fixture.detectChanges();
    const boton = (fixture.nativeElement as HTMLElement).querySelector('button')!;
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
});
