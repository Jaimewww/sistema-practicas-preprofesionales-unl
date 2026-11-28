import { abrir, textoDe } from './pruebas';
import { SecretariaApi } from './secretaria.api';
import type { RouterTestingHarness } from '@angular/router/testing';
import { firstValueFrom } from 'rxjs';

const boton = (vista: HTMLElement) => [...vista.querySelectorAll<HTMLButtonElement>('button')].find((b) => b.textContent?.includes('Marcar como legalizado'));

/** El servicio vive en los providers de la ruta: se toma del componente montado. */
const apiDe = (h: RouterTestingHarness): SecretariaApi => h.routeDebugElement!.injector.get(SecretariaApi);

async function idsPor(h: RouterTestingHarness, estado: 'pendiente' | 'legalizado'): Promise<number[]> {
  const filas = await firstValueFrom(apiDe(h).anexos());
  return filas.filter((f) => f.anexo.estado === estado).map((f) => f.anexo.id);
}

describe('Legalizar anexo (S2)', () => {
  it('un anexo pendiente ofrece «Marcar como legalizado»', async () => {
    const { vista } = await abrir('/secretaria/legalizar?a=802');
    const texto = textoDe(vista);
    expect(texto).toContain('Pendiente de legalización');
    expect(texto).toContain('trazabilidad RF-20');
    expect(boton(vista)).toBeTruthy();
    expect(texto).not.toContain('Legalizado por');
  });

  it('un anexo ya legalizado muestra autor y fecha, sin botón, y avisa que no se puede modificar', async () => {
    const { vista } = await abrir('/secretaria/legalizar?a=801');
    const texto = textoDe(vista);
    expect(texto).toContain('Legalizado por TORRES REYES GLADYS ELENA el 05/06/2026');
    expect(texto).toContain('No se puede modificar (RF-20)');
    expect(texto).toContain('El estado de la práctica no cambió: sigue «Cerrada (aprobada)».');
    expect(boton(vista)).toBeUndefined();
  });

  it('legalizar un anexo pendiente registra autor y fecha, oculta el botón y se ve legalizado en S1', async () => {
    const { harness, vista, esperar } = await abrir('/secretaria/legalizar?a=802');
    boton(vista)!.click();
    await esperar();
    const texto = textoDe(vista);
    expect(texto).toContain('Anexo legalizado. Quedó registrado quién y cuándo');
    expect(texto).toContain('Legalizado por TORRES REYES GLADYS ELENA el 05/06/2026');
    expect(boton(vista)).toBeUndefined();

    const s1 = await abrir('/secretaria/anexos', harness);
    const select = s1.vista.querySelector<HTMLSelectElement>('#f-estado')!;
    select.value = 'legalizado';
    select.dispatchEvent(new Event('change'));
    await s1.esperar();
    const filas = [...s1.vista.querySelectorAll('tbody tr')].map((f) => textoDe(f));
    expect(filas.some((f) => f.includes('informe-externo-cerrada-8.pdf') && f.includes('TORRES REYES GLADYS ELENA · 05/06/2026'))).toBe(true);
  });

  it('legalizar dos veces se rechaza y deja el registro intacto', async () => {
    const { harness, vista, esperar } = await abrir('/secretaria/legalizar?a=802');
    boton(vista)!.click();
    await esperar();
    const api = apiDe(harness);
    await expect(firstValueFrom(api.legalizar(802))).rejects.toMatchObject({ status: 409 });
    const fila = await firstValueFrom(api.anexo(802));
    expect(fila.anexo.legalizadoPor).toBe('TORRES REYES GLADYS ELENA');
    expect(fila.anexo.legalizadoEl).toBe('2026-06-05');
  });

  it('legalizar un anexo que no existe falla con 404', async () => {
    const { harness } = await abrir('/secretaria/legalizar?a=802');
    await expect(firstValueFrom(apiDe(harness).legalizar(999999))).rejects.toMatchObject({ status: 404 });
  });

  it('el mock no repite ids de anexo y hay pendientes y legalizados', async () => {
    const { harness } = await abrir('/secretaria/legalizar?a=802');
    const todos = [...(await idsPor(harness, 'pendiente')), ...(await idsPor(harness, 'legalizado'))];
    expect(new Set(todos).size).toBe(todos.length);
    expect((await idsPor(harness, 'legalizado')).length).toBeGreaterThan(0);
  });
});
