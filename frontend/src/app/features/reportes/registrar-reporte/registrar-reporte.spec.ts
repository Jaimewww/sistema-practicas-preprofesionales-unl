import { TestBed } from '@angular/core/testing';
import { ReportesApi } from '../reportes.api';
import { ReportesMock } from '../reportes.mock';
import { RegistrarReporte } from './registrar-reporte';

describe('RegistrarReporte (E4) contra el mock', () => {
  async function enviar(semana: number, horas: number) {
    const fixture = TestBed.createComponent(RegistrarReporte);
    fixture.componentInstance.form.setValue({ semana, horas_reportadas: horas });
    fixture.componentInstance.enviar();
    await new Promise((r) => setTimeout(r, 0)); // deja salir la respuesta del mock (timer)
    await fixture.whenStable();
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [RegistrarReporte],
      providers: [{ provide: ReportesApi, useFactory: () => Object.assign(new ReportesMock(), { demoraMs: 0 }) }],
    });
  });

  it('201: confirma la semana enviada', async () => {
    const vista = await enviar(1, 12);
    expect(vista.querySelector('[role=status]')?.textContent).toContain('semana 1 enviado (en_revision)');
  });

  it('400: muestra el error del servidor', async () => {
    const vista = await enviar(1, 200);
    expect(vista.querySelector('[role=alert]')?.textContent).toContain('Datos inválidos.');
  });
});
