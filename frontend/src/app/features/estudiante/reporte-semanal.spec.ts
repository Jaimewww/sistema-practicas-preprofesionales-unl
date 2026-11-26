import { abrir, textoDe } from './pruebas';

describe('Reporte semanal (E5)', () => {
  it('un reporte devuelto muestra la observación del tutor y permite corregir y reenviar a E4', async () => {
    const { vista } = await abrir('/estudiante/reporte?s=5');
    const texto = textoDe(vista);
    expect(texto).toContain('Reporte de la semana 5');
    expect(texto).toContain('Devuelto con observación');
    expect(vista.querySelector('.cita[role="note"]')?.textContent).toContain('Falta detallar qué talleres calificó.');
    expect(texto).toContain('6 h (no suman al avance hasta que se valide)');
    expect(texto).toContain('Devuelto por el tutor académico');
    expect(texto).toContain('Corrección del estudiante');
    expect(vista.querySelector('a[href="/estudiante/reportes/nuevo"]')?.textContent).toContain('Corregir y reenviar');
    expect(vista.querySelector('a[href="/estudiante/practica"]')?.textContent).toContain('Volver a mi práctica');
  });

  it('muestra horas, actividades, evidencias con su versión, confirmación de la entidad y seguimiento', async () => {
    const { vista } = await abrir('/estudiante/reporte?s=8');
    const texto = textoDe(vista);
    expect(texto).toContain('8 h (no suman al avance hasta que se valide)');
    expect(texto).toContain('Calificación de los talleres 7 y 8 de Programación.');
    expect(texto).toContain('talleres-semana-8.pdf0,9 MB · versión 1');
    expect(texto).toContain('Confirmación de la entidad');
    expect(texto).toContain('Pendiente');
    expect(texto).toContain('Celi Armijos Martha Cecilia');
    expect(texto).toContain('Seguimiento');
    expect(vista.querySelector('.cita')).toBeNull();
    expect(vista.querySelector('a[href="/estudiante/reportes/nuevo"]')).toBeNull();
  });

  it('un reporte validado no pide corrección y su seguimiento lo da por completado', async () => {
    const { vista } = await abrir('/estudiante/reporte?s=6');
    const texto = textoDe(vista);
    expect(texto).toContain('Validado');
    expect(texto).toContain('Confirmado');
    expect(texto).not.toContain('no suman al avance');
    expect(texto).toContain('Las horas pasan a su avance');
  });

  it('una semana sin reporte invita a reportarla; una que no existe muestra el error', async () => {
    const sin = await abrir('/estudiante/reporte?s=9');
    expect(textoDe(sin.vista)).toContain('Aún no envía el reporte de esta semana.');
    expect(sin.vista.querySelector('a[href="/estudiante/reportes/nuevo"]')?.textContent).toContain('Reportar semana 9');
  });
});

describe('Reporte semanal (E5): semana inexistente', () => {
  it('muestra el error del servicio', async () => {
    const { vista } = await abrir('/estudiante/reporte?s=40');
    expect(vista.querySelector('app-aviso[role="alert"]')?.textContent).toContain('No existe un reporte para esa semana.');
  });
});
