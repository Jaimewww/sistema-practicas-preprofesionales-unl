import { abrir, textoDe } from './pruebas';

describe('Práctica del tutorado (T4)', () => {
  it('muestra los datos, las horas rezagadas y los reportes de Luciana', async () => {
    const { vista } = await abrir('/tutor-academico/practica');
    const texto = textoDe(vista);
    expect(texto).toContain('MENDIETA SARANGO LUCIANA BELÉN');
    expect(texto).toContain('Laboral: Ayudantía de docencia');
    expect(texto).toContain('Rezagada. Entre validadas y en revisión suma 50 h; el mínimo es 72 h (80 % de las 90 h esperadas a la semana 9).');
    expect(vista.querySelectorAll('ol.semanas li')).toHaveLength(16);
    expect(vista.querySelectorAll('#tabla-reportes tbody tr')).toHaveLength(9);
    expect(texto).toContain('Todavía no corresponde');
    expect(texto).toContain('No asistió dos días consecutivos a las tutorías de refuerzo sin presentar justificativo.');
    expect(texto).toContain('Asignada');
    expect(vista.querySelector('a[href="/tutor-academico/revisar/reporte?r=l8"]')?.textContent).toContain('Revisar');
    expect(vista.querySelector('a[href="/tutor-academico/revisar/plan?r=l1"]')?.textContent).toContain('Ver plan');
  });

  it('Andrea, asignada: sin reportes y con el plan por revisar', async () => {
    const { vista } = await abrir('/tutor-academico/practica?p=4');
    const texto = textoDe(vista);
    expect(texto).toContain('Sin reportes todavía');
    expect(texto).toContain('Sin plan aprobado: la práctica pasa a «En curso» cuando valide el plan de actividades.');
    expect(texto).toContain('No aplica (práctica comunitaria)');
    expect(vista.querySelector('a[href="/tutor-academico/revisar/plan?r=a4"]')?.textContent).toContain('Revisar plan');
    expect(texto).toContain('Sin incumplimientos');
  });

  it('en revisión final muestra los informes y lleva a la evaluación', async () => {
    const m = await abrir('/tutor-academico/practica?p=5');
    expect(textoDe(m.vista)).toContain('Registrado el 02/06/2026');
    expect(textoDe(m.vista)).toMatch(/En revisión final \(En curso\) 03\/06\/2026/);
    expect(m.vista.querySelector('a[href="/tutor-academico/evaluacion?p=5"]')?.textContent).toContain('Registrar evaluación final');
    const v = await abrir('/tutor-academico/practica?p=6');
    expect(textoDe(v.vista)).toContain('Aún no registrado');
    expect(v.vista.querySelector('a[href="/tutor-academico/revisar/informe?r=v6"]')?.textContent).toContain('Revisar informe final');
  });

  it('la práctica suspendida es de solo lectura: avisa y no ofrece revisar', async () => {
    const { vista } = await abrir('/tutor-academico/practica?p=ro');
    const texto = textoDe(vista);
    expect(texto).toContain('Práctica suspendida: solo lectura.');
    expect(texto).toContain('la coordinación suspendió la práctica el 20/05/2026 por licencia de la persona practicante');
    expect(texto).toContain('Suspendida');
    expect(vista.querySelectorAll('#tabla-reportes a')).toHaveLength(0);
    expect(vista.querySelector('a[href^="/tutor-academico/revisar"]')).toBeNull();
  });

  it('una práctica que no es de la persona muestra el error', async () => {
    const { vista } = await abrir('/tutor-academico/practica?p=2');
    expect(vista.querySelector('[role="alert"]')).not.toBeNull();
  });
});
