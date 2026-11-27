import { abrir, textoDe } from './pruebas';

describe('Detalle del cierre (D2)', () => {
  it('muestra la práctica 8 como aprobada, con datos, horas, evaluación y anexos', async () => {
    const { vista } = await abrir('/director/cierre?p=8');
    const texto = textoDe(vista);
    expect(vista.querySelector('h3')?.textContent).toBe('CORDOVA VAZQUEZ JOSE LUIS');
    expect(texto).toContain('Aprobada Cerrada el 04/06/2026');
    expect(texto).toContain('Tipo Laboral: Pasantía');
    expect(texto).toContain('Entidad receptora Agroindustrias del Norte Cía. Ltda.');
    expect(texto).toContain('Tutor de la entidad VIVANCO LEÓN PABLO ESTEBAN');
    expect(texto).toContain('Horas validadas 160 h de 160 h requeridas');
    expect(vista.querySelector('[role="img"]')?.getAttribute('aria-label')).toContain('160 h validadas');
    expect(texto).toContain('Resultado de la evaluación final');
    expect(texto).toContain('Desempeño 92 %');
    expect(texto).toContain('Registrado por CAÑAR MERCHÁN WASHINGTON EDUARDO el 03/06/2026');
    expect(texto).toContain('Los legaliza la Secretaría de la carrera.');
    expect(texto).toContain('Informe final del estudiante informe-final-cerrada-8.pdf Legalizado TORRES REYES GLADYS ELENA el 05/06/2026');
    expect(texto).toContain('Informe externo del tutor de la entidad informe-externo-cerrada-8.pdf Pendiente de legalización —');
    expect(texto).not.toContain('No aprobada');
  });

  it('muestra la práctica 9 como no aprobada, con el proyecto de vinculación', async () => {
    const { vista } = await abrir('/director/cierre?p=9');
    const texto = textoDe(vista);
    expect(vista.querySelector('h3')?.textContent).toBe('AYOVI CANDO MARIA FERNANDA');
    expect(texto).toContain('No aprobada Cerrada el 04/06/2026');
    expect(texto).toContain('Tipo Comunitaria');
    expect(texto).toContain('Proyecto de vinculación Alfabetización digital en el GAD de Catamayo');
    expect(texto).toContain('Desempeño 64 %');
    expect(texto).toContain('Informe del proyecto de vinculación informe-externo-cerrada-9.pdf Pendiente de legalización');
  });

  it('es de solo lectura: ningún botón ni formulario modifica datos', async () => {
    const { vista } = await abrir('/director/cierre?p=8');
    expect(vista.querySelectorAll('button, input, select, textarea, form')).toHaveLength(0);
  });

  it('las pestañas conservan ?p= y hay regreso a la lista', async () => {
    const { vista } = await abrir('/director/cierre?p=9');
    expect([...vista.querySelectorAll('ul[aria-label="Secciones"] a')].map((a) => [a.textContent?.trim(), a.getAttribute('href')])).toEqual([
      ['Resumen del cierre', '/director/cierre?p=9'],
      ['Historial', '/director/cierre/historial?p=9'],
    ]);
    expect(vista.querySelector('a[href="/director/cierres"]')?.textContent).toContain('Volver a los cierres');
  });

  it('un cierre que no existe muestra el error', async () => {
    const { vista } = await abrir('/director/cierre?p=1');
    expect(textoDe(vista)).toContain('No encontrado');
    expect(vista.querySelector('h3')).toBeNull();
  });
});
