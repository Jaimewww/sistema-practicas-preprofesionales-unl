import { escribir, filas, abrir, pulsar, textoDe } from './pruebas';

describe('Pendientes de revisión (T1)', () => {
  it('lista los cinco pendientes del más antiguo al más nuevo, con los días hábiles de espera', async () => {
    const { vista } = await abrir('/tutor-academico/pendientes');
    const texto = textoDe(vista);
    expect(texto).toContain('1 pendiente fuera de plazo: el reporte de la semana 7 de Diego Jiménez lleva 9 días hábiles esperando (plazo: 5).');
    expect(filas(vista).map((f) => f.cells[2].textContent)).toEqual(['25/05/2026', '29/05/2026', '01/06/2026', '01/06/2026', '02/06/2026']);
    expect(filas(vista).map((f) => textoDe(f.cells[3]).trim())).toEqual(['9 Fuera de plazo', '5', '4', '4', '3']);
    expect(texto).toContain('5 de 5 pendientes mostrados.');
  });

  it('cada fila lleva a la pantalla de revisión de su tipo', async () => {
    const { vista } = await abrir('/tutor-academico/pendientes');
    const enlaces = [...vista.querySelectorAll('tbody a')].map((a) => a.getAttribute('href'));
    expect(enlaces).toEqual([
      '/tutor-academico/revisar/reporte?r=d7',
      '/tutor-academico/revisar/plan?r=a4',
      '/tutor-academico/revisar/reporte?r=l8',
      '/tutor-academico/revisar/reporte?r=d8',
      '/tutor-academico/revisar/informe?r=v6',
    ]);
  });

  it('el filtro por tipo filtra las filas de verdad y actualiza el contador', async () => {
    const { vista, esperar } = await abrir('/tutor-academico/pendientes');
    escribir(vista, '#f-tipo', 'reporte');
    await esperar();
    expect(filas(vista)).toHaveLength(3);
    expect(filas(vista).every((f) => f.cells[0].textContent?.includes('Reporte semanal'))).toBe(true);
    expect(textoDe(vista)).toContain('3 de 5 pendientes mostrados.');
  });

  it('el filtro de plazo y el de estudiante se combinan', async () => {
    const { vista, esperar } = await abrir('/tutor-academico/pendientes');
    escribir(vista, '#f-plazo', 'fuera');
    await esperar();
    expect(filas(vista)).toHaveLength(1);
    expect(filas(vista)[0].textContent).toContain('JIMÉNEZ CASTILLO DIEGO ALEJANDRO');
    escribir(vista, '#f-plazo', 'plazo');
    escribir(vista, '#f-est', '3');
    await esperar();
    expect(filas(vista)).toHaveLength(1);
    expect(filas(vista)[0].cells[0].textContent).toContain('Semana 8 · 10 h');
  });

  it('si ningún pendiente coincide lo dice y sugiere otro filtro', async () => {
    const { vista, esperar } = await abrir('/tutor-academico/pendientes');
    escribir(vista, '#f-tipo', 'informe');
    escribir(vista, '#f-est', '1');
    await esperar();
    expect(filas(vista)).toHaveLength(0);
    expect(textoDe(vista)).toContain('Ningún pendiente coincide con el filtro Pruebe con otro tipo, plazo o estudiante.');
    expect(textoDe(vista)).toContain('0 de 5 pendientes mostrados.');
  });

  it('la variante «sin pendientes» se alterna con el botón y se abre con ?vacio=1', async () => {
    const { vista, esperar } = await abrir('/tutor-academico/pendientes');
    pulsar(vista, 'Ver sin pendientes');
    await esperar();
    expect(textoDe(vista)).toContain('Sin pendientes de revisión No tiene planes, reportes ni informes por revisar.');
    expect(vista.querySelector('table')).toBeNull();
    pulsar(vista, 'Volver a la lista');
    await esperar();
    expect(filas(vista)).toHaveLength(5);
  });

  it('abre directo en la variante vacía con ?vacio=1', async () => {
    const { vista } = await abrir('/tutor-academico/pendientes?vacio=1');
    expect(textoDe(vista)).toContain('Sin pendientes de revisión');
    expect([...vista.querySelectorAll('button')].map((b) => b.textContent?.trim())).toContain('Volver a la lista');
  });
});
