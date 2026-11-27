import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';
import { authInterceptor } from '../../core/auth/auth.interceptor';
import { apiErrorInterceptor } from '../../core/api/api-error.interceptor';
import type { ApiError } from '../../core/api/envelope';
import type { PlanVersion } from './plan-informe.http';
import { PlanInformeHttp } from './plan-informe.http';

/**
 * Adaptador HTTP del plan (C-09) y del informe final del estudiante (C-10).
 *
 * Contrato real (backend `apps/actividades/api.py` y `apps/practicas/api.py`):
 *   GET  /practicas/{id}/plan/            -> 200 [PlanActividadesSerializer]
 *   POST /practicas/{id}/plan/            {contenido} -> 201 PlanActividadesSerializer
 *   GET  /practicas/{id}/informe-final/   -> 200 detalle con devolución, 404 si no hay
 *   POST /practicas/{id}/informe-final/   multipart {archivo} -> 201 InformeEstudiante
 */
describe('PlanInformeHttp', () => {
  let servicio: PlanInformeHttp;
  let http: HttpTestingController;

  const planUrl = `${environment.apiBaseUrl}/practicas/7/plan/`;
  const informeUrl = `${environment.apiBaseUrl}/practicas/7/informe-final/`;

  const envelope = <T>(data: T) => ({ success: true, message: '', data, errors: null, meta: {} });

  const version: PlanVersion = {
    id: 11,
    practica_id: 7,
    version: 1,
    contenido: 'Actividad 1: acompañar el taller.\nActividad 2: registrar asistencia.',
    estado: 'en_revision',
    observacion: null,
    fecha_validacion: null,
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        PlanInformeHttp,
        provideHttpClient(withInterceptors([authInterceptor, apiErrorInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    servicio = TestBed.inject(PlanInformeHttp);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  describe('C-09 plan: GET /practicas/{id}/plan/', () => {
    it('pide la URL exacta y devuelve las versiones con su contenido intacto', async () => {
      const respuesta = firstValueFrom(servicio.versiones(7));
      const peticion = http.expectOne(planUrl);
      expect(peticion.request.method).toBe('GET');
      peticion.flush(envelope([version]));
      expect(await respuesta).toEqual([version]);
    });

    it('una práctica sin plan responde 200 con la lista vacía: absence, no error ni versión inventada', async () => {
      const respuesta = firstValueFrom(servicio.versiones(7));
      http.expectOne(planUrl).flush(envelope([]));
      expect(await respuesta).toEqual([]);
    });
  });

  describe('C-09 plan: POST /practicas/{id}/plan/', () => {
    it('envía únicamente {contenido} con el texto heredado tal cual y devuelve la versión creada', async () => {
      const texto = '  Actividad 1: acompañar el taller.\n\nActividad 2: registrar asistencia.  ';
      const respuesta = firstValueFrom(servicio.enviarPlan(7, texto));
      const peticion = http.expectOne(planUrl);
      expect(peticion.request.method).toBe('POST');
      expect(peticion.request.body).toEqual({ contenido: texto });
      expect(Object.keys(peticion.request.body as Record<string, unknown>)).toEqual(['contenido']);
      const creada: PlanVersion = { ...version, contenido: texto };
      peticion.flush(envelope(creada), { status: 201, statusText: 'Created' });
      expect(await respuesta).toEqual(creada);
    });

    it('propaga el 409 plan_no_reenviable como ApiError', async () => {
      const respuesta = firstValueFrom(servicio.enviarPlan(7, 'Actividad 1'));
      http.expectOne(planUrl).flush(
        {
          success: false,
          message: 'La última versión está en revisión.',
          data: null,
          errors: { detail: 'La última versión está en revisión.', code: 'plan_no_reenviable' },
          meta: {},
        },
        { status: 409, statusText: 'Conflict' },
      );
      const error = (await respuesta.catch((e: unknown) => e)) as ApiError;
      expect([error.status, error.code]).toEqual([409, 'plan_no_reenviable']);
    });
  });

  describe('C-10 informe final: GET /practicas/{id}/informe-final/', () => {
    it('pide la URL exacta y devuelve la última versión con su devolución', async () => {
      const detalle = {
        id: 3,
        version: 2,
        estado: 'devuelto' as const,
        fecha: '2026-11-20T10:00:00Z',
        devolucion: {
          observacion: 'Falta el detalle de la semana 8.',
          autor_id: 5,
          fecha: '2026-11-21T09:00:00Z',
        },
      };
      const respuesta = firstValueFrom(servicio.informeFinal(7));
      const peticion = http.expectOne(informeUrl);
      expect(peticion.request.method).toBe('GET');
      peticion.flush(envelope(detalle));
      expect(await respuesta).toEqual(detalle);
    });

    it('sin informe la API responde 404: no se fabrica un detalle', async () => {
      const respuesta = firstValueFrom(servicio.informeFinal(7));
      http.expectOne(informeUrl).flush(
        {
          success: false,
          message: 'No encontrado.',
          data: null,
          errors: { detail: 'No encontrado.', code: 'no_encontrado' },
          meta: {},
        },
        { status: 404, statusText: 'Not Found' },
      );
      const error = (await respuesta.catch((e: unknown) => e)) as ApiError;
      expect([error.status, error.code]).toEqual([404, 'no_encontrado']);
    });
  });

  describe('C-10 informe final: POST /practicas/{id}/informe-final/', () => {
    it('envía multipart con solo `archivo` (sin Content-Type manual ni resumen) y devuelve la versión creada', async () => {
      const archivo = new File(['%PDF-1.4\n'], 'informe-final.pdf', { type: 'application/pdf' });
      const creado = {
        id: 4,
        practica_id: 7,
        version: 1,
        estado: 'en_revision' as const,
        fecha: '2026-11-22T08:00:00Z',
      };
      const respuesta = firstValueFrom(servicio.presentarInformeFinal(7, archivo));
      const peticion = http.expectOne(informeUrl);
      expect(peticion.request.method).toBe('POST');
      const cuerpo = peticion.request.body as FormData;
      expect(cuerpo instanceof FormData).toBe(true);
      expect([...cuerpo.keys()]).toEqual(['archivo']);
      expect(cuerpo.get('archivo')).toBe(archivo);
      expect(peticion.request.headers.has('Content-Type')).toBe(false);
      peticion.flush(envelope(creado), { status: 201, statusText: 'Created' });
      expect(await respuesta).toEqual(creado);
    });

    it('propaga el 409 informe_pendiente como ApiError', async () => {
      const archivo = new File(['%PDF-1.4\n'], 'informe-final.pdf', { type: 'application/pdf' });
      const respuesta = firstValueFrom(servicio.presentarInformeFinal(7, archivo));
      http.expectOne(informeUrl).flush(
        {
          success: false,
          message: 'El informe sigue pendiente.',
          data: null,
          errors: { detail: 'El informe sigue pendiente.', code: 'informe_pendiente' },
          meta: {},
        },
        { status: 409, statusText: 'Conflict' },
      );
      const error = (await respuesta.catch((e: unknown) => e)) as ApiError;
      expect([error.status, error.code]).toEqual([409, 'informe_pendiente']);
    });
  });
});
