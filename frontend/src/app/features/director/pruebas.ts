import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { DirectorMock } from './director.mock';
import { RUTAS_DIRECTOR } from './director.routes';

/** Utilidades de las pruebas del rol (no se importa desde la aplicación). */

/** Monta las rutas reales del rol bajo `/director`, con el mock sin espera. */
export async function abrir(url: string): Promise<{ harness: RouterTestingHarness; vista: HTMLElement; esperar: () => Promise<void> }> {
  DirectorMock.demoraPorDefecto = 0;
  TestBed.configureTestingModule({ providers: [provideRouter([{ path: 'director', children: RUTAS_DIRECTOR }])] });
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

/** Texto visible con un espacio entre elementos contiguos (`textContent` los pega). */
export function textoDe(vista: Element): string {
  const partes: string[] = [];
  const recorrer = (n: Node): void => {
    if (n.nodeType === Node.TEXT_NODE) partes.push(n.textContent ?? '');
    else {
      partes.push(' ');
      n.childNodes.forEach(recorrer);
      partes.push(' ');
    }
  };
  recorrer(vista);
  return partes.join('').replace(/\s+/g, ' ');
}

export type Fixture<T> = ComponentFixture<T>;
