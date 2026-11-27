import { abrir, textoDe } from './pruebas';

describe('Tablero del coordinador (C0)', () => {
  it('muestra los indicadores de la carrera y las decisiones pendientes', async () => {
    const { vista } = await abrir('/coordinador');
    const texto = textoDe(vista);
    expect(texto).toContain('Prácticas de la carrera');
    expect(texto).toContain('150');
    expect(texto).toContain('Prácticas por estado');
    expect(texto).toContain('Acciones rápidas');
    expect(texto).toContain('Alertas por tipo');
    expect(texto).toContain('Prácticas que necesitan una decisión');
    expect(vista.querySelectorAll('app-kpi')).toHaveLength(4);
  });

  it('las filas de decisión llevan a cerrar o a la práctica con ?p=', async () => {
    const { vista } = await abrir('/coordinador');
    const enlaces = [...vista.querySelectorAll('a.boton')].map((a) => a.getAttribute('href') ?? '');
    expect(enlaces.length).toBeGreaterThan(0);
    expect(enlaces.every((h) => /\?p=\d+$/.test(h))).toBe(true);
  });
});
