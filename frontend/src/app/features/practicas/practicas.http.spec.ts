import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../../environments/environment';
import type { Practica } from './practica.model';
import { PracticasHttp } from './practicas.http';

describe('PracticasHttp', () => {
  let servicio: PracticasHttp;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [PracticasHttp, provideHttpClient(), provideHttpClientTesting()],
    });
    servicio = TestBed.inject(PracticasHttp);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('lista las prácticas con GET /practicas/ y desenvuelve data', () => {
    const practicas: Practica[] = [
      {
        id: 1,
        estudiante_id: 7,
        tipo: 'practica_laboral',
        subtipo: 'empresa',
        estado: 'en_curso',
        horas_requeridas: 240,
      },
    ];
    let resultado: Practica[] | undefined;

    servicio.listar().subscribe((datos) => (resultado = datos));

    const solicitud = http.expectOne(`${environment.apiBaseUrl}/practicas/`);
    expect(solicitud.request.method).toBe('GET');
    solicitud.flush({ success: true, message: '', data: practicas, errors: null, meta: {} });

    expect(resultado).toEqual(practicas);
  });
});
