import { abrir, escribir, textoDe } from './pruebas';

describe('Reportes por confirmar (R2)', () => {
  const filas = (vista: HTMLElement) => [...vista.querySelectorAll('tbody tr')].map((tr) => tr.querySelector('td')!.textContent!.trim() + ' ' + tr.querySelectorAll('td')[1].textContent!.trim().slice(0, 8));

  it('lista los tres reportes pendientes con su revisión académica y el enlace para confirmarlos', async () => {
    const { vista } = await abrir('/tutor-entidad/reportes-por-confirmar');
    expect(filas(vista)).toEqual(['MENDIETA SARANGO LUCIANA BELÉN Semana 7', 'JIMÉNEZ CASTILLO DIEGO ALEJANDRO Semana 7', 'MENDIETA SARANGO LUCIANA BELÉN Semana 8']);
    const texto = textoDe(vista);
    expect(texto).toContain('18/05/2026 - 24/05/2026');
    expect(texto).toContain('3 de 3 reportes mostrados.');
    expect(texto).toContain('Pendiente de confirmación');
    expect([...vista.querySelectorAll('tbody a')].map((a) => a.getAttribute('href'))).toEqual([
      '/tutor-entidad/confirmar-reporte?r=l7',
      '/tutor-entidad/confirmar-reporte?r=d7',
      '/tutor-entidad/confirmar-reporte?r=l8',
    ]);
  });

  it('el filtro por practicante filtra de verdad', async () => {
    const { vista, esperar } = await abrir('/tutor-entidad/reportes-por-confirmar');
    escribir(vista.querySelector<HTMLSelectElement>('#f-est')!, '3');
    await esperar();
    expect(vista.querySelectorAll('tbody tr')).toHaveLength(1);
    expect(textoDe(vista)).toContain('1 de 3 reportes mostrados.');
  });

  it('el filtro por revisión académica filtra de verdad y puede dejar la lista sin resultados', async () => {
    const { vista, esperar } = await abrir('/tutor-entidad/reportes-por-confirmar');
    escribir(vista.querySelector<HTMLSelectElement>('#f-rev')!, 'validado');
    await esperar();
    expect(vista.querySelectorAll('tbody tr')).toHaveLength(1);
    escribir(vista.querySelector<HTMLSelectElement>('#f-est')!, '3');
    await esperar();
    expect(vista.querySelectorAll('tbody tr')).toHaveLength(0);
    expect(textoDe(vista)).toContain('Ningún reporte coincide con el filtro');
  });

  it('el botón alterna el estado «sin reportes por confirmar»', async () => {
    const { vista, esperar } = await abrir('/tutor-entidad/reportes-por-confirmar');
    vista.querySelector<HTMLButtonElement>('button')!.click();
    await esperar();
    expect(textoDe(vista)).toContain('Todos los reportes de sus practicantes ya están confirmados.');
    expect(vista.querySelector('table')).toBeNull();
  });
});
