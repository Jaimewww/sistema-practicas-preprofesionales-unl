import { abrir, textoDe } from './pruebas';

describe('Confirmar reporte (R3)', () => {
  it('sin ?r= muestra la semana 8 de Luciana pendiente, con actividades y evidencias', async () => {
    const { vista } = await abrir('/tutor-entidad/confirmar-reporte');
    const texto = textoDe(vista);
    expect(texto).toContain('Reporte semanal: Semana 8');
    expect(texto).toContain('MENDIETA SARANGO LUCIANA BELÉN');
    expect(texto).toContain('Laboral: Ayudantía de docencia');
    expect(texto).toContain('25/05/2026 - 31/05/2026');
    expect(texto).toContain('Calificación de los talleres 7 y 8 de Programación.');
    expect(texto).toContain('talleres-semana-8.pdf');
    expect(texto).toContain('Pendiente de confirmación');
    expect(texto).not.toContain('Confirmado por la entidad');
  });

  it('«Confirmar» muestra el aviso, cambia la insignia a «Confirmado por la entidad» y deshabilita el botón', async () => {
    const { vista, esperar } = await abrir('/tutor-entidad/confirmar-reporte?r=l8');
    const boton = [...vista.querySelectorAll('button')].find((b) => b.textContent?.includes('Confirmar'))!;
    boton.click();
    await esperar();
    const texto = textoDe(vista);
    expect(texto).toContain('Reporte confirmado por CELI ARMIJOS MARTHA CECILIA el 05/06/2026. Quedó registrado quién confirmó y cuándo.');
    expect(texto).toContain('Confirmado por la entidad');
    expect(texto).not.toContain('Pendiente de confirmación');
    expect(boton.disabled).toBe(true);
  });

  it('un reporte ya confirmado muestra quién y cuándo, sin botón de confirmar', async () => {
    const { vista } = await abrir('/tutor-entidad/confirmar-reporte?r=d8');
    const texto = textoDe(vista);
    expect(texto).toContain('Confirmado por la entidad');
    expect(texto).toContain('Confirmado porCELI ARMIJOS MARTHA CECILIA');
    expect(texto).toContain('Fecha de confirmación02/06/2026');
    expect(texto).toContain('Reporte confirmado por CELI ARMIJOS MARTHA CECILIA el 02/06/2026.');
    expect([...vista.querySelectorAll('button')].some((b) => b.textContent?.includes('Confirmar'))).toBe(false);
    expect(texto).toContain('Volver a reportes por confirmar');
  });

  it('un reporte devuelto muestra la observación del tutor académico', async () => {
    const { vista } = await abrir('/tutor-entidad/confirmar-reporte?r=l5');
    const texto = textoDe(vista);
    expect(texto).toContain('Devuelto con observación');
    expect(texto).toContain('Falta detallar qué talleres calificó.');
  });

  it('el reporte de Luciana · semana 7 no trae detalle de actividades', async () => {
    const { vista } = await abrir('/tutor-entidad/confirmar-reporte?r=l7');
    expect(textoDe(vista)).toContain('Sin detalle de actividades en el ejemplo.');
  });

  it('un código inexistente muestra el error', async () => {
    const { vista } = await abrir('/tutor-entidad/confirmar-reporte?r=zzz');
    expect(textoDe(vista)).toContain('No existe ese reporte.');
  });
});
