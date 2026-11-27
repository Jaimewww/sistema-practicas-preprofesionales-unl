import { abrir, textoDe } from './pruebas';

const filas = (vista: HTMLElement) => [...vista.querySelectorAll('tbody tr')];

async function elegir(vista: HTMLElement, esperar: () => Promise<void>, id: string, valor: string): Promise<void> {
  const campo = vista.querySelector<HTMLSelectElement | HTMLInputElement>(`#${id}`)!;
  campo.value = valor;
  campo.dispatchEvent(new Event(campo instanceof HTMLSelectElement ? 'change' : 'input'));
  await esperar();
}

describe('Cierres de mi carrera (D1)', () => {
  it('lista los 16 cierres con su resultado, horas y enlace al detalle', async () => {
    const { vista } = await abrir('/director/cierres');
    expect(filas(vista)).toHaveLength(16);
    const texto = textoDe(vista);
    expect(texto).toContain('Prácticas cerradas');
    expect(texto).toContain('Solo lectura: aprobada o no aprobada según la evaluación final.');
    expect(texto).toContain('· 16 prácticas');
    const primera = textoDe(filas(vista)[0]);
    expect(primera).toContain('CORDOVA VAZQUEZ JOSE LUIS MAR.26-AGO.26 GRADO');
    expect(primera).toContain('Laboral Agroindustrias del Norte Cía. Ltda.');
    expect(primera).toContain('Aprobada 160 h 160 h CAÑAR MERCHÁN WASHINGTON EDUARDO');
    expect(textoDe(filas(vista)[1])).toContain('Comunitaria GAD Municipal de Catamayo · Alfabetización digital en el GAD de Catamayo No aprobada');
    expect([...vista.querySelectorAll('tbody a')].slice(0, 2).map((a) => a.getAttribute('href'))).toEqual(['/director/cierre?p=8', '/director/cierre?p=9']);
    expect(vista.querySelector('table caption')?.textContent).toContain('Prácticas cerradas de la carrera con su resultado');
  });

  it('los filtros de tipo, resultado y estudiante filtran las filas y «Limpiar» las restaura', async () => {
    const { vista, esperar } = await abrir('/director/cierres');
    await elegir(vista, esperar, 'f-tipo', 'laboral');
    expect(filas(vista)).toHaveLength(1);
    await elegir(vista, esperar, 'f-tipo', '');
    await elegir(vista, esperar, 'f-res', 'no_aprobada');
    expect(filas(vista)).toHaveLength(8);
    expect(filas(vista).every((f) => textoDe(f).includes('No aprobada'))).toBe(true);
    await elegir(vista, esperar, 'f-q', 'ayovi');
    expect(filas(vista)).toHaveLength(1);
    expect(textoDe(vista)).toContain('· 1 prácticas');
    vista.querySelector<HTMLButtonElement>('button')!.click();
    await esperar();
    expect(filas(vista)).toHaveLength(16);
  });

  it('muestra el estado vacío con un período sin cierres', async () => {
    const { vista, esperar } = await abrir('/director/cierres');
    await elegir(vista, esperar, 'f-periodo', 'SEP.25-ENE.26 GRADO');
    expect(filas(vista)).toHaveLength(0);
    const texto = textoDe(vista);
    expect(texto).toContain('No hay cierres con estos filtros');
    expect(texto).toContain('No hay prácticas cerradas para el período, tipo o resultado elegidos.');
  });

  it('cada filtro tiene su etiqueta asociada', async () => {
    const { vista } = await abrir('/director/cierres');
    for (const id of ['f-periodo', 'f-tipo', 'f-res', 'f-q']) expect(vista.querySelector(`label[for="${id}"]`), id).toBeTruthy();
  });
});
