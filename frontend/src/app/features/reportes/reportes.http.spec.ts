import { TestBed } from '@angular/core/testing';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';
import { apiErrorInterceptor } from '../../core/api/api-error.interceptor';
import { ApiError } from '../../core/api/envelope';
import type { HorasPractica, Reporte } from './reporte.model';
import { ReportesHttp } from './reportes.http';

/** Contrato de OpenAPI (GET /api/v1/schema/) contra lo que manda y recibe el servicio. */
describe('ReportesHttp', () => {
  let servicio: ReportesHttp;
  let http: HttpTestingController;
  const base = environment.apiBaseUrl;
  const envelope = <T>(data: T) => ({ success: true, message: '', data, errors: null, meta: {} });

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        ReportesHttp,
        provideHttpClient(withInterceptors([apiErrorInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    servicio = TestBed.inject(ReportesHttp);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('crear: POST /practicas/{id}/reportes/ con exactamente semana y horas_reportadas', async () => {
    const creado: Reporte = {
      id: 9, practica_id: 3, semana: 3, horas_reportadas: 12,
      estado: 'en_revision', requiere_revision: false, fecha_registro: '2026-11-25T12:00:00Z',
    };
    // Aunque llegue un objeto con campos de más, el servicio solo manda los dos escribibles.
    const cuerpo = { semana: 3, horas_reportadas: 12, estado: 'validado' } as never;
    const respuesta = firstValueFrom(servicio.crear(3, cuerpo));

    const req = http.expectOne(`${base}/practicas/3/reportes/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ semana: 3, horas_reportadas: 12 });
    req.flush(envelope(creado), { status: 201, statusText: 'Created' });

    expect(await respuesta).toEqual(creado);
  });

  it('crear: un 409 semana_duplicada llega como ApiError', async () => {
    const respuesta = firstValueFrom(servicio.crear(3, { semana: 3, horas_reportadas: 12 }));
    http.expectOne(`${base}/practicas/3/reportes/`).flush(
      { success: false, message: '', data: null, errors: { detail: 'Ya existe un reporte para esa semana.', code: 'semana_duplicada' }, meta: {} },
      { status: 409, statusText: 'Conflict' },
    );
    const error = (await respuesta.catch((e: unknown) => e)) as ApiError;
    expect([error.status, error.code]).toEqual([409, 'semana_duplicada']);
  });

  it('horas: GET /practicas/{id}/horas/ devuelve el resumen', async () => {
    const resumen: HorasPractica = {
      horas_validadas: 96, horas_en_revision: 12, horas_requeridas: 240, horas_faltantes: 144, semana_en_revision: true,
    };
    const respuesta = firstValueFrom(servicio.horas(3));
    const req = http.expectOne(`${base}/practicas/3/horas/`);
    expect(req.request.method).toBe('GET');
    req.flush(envelope(resumen));
    expect(await respuesta).toEqual(resumen);
  });
});
