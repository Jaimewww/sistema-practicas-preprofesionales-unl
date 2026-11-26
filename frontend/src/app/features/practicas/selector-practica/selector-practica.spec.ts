import { TestBed } from '@angular/core/testing';
import { Subject } from 'rxjs';
import { ApiError } from '../../../core/api/envelope';
import type { Practica } from '../practica.model';
import { PracticasApi } from '../practicas.api';
import { SelectorPractica } from './selector-practica';

const practicas: Practica[] = [
  {
    id: 1,
    estudiante_id: 7,
    tipo: 'practica_laboral',
    subtipo: 'empresa',
    estado: 'en_curso',
    horas_requeridas: 240,
  },
  {
    id: 409,
    estudiante_id: 7,
    tipo: 'servicio_comunitario',
    subtipo: 'proyecto',
    estado: 'cerrada',
    horas_requeridas: 160,
  },
];

describe('SelectorPractica', () => {
  let respuesta: Subject<Practica[]>;

  beforeEach(() => {
    respuesta = new Subject<Practica[]>();
    TestBed.configureTestingModule({
      imports: [SelectorPractica],
      providers: [{ provide: PracticasApi, useValue: { listar: () => respuesta.asObservable() } }],
    });
  });

  it('muestra cargando, éxito, vacío y error según la respuesta del servicio', () => {
    const fixture = TestBed.createComponent(SelectorPractica);
    const vista = fixture.nativeElement as HTMLElement;

    fixture.detectChanges();
    expect(vista.textContent).toContain('Cargando prácticas');
    expect(vista.querySelector('section.tarjeta')).not.toBeNull();

    respuesta.next(practicas);
    fixture.detectChanges();
    expect(vista.querySelectorAll('option[data-practica-id]')).toHaveLength(2);
    expect(vista.querySelector('.campo select')).not.toBeNull();

    respuesta.next([]);
    fixture.detectChanges();
    expect(vista.querySelector('.aviso-info')?.textContent).toContain('No tenés prácticas activas');
    expect(vista.querySelector('[role=alert]')).toBeNull();

    respuesta.error(new ApiError(0, 'sin_conexion', 'No se pudieron cargar las prácticas.'));
    fixture.detectChanges();
    expect(vista.querySelector('[role=alert]')?.textContent).toContain(
      'No se pudieron cargar las prácticas.',
    );
    expect(vista.querySelector('[role=alert]')?.classList.contains('aviso-error')).toBe(true);
  });

  it('emite el id de la práctica elegida', () => {
    const fixture = TestBed.createComponent(SelectorPractica);
    const seleccionados: number[] = [];
    fixture.componentInstance.seleccion.subscribe((id) => seleccionados.push(id));
    fixture.detectChanges();
    respuesta.next(practicas);
    fixture.detectChanges();

    const selector = fixture.nativeElement.querySelector('select') as HTMLSelectElement;
    selector.value = '409';
    selector.dispatchEvent(new Event('change'));

    expect(seleccionados).toEqual([409]);
  });
});
