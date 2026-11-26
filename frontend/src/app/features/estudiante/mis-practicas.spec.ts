import { abrir, textoDe } from './pruebas';

describe('Mis prácticas (E1)', () => {
  it('lista la práctica laboral y la comunitaria como registros separados', async () => {
    const { vista } = await abrir('/estudiante/mis-practicas');
    const tarjetas = [...vista.querySelectorAll('app-tarjeta')].map((t) => t.querySelector('h3')?.textContent);
    expect(tarjetas).toEqual([
      'Mis prácticas',
      'Universidad Nacional de Loja - Carrera de Computación',
      'Proyecto de vinculación · Alfabetización digital para adultos mayores del cantón Loja',
    ]);
    const texto = textoDe(vista);
    expect(texto).toContain('Tutora de la entidad');
    expect(texto).toContain('No aplica en servicio comunitario');
    expect(texto).toContain('42 h validadas · 8 h en revisión · 160 h requeridas');
    expect(texto).toContain('52 h validadas · 6 h en revisión · 96 h requeridas');
  });

  it('cada tarjeta lleva a su práctica con ?p=', async () => {
    const { vista } = await abrir('/estudiante/mis-practicas');
    const enlaces = [...vista.querySelectorAll('a.boton')].map((a) => [a.textContent?.trim(), a.getAttribute('href')]);
    expect(enlaces).toEqual([
      ['Ir a mi práctica', '/estudiante/practica'],
      ['Ir a mi práctica', '/estudiante/practica?p=2'],
    ]);
  });
});
