import { abrir, textoDe } from './pruebas';

const enviar = (vista: HTMLElement) => vista.querySelector<HTMLButtonElement>('#c5-enviar')!;
async function escribir(vista: HTMLElement, esperar: () => Promise<void>, texto: string): Promise<void> {
  const t = vista.querySelector<HTMLTextAreaElement>('#c5-motivo')!;
  t.value = texto;
  t.dispatchEvent(new Event('input'));
  await esperar();
}

describe('Suspender o cancelar (C5)', () => {
  it('con el motivo vacío muestra el error y no cambia la práctica', async () => {
    const { vista, esperar } = await abrir('/coordinador/suspender-cancelar?p=1&accion=suspender');
    expect(enviar(vista).textContent?.trim()).toBe('Suspender práctica');
    enviar(vista).click();
    await esperar();
    expect(vista.querySelector('#c5-err')?.textContent?.trim()).toBe('Escriba el motivo de la decisión.');
    expect(textoDe(vista)).not.toContain('Práctica suspendida.');
    await escribir(vista, esperar, '   ');
    enviar(vista).click();
    await esperar();
    expect(vista.querySelector('#c5-err')?.textContent?.trim()).toBe('Escriba el motivo de la decisión.');
  });

  it('con motivo suspende la práctica en curso, cuenta caracteres y muestra el éxito', async () => {
    const { vista, esperar } = await abrir('/coordinador/suspender-cancelar?p=1&accion=suspender');
    await escribir(vista, esperar, 'Licencia médica');
    expect(vista.querySelector('#c5-cont')?.textContent).toBe('15');
    enviar(vista).click();
    await esperar();
    await esperar();
    const texto = textoDe(vista);
    expect(texto).toContain('Práctica suspendida.');
    expect(texto).toContain('quedó en estado «Suspendida». El motivo se guardó en el historial.');
  });

  it('solo se suspende una práctica en curso: en otro estado avisa y bloquea el botón', async () => {
    const { vista } = await abrir('/coordinador/suspender-cancelar?p=7&accion=suspender');
    expect(textoDe(vista)).toContain('No se puede aplicar esta decisión: solo se suspende una práctica en curso.');
    expect(enviar(vista).disabled).toBe(true);
  });

  it('solo se cancela una práctica suspendida', async () => {
    const en = await abrir('/coordinador/suspender-cancelar?p=1&accion=cancelar');
    expect(textoDe(en.vista)).toContain('solo se cancela una práctica suspendida.');
    expect(enviar(en.vista).disabled).toBe(true);
  });

  it('una práctica suspendida se cancela con motivo', async () => {
    const { vista, esperar } = await abrir('/coordinador/suspender-cancelar?p=104&accion=cancelar');
    expect(enviar(vista).disabled).toBe(false);
    await escribir(vista, esperar, 'La práctica se abandonó.');
    enviar(vista).click();
    await esperar();
    await esperar();
    expect(textoDe(vista)).toContain('Práctica cancelada.');
  });
});
