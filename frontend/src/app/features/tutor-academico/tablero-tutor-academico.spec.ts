import { abrir, textoDe } from './pruebas';

describe('Tablero del tutor académico', () => {
  it('muestra los indicadores con las cifras de la demostración', async () => {
    const { vista } = await abrir('/tutor-academico');
    const kpis = [...vista.querySelectorAll('app-kpi')].map((k) => textoDe(k as HTMLElement).trim());
    expect(kpis).toEqual([
      'Pendientes de revisión 5 Planes, reportes e informes',
      'Fuera de plazo 1 Más de 5 días hábiles',
      'Tutorados 5 MAR.26-AGO.26 GRADO',
      'Horas rezagadas 2 Luciana y Diego',
    ]);
  });

  it('lista primero lo más antiguo, con la marca de fuera de plazo', async () => {
    const { vista } = await abrir('/tutor-academico');
    const texto = textoDe(vista);
    expect(texto).toContain('Lo más antiguo primero: el reporte de Diego (semana 7) ya venció.');
    const lineas = [...vista.querySelectorAll('app-tarjeta:nth-of-type(2) .lista-lineas li strong')].map((s) => s.textContent);
    expect(lineas).toEqual(['Reporte semanal · Semana 7 · 8 h', 'Plan de actividades', 'Reporte semanal · Semana 8 · 8 h', 'Reporte semanal · Semana 8 · 10 h']);
    expect(texto).toContain('JIMÉNEZ CASTILLO DIEGO ALEJANDRO · enviado 25/05/2026 · 9 días hábiles');
    expect(texto).toContain('Fuera de plazo');
    expect(texto).toContain('Ver los 5 pendientes');
  });

  it('señala a los tutorados que necesitan atención y ofrece las acciones rápidas', async () => {
    const { vista } = await abrir('/tutor-academico');
    const texto = textoDe(vista);
    expect(texto).toContain('42 h validadas + 8 en revisión; mínimo 72 h');
    expect(texto).toContain('48 h validadas + 18 en revisión; mínimo 72 h');
    expect(texto).toContain('Listo para la evaluación final');
    expect(vista.querySelector('a[href="/tutor-academico/pendientes"]')?.textContent).toContain('Revisar pendientes');
    expect(vista.querySelector('a[href="/tutor-academico/tutorados"]')?.textContent).toContain('Mis tutorados');
    expect(vista.querySelector('a[href="/tutor-academico/evaluacion?p=5"]')?.textContent).toContain('Evaluar a Mateo Torres');
  });
});
