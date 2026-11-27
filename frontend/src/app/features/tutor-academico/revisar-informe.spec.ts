import { abrir, escribir, pulsar, textoDe } from './pruebas';

const insignia = (vista: HTMLElement) => textoDe(vista.querySelector('[aria-live="polite"]') as HTMLElement).trim();

describe('Revisar informe final (T2)', () => {
  it('muestra el informe de Valeria con el informe externo sin registrar', async () => {
    const { vista } = await abrir('/tutor-academico/revisar/informe');
    const texto = textoDe(vista);
    expect(texto).toContain('Informe final de actividades');
    expect(texto).toContain('Pasantía · enviado por el estudiante');
    expect(texto).toContain('3 de 5 días hábiles');
    expect(texto).toContain('informe-final-cuenca.pdf');
    expect(texto).toContain('Informe externo aún no registrado');
    expect(insignia(vista)).toBe('En revisión');
  });

  it('«Devolver» sin observación conserva el informe en revisión', async () => {
    const { vista, esperar } = await abrir('/tutor-academico/revisar/informe');
    pulsar(vista, 'Devolver');
    await esperar();
    expect(vista.querySelector('[role="alert"]')?.textContent?.trim()).toBe('La devolución exige una observación');
    expect(insignia(vista)).toBe('En revisión');
  });

  it('«Validar» muestra el aviso y la insignia «Validado»', async () => {
    const { vista, esperar } = await abrir('/tutor-academico/revisar/informe');
    pulsar(vista, 'Validar');
    await esperar();
    expect(textoDe(vista)).toContain('Informe final validado. Cuando el informe externo esté registrado podrá registrar la evaluación final.');
    expect(insignia(vista)).toBe('Validado');
  });

  it('«Devolver» con observación lo deja devuelto', async () => {
    const { vista, esperar } = await abrir('/tutor-academico/revisar/informe');
    escribir(vista, 'textarea', 'Agregue los resultados.');
    pulsar(vista, 'Devolver');
    await esperar();
    expect(insignia(vista)).toBe('Devuelto con observación');
  });

  it('las variantes devuelto y validado de ejemplo', async () => {
    const d = textoDe((await abrir('/tutor-academico/revisar/informe?r=v6d')).vista);
    expect(d).toContain('El resumen no menciona los resultados del módulo de inventario.');
    expect(d).toContain('04/06/2026');
    const v = textoDe((await abrir('/tutor-academico/revisar/informe?r=m5')).vista);
    expect(v).toContain('Informe final validado por PAREDES JARAMILLO ROBERTO ANDRÉS el 03/06/2026. Ya puede registrar la evaluación final.');
    expect(v).toContain('Registrado el 02/06/2026');
  });
});
