import { abrir, textoDe } from './pruebas';

describe('Tablero de Secretaría (S0)', () => {
  it('muestra los indicadores y los siguientes anexos', async () => {
    const { vista } = await abrir('/secretaria');
    const texto = textoDe(vista);
    expect(texto).toContain('Por legalizar');
    expect(texto).toContain('Legalizados');
    expect(texto).toContain('Siguientes anexos');
    expect(texto).toContain('no cambia el estado de la práctica');
    expect(vista.querySelectorAll('app-kpi')).toHaveLength(4);
    expect(vista.querySelectorAll('ul.lineas li').length).toBeGreaterThan(0);
    expect(vista.querySelector('a.boton')?.getAttribute('href')).toBe('/secretaria/anexos');
  });
});
