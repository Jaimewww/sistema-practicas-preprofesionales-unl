import { TestBed } from '@angular/core/testing';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';
import { SesionService } from '../auth/sesion.service';
import { authInterceptor } from '../auth/auth.interceptor';
import { ApiClient } from './api-client';
import { apiErrorInterceptor } from './api-error.interceptor';
import { ApiError } from './envelope';

describe('ApiClient + interceptores', () => {
  let api: ApiClient;
  let http: HttpTestingController;
  const url = `${environment.apiBaseUrl}/practicas/1/reportes/`;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor, apiErrorInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    api = TestBed.inject(ApiClient);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('desenvuelve data del envelope y adjunta el Bearer si hay sesión', async () => {
    TestBed.inject(SesionService).guardarTokens('abc');
    const respuesta = firstValueFrom(api.post<{ id: number }>('/practicas/1/reportes/', { semana: 1, horas_reportadas: 8 }));
    const req = http.expectOne(url);
    expect(req.request.headers.get('Authorization')).toBe('Bearer abc');
    req.flush({ success: true, message: '', data: { id: 5 }, errors: null, meta: {} }, { status: 201, statusText: 'Created' });
    expect(await respuesta).toEqual({ id: 5 });
  });

  it('sin sesión no manda Authorization', () => {
    api.get('/practicas/').subscribe();
    const req = http.expectOne(`${environment.apiBaseUrl}/practicas/`);
    expect(req.request.headers.has('Authorization')).toBe(false);
    req.flush({ success: true, message: '', data: [], errors: null, meta: {} });
  });

  it('convierte un error de dominio en ApiError con su code', async () => {
    const respuesta = firstValueFrom(api.post('/practicas/1/reportes/', {}));
    http.expectOne(url).flush(
      { success: false, message: 'Ya existe', data: null, errors: { detail: 'Ya existe un reporte para esa semana.', code: 'semana_duplicada' }, meta: {} },
      { status: 409, statusText: 'Conflict' },
    );
    await expect(respuesta).rejects.toEqual(new ApiError(409, 'semana_duplicada', 'Ya existe un reporte para esa semana.'));
  });

  it('convierte un 400 en validacion con los mensajes por campo', async () => {
    const respuesta = firstValueFrom(api.post('/practicas/1/reportes/', {}));
    http.expectOne(url).flush(
      { success: false, message: 'Datos inválidos.', data: null, errors: { horas_reportadas: ['Máximo 168.'] }, meta: {} },
      { status: 400, statusText: 'Bad Request' },
    );
    const error = (await respuesta.catch((e: unknown) => e)) as ApiError;
    expect([error.status, error.code, error.campos]).toEqual([400, 'validacion', { horas_reportadas: ['Máximo 168.'] }]);
  });

  it('sin respuesta (red o CORS) da status 0 sin_conexion', async () => {
    const respuesta = firstValueFrom(api.get('/practicas/'));
    http.expectOne(`${environment.apiBaseUrl}/practicas/`).error(new ProgressEvent('error'), { status: 0 });
    const error = (await respuesta.catch((e: unknown) => e)) as ApiError;
    expect([error.status, error.code]).toEqual([0, 'sin_conexion']);
  });
});
