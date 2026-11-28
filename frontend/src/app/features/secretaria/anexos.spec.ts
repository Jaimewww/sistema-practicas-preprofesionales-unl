import { abrir, textoDe } from './pruebas';

const filas = (vista: HTMLElement) => [...vista.querySelectorAll('tbody tr')];
async function elegir(vista: HTMLElement, id: string, valor: string, esperar: () => Promise<void>) {
  const s = vista.querySelector<HTMLSelectElement>(id)!;
  s.value = valor;
  s.dispatchEvent(new Event('change'));
  await esperar();
}

describe('Anexos por legalizar (S1)', () => {
  it('muestra la lista de anexos pendientes por defecto', async () => {
    const { vista } = await abrir('/secretaria/anexos');
    const texto = textoDe(vista);
    expect(texto).toContain('Anexos de cierre');
    expect(texto).toContain('Pendiente de legalización');
    expect(filas(vista).length).toBeGreaterThan(0);
    expect(filas(vista).every((f) => textoDe(f).includes('Pendiente de legalización'))).toBe(true);
    expect(vista.querySelector('a.boton-secundario[href*="/secretaria/legalizar?a="]')).toBeTruthy();
  });

  it('los filtros por estado y tipo filtran las filas', async () => {
    const { vista, esperar } = await abrir('/secretaria/anexos');
    const pendientes = filas(vista).length;
    await elegir(vista, '#f-estado', '', esperar);
    const todos = filas(vista).length;
    expect(todos).toBeGreaterThan(pendientes);
    await elegir(vista, '#f-estado', 'legalizado', esperar);
    expect(filas(vista).length).toBeGreaterThan(0);
    expect(filas(vista).every((f) => textoDe(f).includes('TORRES REYES GLADYS ELENA · 05/06/2026'))).toBe(true);
    await elegir(vista, '#f-estado', '', esperar);
    await elegir(vista, '#f-tipo', 'comunitaria', esperar);
    expect(filas(vista).length).toBeGreaterThan(0);
    expect(filas(vista).length).toBeLessThan(todos);
    expect(filas(vista).every((f) => textoDe(f).includes('Comunitaria ·'))).toBe(true);
  });

  it('muestra el estado vacío al simular la bandeja vacía y «Limpiar» lo quita', async () => {
    const { vista, esperar } = await abrir('/secretaria/anexos');
    const botones = [...vista.querySelectorAll<HTMLButtonElement>('button')];
    botones.find((b) => b.textContent?.includes('Simular bandeja vacía'))!.click();
    await esperar();
    expect(filas(vista)).toHaveLength(0);
    expect(textoDe(vista)).toContain('No hay anexos pendientes de legalización');
    botones.find((b) => b.textContent?.includes('Limpiar'))!.click();
    await esperar();
    expect(filas(vista).length).toBeGreaterThan(0);
  });
});
