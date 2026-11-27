import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { CoordinadorMock } from './coordinador.mock';
import { RUTAS_COORDINADOR } from './coordinador.routes';

/** Utilidades de las pruebas del rol (no se importa desde la aplicación). */

/** Monta las rutas reales del rol bajo `/coordinador`, con el mock sin espera. */
export async function abrir(url: string): Promise<{ harness: RouterTestingHarness; vista: HTMLElement; esperar: () => Promise<void> }> {
  CoordinadorMock.demoraPorDefecto = 0;
  TestBed.configureTestingModule({ providers: [provideRouter([{ path: 'coordinador', children: RUTAS_COORDINADOR }])] });
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

/**
 * Texto visible con un espacio entre elementos vecinos: `textContent` pega los textos de
 * elementos adyacentes sin separarlos y rompería las aserciones.
 */
export function textoDe(nodo: Node): string {
  const partes: string[] = [];
  const recorrer = (n: Node) => {
    if (n.nodeType === Node.TEXT_NODE) partes.push(n.textContent ?? '');
    else n.childNodes.forEach(recorrer);
    if (n.nodeType === Node.ELEMENT_NODE) partes.push(' ');
  };
  recorrer(nodo);
  return partes.join('').replace(/\s+/g, ' ').trim();
}
