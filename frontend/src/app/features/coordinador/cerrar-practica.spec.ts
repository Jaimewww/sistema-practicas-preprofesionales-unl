import { abrir, textoDe } from './pruebas';

const boton = (vista: HTMLElement) => vista.querySelector<HTMLButtonElement>('#c4-cerrar')!;
async function caso(vista: HTMLElement, esperar: () => Promise<void>, valor: string): Promise<void> {
  const s = vista.querySelector<HTMLSelectElement>('#c4-caso')!;
  s.value = valor;
  s.dispatchEvent(new Event('change'));
  await esperar();
}

describe('Cerrar práctica (C4)', () => {
  it('lista los cuatro requisitos de RF-09 con los datos de la práctica', async () => {
    const { vista } = await abrir('/coordinador/cerrar?p=7');
    const texto = textoDe(vista);
    expect(texto).toContain('Requisitos de cierre (RF-09)');
    expect(texto).toContain('El 100 % de las horas requeridas validadas — Cumplido');
    expect(texto).toContain('La evaluación final registrada con 70 % o más — Cumplido');
    expect(vista.querySelectorAll('.requisitos li')).toHaveLength(4);
  });

  it('con requisitos faltantes «Cerrar» está deshabilitado y se listan los que faltan', async () => {
    const { vista, esperar } = await abrir('/coordinador/cerrar?p=7');
    await caso(vista, esperar, 'falta');
    expect(boton(vista).disabled).toBe(true);
    const texto = textoDe(vista);
    expect(texto).toContain('No se puede cerrar hasta cumplir todos los requisitos.');
    expect(texto).toContain('sin informe externo registrado');
    expect(vista.querySelectorAll('#c4-faltan li')).toHaveLength(4);
    expect(vista.querySelector('#c4-conf')).toBeNull();
  });

  it('con todos los requisitos habilita «Cerrar», exige confirmar y muestra el éxito', async () => {
    const { vista, esperar } = await abrir('/coordinador/cerrar?p=1');
    expect(boton(vista).disabled).toBe(true);
    await caso(vista, esperar, 'completo');
    expect(boton(vista).disabled).toBe(false);
    expect(textoDe(vista)).toContain('Todos los requisitos se cumplen.');
    boton(vista).click();
    await esperar();
    expect(textoDe(vista)).toContain('Debe confirmar el cierre.');
    vista.querySelector<HTMLInputElement>('#c4-conf')!.click();
    await esperar();
    boton(vista).click();
    await esperar();
    await esperar();
    const texto = textoDe(vista);
    expect(texto).toContain('Práctica cerrada.');
    expect(texto).toContain('quedó en estado «Cerrada (aprobada)»');
    expect(vista.querySelector('#c4-cerrar')).toBeNull();
  });
});
