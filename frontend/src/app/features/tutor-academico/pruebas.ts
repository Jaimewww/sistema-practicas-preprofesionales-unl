import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { RUTAS_TUTOR_ACADEMICO } from './tutor-academico.routes';
import { TutorAcademicoMock } from './tutor-academico.mock';

/** Utilidades de las pruebas del rol (no se importa desde la aplicación). */

/** Monta las rutas reales del rol bajo `/tutor-academico`, con el mock sin espera. */
export async function abrir(url: string): Promise<{ harness: RouterTestingHarness; vista: HTMLElement; esperar: () => Promise<void> }> {
  TutorAcademicoMock.demoraPorDefecto = 0;
  TestBed.resetTestingModule(); // permite abrir más de una pantalla en la misma prueba
  TestBed.configureTestingModule({ providers: [provideRouter([{ path: 'tutor-academico', children: RUTAS_TUTOR_ACADEMICO }])] });
  const harness = await RouterTestingHarness.create();
  await harness.navigateByUrl(url);
  const esperar = async () => {
    await new Promise((r) => setTimeout(r, 0)); // deja salir la respuesta del mock (timer)
    await harness.fixture.whenStable();
    harness.detectChanges();
  };
  await esperar();
  return { harness, vista: harness.fixture.nativeElement as HTMLElement, esperar };
}

/** Texto visible normalizado: separa con un espacio el contenido de elementos contiguos (como lo lee la persona). */
export const textoDe = (vista: HTMLElement): string => {
  const partes: string[] = [];
  const recorrer = (nodo: Node): void => {
    if (nodo.nodeType === Node.TEXT_NODE) partes.push(nodo.textContent ?? '');
    else if (nodo.nodeType === Node.ELEMENT_NODE) {
      partes.push(' ');
      nodo.childNodes.forEach(recorrer);
      partes.push(' ');
    }
  };
  recorrer(vista);
  return partes.join('').replace(/\s+/g, ' ').replace(/ ([.,;:)])/g, '$1');
};

/** Escribe en un campo o elige en un `<select>` como lo haría la persona. */
export function escribir(vista: HTMLElement, selector: string, valor: string): void {
  const campo = vista.querySelector<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>(selector);
  if (!campo) throw new Error(`No existe ${selector}`);
  campo.value = valor;
  campo.dispatchEvent(new Event('input', { bubbles: true }));
  campo.dispatchEvent(new Event('change', { bubbles: true }));
}

/** Pulsa el botón que tiene exactamente ese texto. */
export function pulsar(vista: HTMLElement, texto: string): void {
  const boton = [...vista.querySelectorAll<HTMLButtonElement>('button')].find((b) => b.textContent?.trim() === texto);
  if (!boton) throw new Error(`No existe el botón «${texto}»`);
  boton.click();
}

export const filas = (vista: HTMLElement): HTMLTableRowElement[] => [...vista.querySelectorAll<HTMLTableRowElement>('tbody tr')];

export type Fixture<T> = ComponentFixture<T>;
