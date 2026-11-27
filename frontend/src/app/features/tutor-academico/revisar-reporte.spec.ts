import { escribir, abrir, pulsar, textoDe } from './pruebas';

const insignia = (vista: HTMLElement) => textoDe(vista.querySelector('[aria-live="polite"]') as HTMLElement).trim();

describe('Revisar reporte semanal (T2)', () => {
  it('muestra el reporte fuera de plazo, la práctica y la confirmación de la entidad', async () => {
    const { vista } = await abrir('/tutor-academico/revisar/reporte');
    const texto = textoDe(vista);
    expect(texto).toContain('Reporte semanal: Semana 7');
    expect(texto).toContain('Ayudantía de investigación · 18/05/2026 - 24/05/2026');
    expect(texto).toContain('Fuera del plazo de revisión. Lleva 9 días hábiles; el plazo de la carrera es de 5. Se avisó a la coordinación.');
    expect(texto).toContain('9 de 5 días hábiles');
    expect(texto).toContain('Pendiente de confirmación');
    expect(texto).toContain('limpieza-datos-semana-7.pdf');
    expect(texto).toContain('JIMÉNEZ CASTILLO DIEGO ALEJANDRO');
    expect(texto).toContain('Rezagada');
    expect(insignia(vista)).toBe('En revisión');
  });

  it('muestra el límite de 10 h de la ayudantía y la confirmación de la entidad', async () => {
    const luciana = textoDe((await abrir('/tutor-academico/revisar/reporte?r=l8')).vista);
    expect(luciana).toContain('8 h (límite de ayudantía: 10 h, Art. 341)');
    expect(luciana).toContain('Pendiente de confirmación');
  });

  it('en el límite y confirmado por la entidad', async () => {
    const { vista } = await abrir('/tutor-academico/revisar/reporte?r=d8');
    const texto = textoDe(vista);
    expect(texto).toContain('10 h (en el límite de la ayudantía, Art. 341)');
    expect(texto).toContain('Confirmado por la entidad');
    expect(texto).toContain('4 de 5 días hábiles');
    expect(texto).not.toContain('Fuera del plazo de revisión.');
  });

  it('«Devolver» sin observación muestra el error y el reporte sigue en revisión', async () => {
    const { vista, esperar } = await abrir('/tutor-academico/revisar/reporte?r=l8');
    pulsar(vista, 'Devolver');
    await esperar();
    const alerta = vista.querySelector('[role="alert"]');
    expect(alerta?.textContent?.trim()).toBe('La devolución exige una observación');
    expect(vista.querySelector('textarea')?.getAttribute('aria-invalid')).toBe('true');
    expect(textoDe(vista)).toContain('No se registró la decisión: el elemento sigue en su bandeja de pendientes, en revisión.');
    expect(insignia(vista)).toBe('En revisión');
    expect(textoDe(vista)).not.toContain('Reporte devuelto con observación.');
    expect([...vista.querySelectorAll('button')].every((b) => !b.disabled)).toBe(true);
  });

  it('una observación de solo espacios tampoco cuenta', async () => {
    const { vista, esperar } = await abrir('/tutor-academico/revisar/reporte?r=l8');
    escribir(vista, 'textarea', '   ');
    pulsar(vista, 'Devolver');
    await esperar();
    expect(vista.querySelector('[role="alert"]')?.textContent?.trim()).toBe('La devolución exige una observación');
    expect(insignia(vista)).toBe('En revisión');
  });

  it('escribir la observación quita el error', async () => {
    const { vista, esperar } = await abrir('/tutor-academico/revisar/reporte?r=l8');
    pulsar(vista, 'Devolver');
    await esperar();
    escribir(vista, 'textarea', 'Falta la lista firmada.');
    await esperar();
    expect(vista.querySelector('[role="alert"]')).toBeNull();
  });

  it('«Validar» muestra el aviso de éxito y la insignia pasa a «Validado»', async () => {
    const { vista, esperar } = await abrir('/tutor-academico/revisar/reporte?r=l8');
    pulsar(vista, 'Validar');
    await esperar();
    expect(textoDe(vista)).toContain('Reporte validado. Sus 8 h ya cuentan como horas validadas de la práctica.');
    expect(insignia(vista)).toBe('Validado');
    expect(textoDe(vista)).toContain('Validado por PAREDES JARAMILLO ROBERTO ANDRÉS');
    expect([...vista.querySelectorAll('button')].every((b) => b.disabled)).toBe(true);
  });

  it('«Devolver» con observación lo deja «Devuelto con observación» y la muestra', async () => {
    const { vista, esperar } = await abrir('/tutor-academico/revisar/reporte?r=l8');
    escribir(vista, 'textarea', 'Falta detallar los talleres.');
    pulsar(vista, 'Devolver');
    await esperar();
    expect(textoDe(vista)).toContain('Reporte devuelto con observación. El estudiante la verá y podrá corregir el reporte y reenviarlo.');
    expect(insignia(vista)).toBe('Devuelto con observación');
    expect(textoDe(vista)).toContain('Observación del tutor Falta detallar los talleres.');
    expect(vista.querySelector('[role="alert"]')).toBeNull();
  });

  it('el reporte devuelto de ejemplo muestra la observación y no ofrece decidir', async () => {
    const { vista } = await abrir('/tutor-academico/revisar/reporte?r=l5');
    const texto = textoDe(vista);
    expect(texto).toContain('Reporte semanal devuelto con observación. El estudiante verá la observación y podrá corregirlo.');
    expect(texto).toContain('Devuelto por PAREDES JARAMILLO ROBERTO ANDRÉS');
    expect(texto).toContain('Falta detallar qué talleres calificó.');
    expect(insignia(vista)).toBe('Devuelto con observación');
    expect([...vista.querySelectorAll('button')]).toHaveLength(0);
    expect(texto).toContain('Siguiente paso');
  });

  it('el reporte validado de ejemplo dice quién lo validó y cuándo', async () => {
    const { vista } = await abrir('/tutor-academico/revisar/reporte?r=l6');
    expect(textoDe(vista)).toContain('Reporte semanal validado por PAREDES JARAMILLO ROBERTO ANDRÉS el 20/05/2026. Sus 4 h ya cuentan como horas validadas de la práctica.');
    expect(insignia(vista)).toBe('Validado');
  });

  it('una clave desconocida abre el primer ejemplo', async () => {
    const { vista } = await abrir('/tutor-academico/revisar/reporte?r=zzz');
    expect(textoDe(vista)).toContain('Reporte semanal: Semana 7');
  });

  it('los estados de ejemplo marcan el activo con aria-current', async () => {
    const { vista } = await abrir('/tutor-academico/revisar/reporte?r=d8');
    const activo = vista.querySelector('.demo-vistas a[aria-current="true"]');
    expect(activo?.textContent).toBe('Semana 8 · Diego');
  });
});
