import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { EstudianteMock } from './estudiante.mock';
import { RUTAS_ESTUDIANTE } from './estudiante.routes';

/** Utilidades de las pruebas del rol (no se importa desde la aplicación). */

/** Monta las rutas reales del rol bajo `/estudiante`, con el mock sin espera. */
export async function abrir(url: string): Promise<{ harness: RouterTestingHarness; vista: HTMLElement; esperar: () => Promise<void> }> {
  EstudianteMock.demoraPorDefecto = 0;
  TestBed.configureTestingModule({ providers: [provideRouter([{ path: 'estudiante', children: RUTAS_ESTUDIANTE }])] });
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

export type Fixture<T> = ComponentFixture<T>;
