import { abrir, textoDe } from './pruebas';

function elegir(vista: HTMLElement, id: string, valor: string): void {
  const s = vista.querySelector<HTMLSelectElement>('#' + id)!;
  s.value = valor;
  s.dispatchEvent(new Event('change'));
}
const filas = (vista: HTMLElement) => vista.querySelectorAll('tbody tr').length;

describe('Prácticas de la carrera (C1)', () => {
  it('muestra la tabla con las columnas de RF-06 y las 150 prácticas', async () => {
    const { vista } = await abrir('/coordinador/practicas');
    const cabeceras = [...vista.querySelectorAll('th')].map((t) => t.textContent?.trim());
    expect(cabeceras).toEqual(['Estudiante', 'Tipo', 'Estado', 'Horas validadas / en revisión / requeridas', 'Alertas', 'Tutor académico']);
    expect(filas(vista)).toBe(150);
    expect(textoDe(vista)).toContain('Se muestran 150 de las 150 prácticas de la carrera.');
    expect(textoDe(vista)).toContain('42 / 8 / 160 h');
  });

  it('los filtros filtran filas de verdad y el contador acompaña', async () => {
    const { vista, esperar } = await abrir('/coordinador/practicas');
    elegir(vista, 'f-estado', 'cerrada');
    await esperar();
    const cerradas = filas(vista);
    expect(cerradas).toBeGreaterThan(0);
    expect(cerradas).toBeLessThan(150);
    expect(textoDe(vista)).toContain(`Se muestran ${cerradas} de las 150`);
    elegir(vista, 'f-tipo', 'comunitaria');
    await esperar();
    expect(filas(vista)).toBeLessThan(cerradas);
    for (const c of vista.querySelectorAll('tbody tr td:nth-child(2)')) expect(c.textContent).toContain('Comunitaria');
  });

  it('el filtro de alerta deja solo las prácticas con esa alerta y marca las rezagadas', async () => {
    const { vista, esperar } = await abrir('/coordinador/practicas');
    elegir(vista, 'f-alerta', 'rezago');
    await esperar();
    const n = filas(vista);
    expect(n).toBeGreaterThan(0);
    expect(vista.querySelectorAll('tbody tr.fila-alerta')).toHaveLength(n);
    for (const c of vista.querySelectorAll('tbody tr td:nth-child(5)')) expect(c.textContent).toContain('Horas rezagadas');
  });

  it('sin coincidencias muestra el estado vacío y «Limpiar filtros» lo quita', async () => {
    const { vista, esperar } = await abrir('/coordinador/practicas');
    elegir(vista, 'f-estado', 'cerrada');
    elegir(vista, 'f-alerta', 'rezago');
    await esperar();
    expect(filas(vista)).toBe(0);
    expect(textoDe(vista)).toContain('Sin prácticas para estos filtros');
    vista.querySelector<HTMLButtonElement>('form button')!.click();
    await esperar();
    expect(filas(vista)).toBe(150);
  });

  it('?estado= del tablero llega como filtro inicial', async () => {
    const { vista } = await abrir('/coordinador/practicas?estado=suspendida');
    expect(vista.querySelector<HTMLSelectElement>('#f-estado')!.value).toBe('suspendida');
    for (const c of vista.querySelectorAll('tbody tr td:nth-child(3)')) expect(c.textContent).toContain('Suspendida');
  });
});
