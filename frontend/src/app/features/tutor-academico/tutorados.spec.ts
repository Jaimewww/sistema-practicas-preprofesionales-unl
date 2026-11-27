import { abrir, escribir, filas, pulsar, textoDe } from './pruebas';

describe('Mis tutorados (T3)', () => {
  it('muestra los indicadores y las cinco prácticas con su avance', async () => {
    const { vista } = await abrir('/tutor-academico/tutorados');
    const kpis = [...vista.querySelectorAll('app-kpi')].map((k) => textoDe(k as HTMLElement).trim());
    expect(kpis).toEqual(['Tutorados 5 MAR.26-AGO.26 GRADO', 'En curso 2', 'En revisión final 2 Esperan evaluación final', 'Rezagadas 2 Por debajo del 80 % de lo esperado']);
    expect(filas(vista)).toHaveLength(5);
    expect(filas(vista).map((f) => f.cells[4].textContent?.trim())).toEqual(['Rezagada', 'Rezagada', 'Sin plan aprobado', 'Horas completas', 'Horas completas']);
    expect(textoDe(vista)).toContain('42 h de 160 h');
    expect(textoDe(vista)).toContain('En revisión: 18 h');
    expect(vista.querySelector('a[href="/tutor-academico/practica?p=4"]')?.textContent).toContain('Ver práctica');
  });

  it('la búsqueda, el estado y el avance filtran las filas', async () => {
    const { vista, esperar } = await abrir('/tutor-academico/tutorados');
    escribir(vista, '#f-q', 'jiménez');
    await esperar();
    expect(filas(vista)).toHaveLength(1);
    escribir(vista, '#f-q', '');
    escribir(vista, '#f-estado', 'en_revision_final');
    await esperar();
    expect(filas(vista)).toHaveLength(2);
    escribir(vista, '#f-estado', '');
    escribir(vista, '#f-avance', 'rezagada');
    await esperar();
    expect(filas(vista)).toHaveLength(2);
    expect(textoDe(vista)).toContain('2 de 5 prácticas mostradas.');
  });

  it('si ninguna coincide muestra el estado vacío del filtro', async () => {
    const { vista, esperar } = await abrir('/tutor-academico/tutorados');
    escribir(vista, '#f-q', 'zzzz');
    await esperar();
    expect(filas(vista)).toHaveLength(0);
    expect(textoDe(vista)).toContain('Ninguna práctica coincide con el filtro Cambie la búsqueda o los filtros.');
  });

  it('la variante «sin tutorados» muestra el estado vacío', async () => {
    const { vista, esperar } = await abrir('/tutor-academico/tutorados');
    pulsar(vista, 'Ver sin tutorados');
    await esperar();
    expect(textoDe(vista)).toContain('Sin prácticas asignadas No tiene prácticas asignadas como tutor académico en este periodo.');
    expect(vista.querySelector('table')).toBeNull();
    pulsar(vista, 'Volver a la lista');
    await esperar();
    expect(filas(vista)).toHaveLength(5);
  });

  it('abre en la variante vacía con ?vacio=1', async () => {
    const { vista } = await abrir('/tutor-academico/tutorados?vacio=1');
    expect(textoDe(vista)).toContain('Sin prácticas asignadas');
  });
});
