import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import type { Type } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { of } from 'rxjs';
import { environment } from '../../../environments/environment';
import { apiErrorInterceptor } from '../../core/api/api-error.interceptor';
import { authInterceptor } from '../../core/auth/auth.interceptor';
import { PracticasApi } from '../practicas/practicas.api';
import type { Practica } from '../practicas/practica.model';
import { PlanActividadesReal } from './plan-actividades-real';
import type { PlanVersion } from './plan-informe.http';
import { PlanInformeHttp } from './plan-informe.http';

/**
 * Pantallas reales del plan (C-09) y del informe final (C-10): hablan con
 * `PlanInformeHttp` y solo pintan lo que devuelve el API. No hay `?p=` ni
 * prácticas de demostración: sin parámetro se elige entre las prácticas visibles.
 */
describe('Pantallas reales de plan e informe final', () => {
  let http: HttpTestingController;

  const envelope = <T>(data: T) => ({ success: true, message: '', data, errors: null, meta: {} });
  const error = (status: number, code: string, detail: string) => ({
    success: false,
    message: detail,
    data: null,
    errors: { detail, code },
    meta: {},
  });
  const planUrl = (id = 7) => `${environment.apiBaseUrl}/practicas/${id}/plan/`;

  const practicas: Practica[] = [
    {
      id: 7,
      estudiante_id: 3,
      tipo: 'practica_laboral',
      subtipo: 'empresa',
      estado: 'en_curso',
      horas_requeridas: 160,
    },
    {
      id: 9,
      estudiante_id: 3,
      tipo: 'servicio_comunitario',
      subtipo: 'proyecto',
      estado: 'asignada',
      horas_requeridas: 120,
    },
  ];

  const version = (datos: Partial<PlanVersion> = {}): PlanVersion => ({
    id: 11,
    practica_id: 7,
    version: 1,
    contenido: 'Acompañar el taller de programación.\nRegistrar la asistencia.',
    estado: 'devuelto',
    observacion: 'Detalle los entregables.',
    fecha_validacion: '2026-11-20T10:00:00Z',
    ...datos,
  });

  async function abrir<T>(componente: Type<T>, url = '/prueba?p=7') {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([{ path: 'prueba', component: componente }]),
        provideHttpClient(withInterceptors([authInterceptor, apiErrorInterceptor])),
        provideHttpClientTesting(),
        PlanInformeHttp,
        { provide: PracticasApi, useValue: { listar: () => of(practicas) } },
      ],
    });
    const harness = await RouterTestingHarness.create();
    await harness.navigateByUrl(url);
    harness.detectChanges();
    http = TestBed.inject(HttpTestingController);
    return { harness, vista: harness.fixture.nativeElement as HTMLElement };
  }

  function escribir(vista: HTMLElement, texto: string): void {
    const area = vista.querySelector<HTMLTextAreaElement>('#plan-contenido')!;
    area.value = texto;
    area.dispatchEvent(new Event('input'));
  }

  afterEach(() => {
    if (http) http.verify();
  });

  describe('editor del plan (C-09)', () => {
    it('la etiqueta controla el campo aunque el layout tenga un elemento #contenido', async () => {
      const main = document.createElement('main');
      main.id = 'contenido';
      document.body.prepend(main);
      try {
        const { vista, harness } = await abrir(PlanActividadesReal);
        http.expectOne(planUrl()).flush(envelope([]));
        harness.detectChanges();
        const campo = vista.querySelector('textarea');
        const etiqueta = vista.querySelector<HTMLLabelElement>('label[for]:has(.req)');
        expect(campo).not.toBeNull();
        expect(etiqueta?.control).toBe(campo);
      } finally {
        main.remove();
      }
    });

    it('sin ?p= pide elegir una práctica visible y no inventa un id de demostración', async () => {
      const { vista, harness } = await abrir(PlanActividadesReal, '/prueba');
      expect(vista.querySelector('#selector-practica')).not.toBeNull();
      expect(vista.textContent).toContain('Elegí la práctica');
      http.expectNone(planUrl());

      const selector = vista.querySelector<HTMLSelectElement>('#selector-practica')!;
      selector.value = '9';
      selector.dispatchEvent(new Event('change'));
      await harness.fixture.whenStable();
      expect(TestBed.inject(Router).url).toContain('p=9');
      const peticion = http.expectOne(planUrl(9));
      expect(peticion.request.method).toBe('GET');
      peticion.flush(envelope([]));
    });

    it('carga las versiones y muestra la última, su estado y las anteriores', async () => {
      const { vista, harness } = await abrir(PlanActividadesReal);
      expect(vista.querySelector('[role="status"]')?.textContent).toContain('Cargando');
      http
        .expectOne(planUrl())
        .flush(
          envelope([
            version({
              id: 12,
              version: 2,
              estado: 'en_revision',
              observacion: null,
              fecha_validacion: null,
            }),
            version(),
          ]),
        );
      harness.detectChanges();
      const texto = vista.textContent ?? '';
      expect(texto).toContain('versión 2');
      expect(texto).toContain('En revisión');
      expect(texto).toContain('Versión 1');
      expect(texto).toContain('Detalle los entregables.');
      expect(vista.querySelector('#plan-contenido')).toBeNull();
    });

    it('tras una devolución precarga el contenido y envía solo {contenido} mostrando «Enviando…»', async () => {
      const { vista, harness } = await abrir(PlanActividadesReal);
      http.expectOne(planUrl()).flush(envelope([version()]));
      harness.detectChanges();

      const area = vista.querySelector<HTMLTextAreaElement>('#plan-contenido')!;
      expect(area.value).toBe(version().contenido);
      escribir(vista, 'Actividad corregida.');
      const boton = vista.querySelector<HTMLButtonElement>('button[type="submit"]')!;
      boton.click();
      harness.detectChanges();
      expect(boton.disabled).toBe(true);
      expect(boton.textContent).toContain('Enviando…');

      const peticion = http.expectOne(planUrl());
      expect(peticion.request.method).toBe('POST');
      expect(peticion.request.body).toEqual({ contenido: 'Actividad corregida.' });
      peticion.flush(
        envelope(
          version({
            id: 13,
            version: 3,
            estado: 'en_revision',
            observacion: null,
            fecha_validacion: null,
          }),
        ),
        { status: 201, statusText: 'Created' },
      );
      harness.detectChanges();
      expect(vista.textContent).toContain('Plan enviado');
      expect(vista.textContent).toContain('En revisión');
      expect(vista.querySelector('#plan-contenido')).toBeNull();
    });

    it('no llama al API con el contenido vacío y explica qué falta', async () => {
      const { vista, harness } = await abrir(PlanActividadesReal);
      http.expectOne(planUrl()).flush(envelope([version()]));
      harness.detectChanges();
      escribir(vista, '   ');
      vista.querySelector<HTMLButtonElement>('button[type="submit"]')!.click();
      harness.detectChanges();
      expect(vista.querySelector('.resumen-error')?.textContent).toContain(
        'Escriba las actividades del plan.',
      );
      http.expectNone(planUrl());
    });

    it('muestra el mensaje del backend cuando la versión no se puede reenviar', async () => {
      const { vista, harness } = await abrir(PlanActividadesReal);
      http.expectOne(planUrl()).flush(envelope([version()]));
      harness.detectChanges();
      escribir(vista, 'Actividad corregida.');
      vista.querySelector<HTMLButtonElement>('button[type="submit"]')!.click();
      harness.detectChanges();
      http
        .expectOne(planUrl())
        .flush(error(409, 'plan_no_reenviable', 'La última versión está en revisión.'), {
          status: 409,
          statusText: 'Conflict',
        });
      harness.detectChanges();
      expect(vista.querySelector('app-aviso[role="alert"]')?.textContent).toContain(
        'La última versión está en revisión.',
      );
      expect(vista.querySelector('#plan-contenido')).not.toBeNull();
    });
  });
});
