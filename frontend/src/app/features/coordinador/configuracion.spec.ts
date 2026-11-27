import { abrir, textoDe } from './pruebas';

const entrada = (vista: HTMLElement, campo: string) => vista.querySelector<HTMLInputElement>(`#c7-${campo}`)!;
async function poner(vista: HTMLElement, esperar: () => Promise<void>, campo: string, valor: number): Promise<void> {
  const i = entrada(vista, campo);
  i.value = String(valor);
  i.dispatchEvent(new Event('input'));
  await esperar();
}
const guardar = (vista: HTMLElement) => vista.querySelector<HTMLButtonElement>('#c7-guardar')!.click();

describe('Configuración (C7)', () => {
  it('muestra los valores de la carrera en contadores etiquetados', async () => {
    const { vista } = await abrir('/coordinador/configuracion');
    expect(entrada(vista, 'horasLaboral').value).toBe('160');
    expect(entrada(vista, 'horasComunitariaDistancia').value).toBe('144');
    expect(entrada(vista, 'plazoRevisionDias').value).toBe('5');
    expect(entrada(vista, 'umbralRezago').value).toBe('80');
    expect(vista.querySelectorAll('app-contador')).toHaveLength(7);
    expect(vista.querySelector('label[for="c7-umbralRezago"]')?.textContent).toBe('Umbral de rezago (%)');
    expect(textoDe(vista)).toContain('Las horas nuevas se aplicarán a futuras asignaciones');
  });

  it('rechaza un umbral de 0 y no guarda', async () => {
    const { vista, esperar } = await abrir('/coordinador/configuracion');
    await poner(vista, esperar, 'umbralRezago', 0);
    guardar(vista);
    await esperar();
    const texto = textoDe(vista);
    expect(texto).toContain('No se pudo guardar la configuración:');
    expect(texto).toContain('El umbral debe estar entre 1 y 100 %.');
    expect(texto).not.toContain('Configuración guardada.');
  });

  it('rechaza horas a distancia menores que las presenciales', async () => {
    const { vista, esperar } = await abrir('/coordinador/configuracion');
    await poner(vista, esperar, 'horasLaboralDistancia', 100);
    guardar(vista);
    await esperar();
    expect(textoDe(vista)).toContain('Las horas a distancia no pueden ser menores que las presenciales.');
  });

  it('acepta valores válidos y muestra el aviso de éxito', async () => {
    const { vista, esperar } = await abrir('/coordinador/configuracion');
    await poner(vista, esperar, 'umbralRezago', 70);
    await poner(vista, esperar, 'plazoRevisionDias', 7);
    guardar(vista);
    await esperar();
    await esperar();
    const texto = textoDe(vista);
    expect(texto).toContain('Configuración guardada.');
    expect(texto).not.toContain('No se pudo guardar');
  });

  it('«Restablecer valores» vuelve a los valores de la carrera', async () => {
    const { vista, esperar } = await abrir('/coordinador/configuracion');
    await poner(vista, esperar, 'umbralRezago', 0);
    guardar(vista);
    await esperar();
    vista.querySelector<HTMLButtonElement>('#c7-restablecer')!.click();
    await esperar();
    expect(entrada(vista, 'umbralRezago').value).toBe('80');
    expect(textoDe(vista)).not.toContain('No se pudo guardar');
  });
});
