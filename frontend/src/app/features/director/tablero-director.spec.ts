import { abrir, textoDe } from './pruebas';

describe('Tablero del director (D0)', () => {
  it('muestra los KPIs de cierres y los últimos cierres con su resultado', async () => {
    const { vista } = await abrir('/director');
    const texto = textoDe(vista);
    expect(texto).toContain('Prácticas cerradas 16 Carrera de Computación');
    expect(texto).toContain('Aprobadas 8');
    expect(texto).toContain('No aprobadas 8');
    expect(texto).toContain('Período MAR.26 AGO.26 GRADO');
    expect([...vista.querySelectorAll('.lista-lineas li strong')].map((s) => s.textContent)).toEqual([
      'CORDOVA VAZQUEZ JOSE LUIS',
      'AYOVI CANDO MARIA FERNANDA',
      'ESPINOZA ESTRELLA ANA LUCÍA',
    ]);
    expect(texto).toContain('Laboral · cerrada el 04/06/2026 Aprobada');
    expect(texto).toContain('Comunitaria · cerrada el 04/06/2026 No aprobada');
    expect(texto).toContain('No hay acciones de edición en estas pantallas.');
  });

  it('enlaza a la lista de cierres y no ofrece botones que modifiquen datos', async () => {
    const { vista } = await abrir('/director');
    expect(vista.querySelector('a[href="/director/cierres"]')?.textContent).toContain('Ver todos los cierres');
    expect(vista.querySelectorAll('button')).toHaveLength(0);
  });
});
