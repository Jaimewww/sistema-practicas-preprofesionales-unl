import { abrir, textoDe } from './pruebas';

const botones = (vista: HTMLElement) => [...vista.querySelectorAll('.acciones-fila a, .acciones-fila button')].map((x) => x.textContent?.trim());

describe('Práctica (C3)', () => {
  it('el resumen muestra datos, horas, documentos y alertas de la práctica en curso', async () => {
    const { vista, esperar } = await abrir('/coordinador/practica?p=1');
    await esperar();
    const texto = textoDe(vista);
    expect(texto).toContain('Mendieta Sarango Luciana Belén');
    expect(texto).toContain('Avance de horas');
    expect(texto).toContain('Plan, informes y evaluación');
    expect(texto).toContain('Sin evaluación final registrada');
    expect(texto).toContain('Alertas activas');
    expect(botones(vista)).toEqual(['Suspender', 'Volver a la lista']);
    expect(vista.querySelector('[aria-current="page"]')?.textContent?.trim()).toBe('Resumen');
  });

  it('en revisión final ofrece cerrar; suspendida ofrece reanudar y cancelar (solo lectura)', async () => {
    const final = await abrir('/coordinador/practica?p=7');
    expect(botones(final.vista)).toEqual(['Cerrar práctica', 'Volver a la lista']);
  });

  it('el selector de estado de la demostración cambia las acciones y el modo de solo lectura', async () => {
    const { vista, esperar } = await abrir('/coordinador/practica?p=1');
    const s = vista.querySelector<HTMLSelectElement>('#demo-estado')!;
    s.value = 'suspendida';
    s.dispatchEvent(new Event('change'));
    await esperar();
    await esperar();
    expect(botones(vista)).toEqual(['Reanudar', 'Cancelar práctica', 'Volver a la lista']);
    expect(textoDe(vista)).toContain('Práctica suspendida: solo lectura. Para seguir, reanúdela o cancélela.');
    s.value = 'cerrada';
    s.dispatchEvent(new Event('change'));
    await esperar();
    await esperar();
    expect(textoDe(vista)).toContain('En estado «Cerrada» no hay decisiones del coordinador disponibles.');
    expect(botones(vista)).toEqual(['Volver a la lista']);
  });

  it('el historial lista quién, qué y cuándo con lo más reciente primero', async () => {
    const { vista, esperar } = await abrir('/coordinador/practica/historial?p=8');
    await esperar();
    const texto = textoDe(vista);
    expect(texto).toContain('Historial de estados');
    expect([...vista.querySelectorAll('th')].map((t) => t.textContent)).toEqual(['Cuándo', 'Quién', 'Qué', 'Motivo']);
    const filas = vista.querySelectorAll('tbody tr');
    expect(filas.length).toBeGreaterThan(0);
    expect(filas[0].textContent).toContain('Cerrada');
    expect(vista.querySelector('[aria-current="page"]')?.textContent?.trim()).toBe('Historial');
  });
});
