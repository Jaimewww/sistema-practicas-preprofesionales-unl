import { abrir, textoDe } from './pruebas';

describe('Tablero del estudiante', () => {
  it('muestra la práctica, el avance de horas, los pendientes y los últimos reportes', async () => {
    const { vista } = await abrir('/estudiante');
    const texto = textoDe(vista);
    expect(texto).toContain('Mi práctica');
    expect(texto).toContain('MENDIETA SARANGO LUCIANA BELÉN');
    expect(texto).toContain('En curso');
    expect(texto).toContain('Rezagada');
    expect(texto).toContain('42 h validadas de 160 h requeridas');
    expect(texto).toContain('Esperadas: 90 h');
    expect(texto).toContain('2 reportes necesitan acción.');
    expect(texto).toContain('Últimos reportes semanales');
    expect([...vista.querySelectorAll('.filas li')].map((li) => li.querySelector('strong')?.textContent)).toEqual(['Semana 8', 'Semana 7', 'Semana 6', 'Semana 5']);
  });

  it('enlaza «Corregir reporte» al reporte devuelto y «Reportar» al registro de horas', async () => {
    const { vista } = await abrir('/estudiante');
    const texto = textoDe(vista);
    expect(texto).toContain('Observación: Falta detallar qué talleres calificó.');
    expect(vista.querySelector('a[href="/estudiante/reporte?s=5"]')?.textContent).toContain('Corregir reporte');
    expect([...vista.querySelectorAll('a[href="/estudiante/reportes/nuevo"]')].map((a) => a.textContent?.trim())).toContain('Reportar semana 9');
  });

  it('lleva a la práctica y al informe final', async () => {
    const { vista } = await abrir('/estudiante');
    expect(vista.querySelector('a[href="/estudiante/practica"]')?.textContent).toContain('Ir a mi práctica');
    expect(vista.querySelector('a[href="/estudiante/informe-final"]')?.textContent).toContain('Informe final');
  });
});
