import { abrir, escribir, pulsar, textoDe } from './pruebas';

const resultado = (vista: HTMLElement) => textoDe(vista.querySelector('.resultado .resultado') as HTMLElement).trim();

describe('Evaluación final (T5)', () => {
  it('con el informe validado y el externo registrado se puede evaluar', async () => {
    const { vista } = await abrir('/tutor-academico/evaluacion');
    const texto = textoDe(vista);
    expect(texto).toContain('TORRES VIVANCO MATEO JOSÉ. Práctica laboral: pasantía en Soluciones Informáticas del Sur Cía. Ltda.');
    expect(texto).toContain('Informe final del estudiante: validado el 03/06/2026.');
    expect(texto).toContain('Informe externo del tutor de la entidad: registrado el 02/06/2026.');
    expect(texto).toContain('Aprobada desde 70 % (RF-17, Art. 339)');
    expect(texto).not.toContain('..');
    expect(vista.querySelector<HTMLInputElement>('#porcentaje-5')?.value).toBe('75');
    expect(resultado(vista)).toBe('Aprobada 75 % (desde 70 % se aprueba)');
  });

  it('con 70 % queda Aprobada y con 69 % No aprobada', async () => {
    const { vista, esperar } = await abrir('/tutor-academico/evaluacion?p=5');
    escribir(vista, '#porcentaje-5', '70');
    await esperar();
    expect(resultado(vista)).toContain('Aprobada');
    expect(resultado(vista)).not.toContain('No aprobada');
    expect(vista.querySelector('.medidor')?.classList.contains('ok')).toBe(true);
    escribir(vista, '#porcentaje-5', '69');
    await esperar();
    expect(resultado(vista)).toBe('No aprobada 69 % (por debajo de 70 %)');
    expect(vista.querySelector('.medidor')?.classList.contains('ok')).toBe(false);
  });

  it('el contador − y + mueve el porcentaje y respeta 0 y 100', async () => {
    const { vista, esperar } = await abrir('/tutor-academico/evaluacion?p=5');
    escribir(vista, '#porcentaje-5', '100');
    await esperar();
    expect(vista.querySelector<HTMLButtonElement>('button[aria-label="Aumentar Desempeño"]')?.disabled).toBe(true);
    vista.querySelector<HTMLButtonElement>('button[aria-label="Disminuir Desempeño"]')?.click();
    await esperar();
    expect(vista.querySelector<HTMLInputElement>('#porcentaje-5')?.value).toBe('99');
  });

  it('«Guardar» registra la evaluación, muestra el éxito y bloquea el formulario', async () => {
    const { vista, esperar } = await abrir('/tutor-academico/evaluacion?p=5');
    escribir(vista, '#porcentaje-5', '88');
    pulsar(vista, 'Guardar');
    await esperar();
    expect(textoDe(vista)).toContain('Evaluación final registrada por PAREDES JARAMILLO ROBERTO ANDRÉS el 05/06/2026. Desempeño 88 %: aprobada. La coordinación ya puede cerrar la práctica.');
    expect(vista.querySelector<HTMLButtonElement>('.acciones-fila button')?.disabled).toBe(true);
    expect(vista.querySelector<HTMLInputElement>('#porcentaje-5')?.disabled).toBe(true);
  });

  it('falta el informe externo: avisa y «Guardar» no registra nada', async () => {
    const { vista, esperar } = await abrir('/tutor-academico/evaluacion?p=6');
    const texto = textoDe(vista);
    expect(texto).toContain('Para registrar la evaluación final falta el informe final del estudiante revisado y el informe externo.');
    expect(vista.querySelector<HTMLInputElement>('#porcentaje-6')?.value).toBe('70');
    pulsar(vista, 'Guardar');
    await esperar();
    expect(vista.querySelector('.resumen-error')?.getAttribute('role')).toBe('alert');
    expect(textoDe(vista)).toContain('No se pudo registrar la evaluación. Corrija lo siguiente:');
    expect(textoDe(vista)).toContain('No se puede registrar la evaluación final: falta el informe final del estudiante revisado y el informe externo.');
    expect(textoDe(vista)).not.toContain('Evaluación final registrada');
    expect(vista.querySelector<HTMLButtonElement>('.acciones-fila button')?.disabled).toBe(false);
  });
});
