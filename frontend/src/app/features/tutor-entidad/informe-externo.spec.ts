import { abrir, escribir, textoDe } from './pruebas';

function elegirArchivo(vista: HTMLElement, nombre: string, bytes: number, tipo = 'application/pdf'): void {
  const entrada = vista.querySelector<HTMLInputElement>('#archivo')!;
  const archivo = new File(['x'], nombre, { type: tipo });
  Object.defineProperty(archivo, 'size', { value: bytes });
  Object.defineProperty(entrada, 'files', { value: [archivo], configurable: true });
  entrada.dispatchEvent(new Event('change', { bubbles: true }));
}
const guardar = (vista: HTMLElement) => [...vista.querySelectorAll('button')].find((b) => b.textContent?.includes('Guardar'))!.click();
const MB = 1048576;

describe('Informe externo (R4)', () => {
  it('muestra el formulario, el contexto del practicante y las reglas del archivo', async () => {
    const { vista } = await abrir('/tutor-entidad/informe-externo');
    const texto = textoDe(vista);
    expect(texto).toContain('Informe final del tutor de la entidad sobre su practicante (HU-07).');
    expect(texto).toContain('MENDIETA SARANGO LUCIANA BELÉN. Práctica laboral (ayudantía de docencia) en Universidad Nacional de Loja - Carrera de Computación.');
    expect(texto).toContain('Máximo 5 MB por archivo.');
    expect(vista.querySelector('label[for="valoracion"]')).not.toBeNull();
    expect(vista.querySelector('label[for="archivo"]')).not.toBeNull();
  });

  it('con ?p=3 preselecciona a Diego', async () => {
    const { vista } = await abrir('/tutor-entidad/informe-externo?p=3');
    expect(vista.querySelector<HTMLSelectElement>('#practicante')!.value).toBe('3');
    expect(textoDe(vista)).toContain('JIMÉNEZ CASTILLO DIEGO ALEJANDRO. Práctica laboral (ayudantía de investigación)');
  });

  it('exige la valoración y el archivo', async () => {
    const { vista, esperar } = await abrir('/tutor-entidad/informe-externo');
    guardar(vista);
    await esperar();
    const lista = [...vista.querySelectorAll('.resumen-error li')].map((li) => li.textContent);
    expect(lista).toEqual(['Describa la valoración del desempeño.', 'Adjunte el informe firmado en PDF.']);
    expect(textoDe(vista)).not.toContain('Informe externo registrado');
  });

  it('rechaza un archivo que no es PDF', async () => {
    const { vista, esperar } = await abrir('/tutor-entidad/informe-externo');
    escribir(vista.querySelector<HTMLTextAreaElement>('#valoracion')!, 'Cumplió el plan.');
    elegirArchivo(vista, 'informe.docx', 400, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document');
    await esperar();
    guardar(vista);
    await esperar();
    expect(textoDe(vista)).toContain('«informe.docx»: solo se admiten archivos PDF.');
    expect(textoDe(vista)).not.toContain('Informe externo registrado');
  });

  it('rechaza un PDF de más de 5 MB', async () => {
    const { vista, esperar } = await abrir('/tutor-entidad/informe-externo');
    escribir(vista.querySelector<HTMLTextAreaElement>('#valoracion')!, 'Cumplió el plan.');
    elegirArchivo(vista, 'grande.pdf', 7.2 * MB);
    await esperar();
    guardar(vista);
    await esperar();
    expect(textoDe(vista)).toContain('«grande.pdf» pesa 7,2 MB y supera el máximo de 5 MB por archivo.');
    expect(textoDe(vista)).not.toContain('Informe externo registrado');
  });

  it('acepta un PDF válido de hasta 5 MB y registra el informe', async () => {
    const { vista, esperar } = await abrir('/tutor-entidad/informe-externo');
    escribir(vista.querySelector<HTMLTextAreaElement>('#valoracion')!, 'Cumplió el plan.');
    elegirArchivo(vista, 'firmado.pdf', 5 * MB);
    await esperar();
    guardar(vista);
    await esperar();
    const texto = textoDe(vista);
    expect(texto).toContain('Informe externo registrado por CELI ARMIJOS MARTHA CECILIA el 05/06/2026, con el archivo «firmado.pdf». Se avisa al tutor académico.');
    expect(vista.querySelector('.resumen-error')).toBeNull();
  });

  it('los enlaces «Probar archivo» cargan los ejemplos del prototipo', async () => {
    const { vista, esperar } = await abrir('/tutor-entidad/informe-externo');
    escribir(vista.querySelector<HTMLTextAreaElement>('#valoracion')!, 'Cumplió el plan.');
    const enlaces = [...vista.querySelectorAll<HTMLAnchorElement>('.demo-vistas a')];
    expect(enlaces.map((a) => a.textContent)).toEqual(['informe-entidad.pdf (1,2 MB)', 'informe-entidad.docx', 'informe de 7,2 MB']);
    enlaces[2].click();
    await esperar();
    expect(textoDe(vista)).toContain('Seleccionado: informe-entidad.pdf');
    guardar(vista);
    await esperar();
    expect(textoDe(vista)).toContain('«informe-entidad.pdf» pesa 7,2 MB y supera el máximo de 5 MB por archivo.');
    enlaces[0].click();
    await esperar();
    guardar(vista);
    await esperar();
    expect(textoDe(vista)).toContain('Informe externo registrado');
  });
});
