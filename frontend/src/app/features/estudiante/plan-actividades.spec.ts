import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { EstudianteMock } from './estudiante.mock';
import { abrir, textoDe } from './pruebas';

describe('Plan de actividades (E3)', () => {
  afterEach(() => vi.restoreAllMocks());

  const descripciones = (vista: HTMLElement) => [...vista.querySelectorAll<HTMLTextAreaElement>('li.fila textarea')];
  const enviar = (vista: HTMLElement) => vista.querySelector<HTMLButtonElement>('button[type="submit"]')!.click();

  it('muestra la observación del tutor, la versión a enviar y el recorrido del plan', async () => {
    const { vista } = await abrir('/estudiante/plan');
    const texto = textoDe(vista);
    expect(texto).toContain('Plan de actividades · versión 2');
    expect(texto).toContain('Su tutor académico devolvió la versión 1.');
    expect(texto).toContain('«Detalle las herramientas y los entregables de cada actividad.»');
    expect(texto).toContain('Versión 2: usted corrige');
    expect(descripciones(vista)).toHaveLength(3);
    expect(vista.querySelector<HTMLInputElement>('input[id^="herramientas-"]')?.value).toBe('Rúbricas y hoja de cálculo de notas.');
  });

  it('cada control tiene su etiqueta enlazada con for/id', async () => {
    const { vista } = await abrir('/estudiante/plan');
    for (const control of vista.querySelectorAll('li.fila textarea, li.fila input')) {
      expect(vista.querySelector(`label[for="${control.id}"]`)).not.toBeNull();
    }
    expect(vista.querySelector('label[for^="actividad-"] .sr-only')?.textContent).toBe('Actividad 1');
  });

  it('agrega y quita actividades; la última no se puede quitar', async () => {
    const { vista, esperar } = await abrir('/estudiante/plan');
    vista.querySelector<HTMLButtonElement>('button.agregar')!.click();
    await esperar();
    expect(descripciones(vista)).toHaveLength(4);
    expect(document.activeElement).toBe(descripciones(vista)[3]);
    vista.querySelector<HTMLButtonElement>('button[aria-label="Quitar actividad 4"]')!.click();
    await esperar();
    expect(descripciones(vista)).toHaveLength(3);
    for (const n of [3, 2]) {
      vista.querySelector<HTMLButtonElement>(`button[aria-label="Quitar actividad ${n}"]`)!.click();
      await esperar();
    }
    expect(descripciones(vista)).toHaveLength(1);
    expect(vista.querySelector<HTMLButtonElement>('button[aria-label="Quitar actividad 1"]')!.disabled).toBe(true);
  });

  it('rechaza una lista sin actividades: avisa y no envía nada', async () => {
    const { vista, esperar } = await abrir('/estudiante/plan');
    const envio = vi.spyOn(EstudianteMock.prototype, 'enviarPlan');
    for (const area of descripciones(vista)) {
      area.value = '';
      area.dispatchEvent(new Event('input'));
    }
    enviar(vista);
    await esperar();
    expect(vista.querySelector('#error-plan')?.getAttribute('role')).toBe('alert');
    expect(vista.querySelector('#error-plan')?.textContent).toContain('Registre al menos una actividad.');
    expect(descripciones(vista)[0].getAttribute('aria-invalid')).toBe('true');
    expect(envio).not.toHaveBeenCalled();
    expect(TestBed.inject(Router).url).toBe('/estudiante/plan');
  });

  it('acepta una lista con una actividad, la envía y pasa a la pestaña Plan con el aviso de éxito', async () => {
    const { harness, vista, esperar } = await abrir('/estudiante/plan?p=2');
    const envio = vi.spyOn(EstudianteMock.prototype, 'enviarPlan');
    expect(descripciones(vista)).toHaveLength(1);
    expect(textoDe(vista)).toContain('Plan de actividades · versión 1');
    descripciones(vista)[0].value = 'Talleres de uso del teléfono';
    descripciones(vista)[0].dispatchEvent(new Event('input'));
    enviar(vista);
    await esperar();
    await esperar();
    expect(envio).toHaveBeenCalledWith(2, [{ descripcion: 'Talleres de uso del teléfono', herramientas: '', entregable: '' }]);
    expect(TestBed.inject(Router).url).toBe('/estudiante/practica/plan?p=2');
    const texto = textoDe(harness.fixture.nativeElement);
    expect(texto).toContain('Plan enviado a revisión.');
    expect(texto).toContain('Talleres de uso del teléfono');
    expect(texto).toContain('En revisión');
  });
});
