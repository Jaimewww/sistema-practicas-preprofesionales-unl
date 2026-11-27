import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { RUTAS_TUTOR_ENTIDAD } from './tutor-entidad.routes';
import { TutorEntidadMock } from './tutor-entidad.mock';

/** Utilidades de las pruebas del rol (no se importa desde la aplicación). */

/** Monta las rutas reales del rol bajo `/tutor-entidad`, con el mock sin espera. */
export async function abrir(url: string): Promise<{ harness: RouterTestingHarness; vista: HTMLElement; esperar: () => Promise<void> }> {
  TutorEntidadMock.demoraPorDefecto = 0;
  TestBed.configureTestingModule({ providers: [provideRouter([{ path: 'tutor-entidad', children: RUTAS_TUTOR_ENTIDAD }])] });
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

export const textoDe = (vista: HTMLElement): string => (vista.textContent ?? '').replace(/\s+/g, ' ');

/** Escribe en un campo como lo haría la persona (dispara `input`/`change`). */
export function escribir(el: HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement, valor: string): void {
  el.value = valor;
  el.dispatchEvent(new Event('input', { bubbles: true }));
  el.dispatchEvent(new Event('change', { bubbles: true }));
}
