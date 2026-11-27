import { abrir, escribir, pulsar, textoDe } from './pruebas';

const insignia = (vista: HTMLElement) => textoDe(vista.querySelector('[aria-live="polite"]') as HTMLElement).trim();

describe('Revisar plan de actividades (T2)', () => {
  it('muestra el plan de Andrea en revisión, sin plan aprobado todavía', async () => {
    const { vista } = await abrir('/tutor-academico/revisar/plan');
    const texto = textoDe(vista);
    expect(texto).toContain('Plan de actividades');
    expect(texto).toContain('Práctica comunitaria · sin plan aprobado todavía');
    expect(texto).toContain('5 de 5 días hábiles');
    expect(texto).toContain('Sitio web informativo para el GAD parroquial de Vilcabamba');
    expect(texto).toContain('Capacitación al personal que lo actualizará.');
    expect(insignia(vista)).toBe('En revisión');
  });

  it('«Devolver» sin observación muestra el error y sigue en revisión', async () => {
    const { vista, esperar } = await abrir('/tutor-academico/revisar/plan');
    pulsar(vista, 'Devolver');
    await esperar();
    expect(vista.querySelector('[role="alert"]')?.textContent?.trim()).toBe('La devolución exige una observación');
    expect(insignia(vista)).toBe('En revisión');
  });

  it('«Validar» pasa la práctica a «En curso»', async () => {
    const { vista, esperar } = await abrir('/tutor-academico/revisar/plan');
    pulsar(vista, 'Validar');
    await esperar();
    expect(textoDe(vista)).toContain('Plan validado. La práctica pasa a «En curso» y el estudiante ya puede enviar sus reportes semanales.');
    expect(insignia(vista)).toBe('Validado');
    expect(textoDe(vista)).toContain('En curso');
  });

  it('«Devolver» con observación lo deja devuelto', async () => {
    const { vista, esperar } = await abrir('/tutor-academico/revisar/plan');
    escribir(vista, 'textarea', 'Indique las horas por actividad.');
    pulsar(vista, 'Devolver');
    await esperar();
    expect(textoDe(vista)).toContain('Plan devuelto con observación. El estudiante verá la observación y podrá corregir el plan.');
    expect(insignia(vista)).toBe('Devuelto con observación');
  });

  it('las variantes devuelto y validado muestran quién decidió', async () => {
    const d = textoDe((await abrir('/tutor-academico/revisar/plan?r=a4d')).vista);
    expect(d).toContain('Plan de actividades devuelto con observación');
    expect(d).toContain('Devuelto por PAREDES JARAMILLO ROBERTO ANDRÉS');
    expect(d).toContain('Indique cuántas horas dedicará a cada actividad');
    const v = textoDe((await abrir('/tutor-academico/revisar/plan?r=l1')).vista);
    expect(v).toContain('Plan de actividades validado por PAREDES JARAMILLO ROBERTO ANDRÉS');
    expect(v).toContain('La práctica pasó a «En curso».');
  });
});
