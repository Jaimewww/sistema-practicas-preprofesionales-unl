import { abrir, escribir, textoDe } from './pruebas';

describe('Mis practicantes (R1)', () => {
  it('lista los practicantes con estado, horas y enlaces al informe externo y al incumplimiento', async () => {
    const { vista } = await abrir('/tutor-entidad/practicantes');
    const texto = textoDe(vista);
    expect(texto).toContain('Solo aparecen las prácticas laborales');
    expect(vista.querySelectorAll('tbody tr')).toHaveLength(2);
    expect(texto).toContain('Laboral: Ayudantía de docencia');
    expect(texto).toContain('Tutor académico: PAREDES JARAMILLO ROBERTO ANDRÉS');
    expect(texto).toContain('42 h de 160 h');
    expect(texto).toContain('En revisión: 8 h');
    expect(texto).toContain('En curso');
    expect(texto).toContain('Rezagada');
    expect(texto).toContain('2 de 2 practicantes mostrados.');
    const enlaces = [...vista.querySelectorAll('a')].map((a) => a.getAttribute('href'));
    expect(enlaces).toContain('/tutor-entidad/informe-externo?p=1');
    expect(enlaces).toContain('/tutor-entidad/incumplimiento?p=3');
  });

  it('la búsqueda y el filtro de avance filtran de verdad', async () => {
    const { vista, esperar } = await abrir('/tutor-entidad/practicantes');
    escribir(vista.querySelector<HTMLInputElement>('#f-q')!, 'jiménez');
    await esperar();
    expect(vista.querySelectorAll('tbody tr')).toHaveLength(1);
    expect(textoDe(vista)).toContain('1 de 2 practicantes mostrados.');
    escribir(vista.querySelector<HTMLSelectElement>('#f-avance')!, 'aldia');
    await esperar();
    expect(vista.querySelectorAll('tbody tr')).toHaveLength(0);
    expect(textoDe(vista)).toContain('Ningún practicante coincide');
  });

  it('el botón alterna el estado «sin practicantes»', async () => {
    const { vista, esperar } = await abrir('/tutor-entidad/practicantes');
    vista.querySelector<HTMLButtonElement>('button')!.click();
    await esperar();
    expect(textoDe(vista)).toContain('Sin practicantes asignados');
    expect(vista.querySelector('table')).toBeNull();
    vista.querySelector<HTMLButtonElement>('button')!.click();
    await esperar();
    expect(vista.querySelectorAll('tbody tr')).toHaveLength(2);
  });

  it('con ?vacio=1 abre en el estado vacío', async () => {
    const { vista } = await abrir('/tutor-entidad/practicantes?vacio=1');
    expect(textoDe(vista)).toContain('No tiene practicantes de práctica laboral asignados en este periodo.');
  });
});
