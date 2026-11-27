import { abrir, textoDe } from './pruebas';

describe('Alertas (C2)', () => {
  it('agrupa las alertas activas por tipo con su conteo', async () => {
    const { vista } = await abrir('/coordinador/alertas');
    const titulos = [...vista.querySelectorAll('app-tarjeta h3')].map((h) => h.textContent);
    expect(titulos).toEqual(['Alertas activas', 'Reportes no enviados', 'Revisiones pendientes', 'Horas rezagadas', 'Incumplimientos reportados']);
    const texto = textoDe(vista);
    expect(texto).toContain('La semana se cerró y el plazo de reporte (3 días) venció.');
    expect(texto).toContain('El tutor académico superó el plazo de revisión (5 días hábiles).');
    expect(texto).toMatch(/Mostrando \d+ de \d+ alertas activas de este tipo\./);
  });

  it('el filtro deja solo el tipo elegido', async () => {
    const { vista, esperar } = await abrir('/coordinador/alertas');
    const s = vista.querySelector<HTMLSelectElement>('#f-tipo-alerta')!;
    s.value = 'incumplimiento';
    s.dispatchEvent(new Event('change'));
    await esperar();
    const titulos = [...vista.querySelectorAll('app-tarjeta h3')].map((h) => h.textContent);
    expect(titulos).toEqual(['Alertas activas', 'Incumplimientos reportados']);
  });

  it('alterna el estado sin alertas de demostración', async () => {
    const { vista, esperar } = await abrir('/coordinador/alertas');
    vista.querySelector<HTMLButtonElement>('#demo-vacio')!.click();
    await esperar();
    expect(textoDe(vista)).toContain('No hay alertas activas');
    expect(vista.querySelector('table')).toBeNull();
    vista.querySelector<HTMLButtonElement>('#volver-alertas')!.click();
    await esperar();
    expect(vista.querySelector('table')).not.toBeNull();
  });
});
