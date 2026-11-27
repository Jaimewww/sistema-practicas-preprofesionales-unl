import { abrir, textoDe } from './pruebas';

describe('Historial del cierre (D2)', () => {
  it('muestra quién, qué y cuándo de la práctica 8 y su línea de seguimiento', async () => {
    const { vista } = await abrir('/director/cierre/historial?p=8');
    const texto = textoDe(vista);
    expect(texto).toContain('Historial de CORDOVA VAZQUEZ JOSE LUIS');
    expect(texto).toContain('Solo lectura: cada cambio conserva el estado anterior y el nuevo, quién lo hizo y cuándo (RF-10). El director únicamente consulta.');
    const filas = [...vista.querySelectorAll('tbody tr')].map((f) => textoDe(f).trim());
    expect(filas).toEqual([
      '— Asignada SISTEMA 06/04/2026 —',
      'Asignada En curso CAÑAR MERCHÁN WASHINGTON EDUARDO 10/04/2026 —',
      'En curso En revisión final CAÑAR MERCHÁN WASHINGTON EDUARDO 03/06/2026 —',
      'En revisión final Cerrada (aprobada) MENDOZA ARÉVALO CARLOS ANDRÉS 04/06/2026 Práctica cerrada con el resultado de la evaluación final.',
    ]);
    expect(texto).toContain('Línea de seguimiento');
    expect(vista.querySelectorAll('ol li')).toHaveLength(4);
    expect(textoDe(vista.querySelectorAll('ol li')[3])).toContain('Cerrada (aprobada) (Completado) MENDOZA ARÉVALO CARLOS ANDRÉS · 04/06/2026');
  });

  it('la práctica 9 termina en «Cerrada (no aprobada)» y no hay controles que modifiquen datos', async () => {
    const { vista } = await abrir('/director/cierre/historial?p=9');
    expect(textoDe(vista)).toContain('Historial de AYOVI CANDO MARIA FERNANDA');
    expect(textoDe(vista)).toContain('Cerrada (no aprobada)');
    expect(vista.querySelectorAll('button, input, select, textarea, form')).toHaveLength(0);
  });

  it('la pestaña Historial está activa', async () => {
    const { vista } = await abrir('/director/cierre/historial?p=8');
    expect(vista.querySelector('ul[aria-label="Secciones"] a[aria-current="page"]')?.textContent?.trim()).toBe('Historial');
  });
});
