import { construirCsv } from './csv.util';
import type { FilaConsolidado } from './coordinador.model';
import { abrir, textoDe } from './pruebas';

const FILAS: FilaConsolidado[] = [
  { estudiante: 'AYOVI CANDO MARIA FERNANDA', periodo: 'MAR.26-AGO.26 GRADO', componente: 'comunitaria', horasValidadas: 96, horasRequeridas: 96, resultado: 'no_aprobada', cierre: '2026-06-04' },
  { estudiante: 'CORDOVA, VAZQUEZ "JOSE" LUIS', periodo: 'MAR.26-AGO.26 GRADO', componente: 'laboral', horasValidadas: 160, horasRequeridas: 160, resultado: 'aprobada', cierre: '2026-06-04' },
];

describe('CSV del consolidado', () => {
  it('lleva BOM, encabezado, una línea por fila, fechas ISO y escapa comas y comillas', () => {
    const csv = construirCsv(FILAS);
    expect(csv.charCodeAt(0)).toBe(0xfeff);
    const lineas = csv.slice(1).split('\r\n');
    expect(lineas[0]).toBe('estudiante,periodo,componente,horas_validadas,horas_requeridas,resultado,fecha_cierre');
    expect(lineas[1]).toBe('Ayovi Cando Maria Fernanda,MAR.26-AGO.26 GRADO,Comunitaria,96,96,No aprobada,2026-06-04');
    expect(lineas[2]).toBe('"Cordova, Vazquez ""jose"" Luis",MAR.26-AGO.26 GRADO,Laboral,160,160,Aprobada,2026-06-04');
    expect(lineas[3]).toBe('');
    expect(lineas).toHaveLength(4);
  });

  it('sin filas solo trae el encabezado', () => {
    expect(construirCsv([]).slice(1)).toBe('estudiante,periodo,componente,horas_validadas,horas_requeridas,resultado,fecha_cierre\r\n');
  });
});

describe('Consolidado (C6)', () => {
  it('lista las prácticas cerradas con su resultado y el conteo', async () => {
    const { vista } = await abrir('/coordinador/consolidado');
    const filas = vista.querySelectorAll('tbody tr');
    expect(filas.length).toBeGreaterThan(0);
    expect(textoDe(vista)).toContain(`${filas.length} componentes cerrados.`);
    expect([...vista.querySelectorAll('th')].map((t) => t.textContent)).toContain('Fecha de cierre');
  });

  it('filtra por componente y exporta solo las filas visibles con un Blob real', async () => {
    const { vista, esperar } = await abrir('/coordinador/consolidado');
    const s = vista.querySelector<HTMLSelectElement>('#f-comp')!;
    s.value = 'comunitaria';
    s.dispatchEvent(new Event('change'));
    await esperar();
    const visibles = vista.querySelectorAll('tbody tr').length;
    for (const c of vista.querySelectorAll('tbody tr td:nth-child(3)')) expect(c.textContent).toBe('Comunitaria');

    const blobs: Blob[] = [];
    URL.createObjectURL = (b: Blob | MediaSource) => {
      blobs.push(b as Blob);
      return 'blob:prueba';
    };
    URL.revokeObjectURL = () => undefined;
    const clic = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
    vista.querySelector<HTMLButtonElement>('#csv')!.click();
    await esperar();
    expect(clic).toHaveBeenCalledOnce();
    expect(blobs).toHaveLength(1);
    expect(blobs[0].type).toBe('text/csv;charset=utf-8');
    const bytes = new Uint8Array(await blobs[0].arrayBuffer());
    expect([...bytes.slice(0, 3)]).toEqual([0xef, 0xbb, 0xbf]);
    const texto = new TextDecoder('utf-8', { ignoreBOM: true }).decode(bytes);
    const lineas = texto.slice(1).split('\r\n').filter(Boolean);
    expect(lineas).toHaveLength(visibles + 1);
    expect(lineas[0]).toContain('estudiante,periodo');
    expect(textoDe(vista)).toContain('Archivo generado.');
    clic.mockRestore();
  });

  it('un período sin cierres muestra el estado vacío', async () => {
    const { vista, esperar } = await abrir('/coordinador/consolidado');
    const s = vista.querySelector<HTMLSelectElement>('#f-periodo')!;
    s.value = 'SEP.25-ENE.26 GRADO';
    s.dispatchEvent(new Event('change'));
    await esperar();
    expect(textoDe(vista)).toContain('Sin prácticas cerradas');
    expect(textoDe(vista)).toContain('0 componentes cerrados.');
  });
});
