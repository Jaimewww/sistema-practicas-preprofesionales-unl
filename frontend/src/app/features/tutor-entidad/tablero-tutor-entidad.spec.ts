import { abrir, textoDe } from './pruebas';

describe('Tablero del tutor de la entidad', () => {
  it('muestra los indicadores, las acciones rápidas, los reportes por confirmar y los practicantes', async () => {
    const { vista } = await abrir('/tutor-entidad');
    const texto = textoDe(vista);
    const kpis = [...vista.querySelectorAll('app-kpi')].map((k) => [...k.querySelectorAll('small, strong, span')].map((x) => x.textContent!.trim()));
    expect(kpis).toEqual([
      ['Reportes por confirmar', '3', 'De sus practicantes'],
      ['Practicantes', '2', 'Práctica laboral'],
      ['Informes externos', '2', 'Por registrar'],
      ['Incumplimientos reportados', '1', 'Luciana Mendieta'],
    ]);
    expect(texto).toContain('Acciones rápidas');
    expect(texto).toContain('Semana 7 · 8 h · enviado 25/05/2026');
    expect(texto).toContain('Ayudantía de docencia · 42 h de 160 h');
    expect(texto).toContain('Ayudantía de investigación · 48 h de 160 h');
    expect(vista.querySelectorAll('app-insignia').length).toBeGreaterThanOrEqual(5);
  });

  it('enlaza a cada reporte y a las demás pantallas', async () => {
    const { vista } = await abrir('/tutor-entidad');
    const enlaces = [...vista.querySelectorAll('a')].map((a) => a.getAttribute('href'));
    expect(enlaces).toContain('/tutor-entidad/confirmar-reporte?r=l7');
    expect(enlaces).toContain('/tutor-entidad/confirmar-reporte?r=d7');
    expect(enlaces).toContain('/tutor-entidad/reportes-por-confirmar');
    expect(enlaces).toContain('/tutor-entidad/practicantes');
    expect(enlaces).toContain('/tutor-entidad/incumplimiento');
    expect(enlaces).toContain('/tutor-entidad/informe-externo');
  });
});
