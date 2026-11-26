import { abrir, textoDe } from './pruebas';

describe('Mi práctica: marco y pestañas', () => {
  it('muestra «Datos de la práctica» y las cuatro pestañas con la actual marcada', async () => {
    const { vista } = await abrir('/estudiante/practica');
    const texto = textoDe(vista);
    expect(texto).toContain('Datos de la práctica');
    expect(texto).toContain('Computación · Presencial · Ciclo 4A');
    expect(texto).toContain('Periodo académico');
    expect(texto).toContain('Tutor académico');
    const pestanas = [...vista.querySelectorAll('ul.pestanas a')];
    expect(pestanas.map((a) => a.textContent?.trim())).toEqual(['Resumen', 'Plan', 'Reportes semanales', 'Informe final']);
    expect(pestanas.filter((a) => a.getAttribute('aria-current') === 'page').map((a) => a.textContent?.trim())).toEqual(['Resumen']);
  });

  it('con ?p=2 muestra la práctica comunitaria y conserva el parámetro en las pestañas', async () => {
    const { vista } = await abrir('/estudiante/practica?p=2');
    expect(textoDe(vista)).toContain('Comunitaria');
    expect(textoDe(vista)).toContain('No aplica en servicio comunitario');
    expect(vista.querySelector('ul.pestanas a[href="/estudiante/practica/plan?p=2"]')).not.toBeNull();
  });

  it('una práctica que no existe muestra el error del servicio', async () => {
    const { vista } = await abrir('/estudiante/practica?p=99');
    expect(vista.querySelector('app-estado-pantalla app-aviso[role="alert"]')?.textContent).toContain('No encontrado.');
  });
});

describe('Resumen (E2)', () => {
  it('muestra el avance frente a lo esperado, las 16 semanas y lo pendiente', async () => {
    const { vista } = await abrir('/estudiante/practica');
    const texto = textoDe(vista);
    expect(texto).toContain('A la semana 9 de 16 debería llevar 90 h validadas y lleva 42 h (47 % de lo esperado). Cuenta con 8 h en revisión.');
    expect(texto).toContain('Le faltan 118 h para completar las 160 requeridas.');
    expect(vista.querySelectorAll('ol.semanas li')).toHaveLength(16);
    expect(texto).toContain('Devuelto con observación');
    expect(texto).toContain('Falta detallar qué talleres calificó.');
    expect(texto).toContain('8 h esperando la validación de su tutor académico.');
  });

  it('enlaza «Corregir reporte» a E5 y «Reportar semana 9» a E4', async () => {
    const { vista } = await abrir('/estudiante/practica');
    expect(vista.querySelector('a[href="/estudiante/reporte?s=5"]')?.textContent).toContain('Corregir reporte');
    expect([...vista.querySelectorAll('a[href="/estudiante/reportes/nuevo"]')].map((a) => a.textContent?.trim())).toEqual(['Reportar semana 9', 'Nuevo reporte semanal']);
  });
});

describe('Plan (pestaña)', () => {
  it('muestra el plan vigente en solo lectura con herramientas, entregables e historial de versiones', async () => {
    const { vista } = await abrir('/estudiante/practica/plan');
    const texto = textoDe(vista);
    expect(texto).toContain('Plan de actividades · versión 2');
    expect(texto).toContain('Aprobado');
    expect(texto).toContain('Apoyo en la calificación de talleres de Programación.');
    expect(texto).toContain('Rúbricas y hoja de cálculo de notas.');
    expect(vista.querySelectorAll('ol.actividades li')).toHaveLength(3);
    expect([...vista.querySelectorAll('app-pasos strong')].map((s) => s.textContent?.replace(/\s+/g, ' ').trim())).toEqual([
      'Versión 1 · devuelta (Con observación)',
      'Versión 2 · aprobada (Completado)',
    ]);
    expect(texto).toContain('«Detalle las herramientas y los entregables de cada actividad.»');
  });
});

describe('Reportes semanales (pestaña)', () => {
  const filas = (vista: HTMLElement) => [...vista.querySelectorAll('tbody tr')].map((tr) => tr.querySelector('td')?.textContent?.trim());
  async function filtrar(vista: HTMLElement, esperar: () => Promise<void>, valor: string) {
    const select = vista.querySelector<HTMLSelectElement>('#filtro-estado')!;
    select.value = valor;
    select.dispatchEvent(new Event('change'));
    await esperar();
  }

  it('lista las 9 semanas y los contadores de enviados, validados, devueltos y en revisión', async () => {
    const { vista } = await abrir('/estudiante/practica/reportes');
    expect(filas(vista)).toHaveLength(9);
    expect([...vista.querySelectorAll('app-kpi')].map((k) => k.querySelector('strong')?.textContent)).toEqual(['8', '6', '1', '1']);
    expect(textoDe(vista)).toContain('Semanas 10 a 16: aún no inician.');
  });

  it('el filtro por estado filtra las filas de verdad', async () => {
    const { vista, esperar } = await abrir('/estudiante/practica/reportes');
    await filtrar(vista, esperar, 'devuelto');
    expect(filas(vista)).toEqual(['Semana 5']);
    await filtrar(vista, esperar, 'validado');
    expect(filas(vista)).toHaveLength(6);
    await filtrar(vista, esperar, 'sin_reporte');
    expect(filas(vista)).toEqual(['Semana 9']);
    await filtrar(vista, esperar, '');
    expect(filas(vista)).toHaveLength(9);
  });

  it('los enlaces «Corregir», «Ver» y «Reportar» van a E5 y E4', async () => {
    const { vista } = await abrir('/estudiante/practica/reportes');
    const enlace = (semana: number) => vista.querySelector(`tbody tr:nth-child(${semana}) a`);
    expect([enlace(5)?.textContent, enlace(5)?.getAttribute('href')]).toEqual(['Corregir', '/estudiante/reporte?s=5']);
    expect([enlace(1)?.textContent, enlace(1)?.getAttribute('href')]).toEqual(['Ver', '/estudiante/reporte?s=1']);
    expect([enlace(9)?.textContent, enlace(9)?.getAttribute('href')]).toEqual(['Reportar', '/estudiante/reportes/nuevo']);
  });
});
