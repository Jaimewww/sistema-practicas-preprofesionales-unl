import { abrir, escribir, textoDe } from './pruebas';

const enviar = (vista: HTMLElement) => [...vista.querySelectorAll('button')].find((b) => b.textContent?.includes('Enviar'))!.click();

describe('Reportar incumplimiento (R5)', () => {
  it('muestra el formulario y lo ya reportado para Luciana', async () => {
    const { vista } = await abrir('/tutor-entidad/incumplimiento');
    const texto = textoDe(vista);
    expect(texto).toContain('Se avisa al tutor académico de la práctica (HU-12, RF-18).');
    expect(texto).toContain('Para Luciana Mendieta:');
    expect(texto).toContain('18/05/2026 · CELI ARMIJOS MARTHA CECILIA');
    expect(texto).toContain('No asistió dos días consecutivos a las tutorías de refuerzo sin presentar justificativo.');
    expect(texto).toContain('Aviso enviado a PAREDES JARAMILLO ROBERTO ANDRÉS.');
    expect(vista.querySelector('label[for="descripcion"]')).not.toBeNull();
  });

  it('con una descripción vacía muestra el error y no envía', async () => {
    const { vista, esperar } = await abrir('/tutor-entidad/incumplimiento');
    escribir(vista.querySelector<HTMLTextAreaElement>('#descripcion')!, '   ');
    enviar(vista);
    await esperar();
    expect(vista.querySelector('.resumen-error li')?.textContent).toBe('Describa el incumplimiento.');
    expect(vista.querySelector('#error-descripcion')?.textContent).toContain('Describa el incumplimiento.');
    expect(vista.querySelector('#descripcion')?.getAttribute('aria-invalid')).toBe('true');
    expect(textoDe(vista)).not.toContain('Incumplimiento reportado por');
  });

  it('con texto avisa al tutor académico y suma el incumplimiento a la lista', async () => {
    const { vista, esperar } = await abrir('/tutor-entidad/incumplimiento?p=3');
    expect(textoDe(vista)).toContain('Aún no hay incumplimientos reportados');
    escribir(vista.querySelector<HTMLTextAreaElement>('#descripcion')!, 'No entregó el avance acordado.');
    enviar(vista);
    await esperar();
    const texto = textoDe(vista);
    expect(texto).toContain('Incumplimiento reportado por CELI ARMIJOS MARTHA CECILIA el 05/06/2026. Se avisó al tutor académico PAREDES JARAMILLO ROBERTO ANDRÉS.');
    expect(texto).toContain('No entregó el avance acordado.');
    expect(vista.querySelector('.resumen-error')).toBeNull();
    expect(vista.querySelector<HTMLTextAreaElement>('#descripcion')!.disabled).toBe(true);
  });
});
