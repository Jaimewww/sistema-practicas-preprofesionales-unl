import type { FilaConsolidado } from './coordinador.model';
import { nombrePropio } from './coordinador.util';

export const ENCABEZADO_CSV = ['estudiante', 'periodo', 'componente', 'horas_validadas', 'horas_requeridas', 'resultado', 'fecha_cierre'] as const;

/** Entrecomilla lo que lleva coma, comillas, punto y coma o salto de línea. */
const celda = (valor: string | number): string => {
  const texto = String(valor);
  return /[",;\r\n]/.test(texto) ? `"${texto.replace(/"/g, '""')}"` : texto;
};

export const textoResultado = (f: Pick<FilaConsolidado, 'resultado'>): string => (f.resultado === 'aprobada' ? 'Aprobada' : f.resultado === 'no_aprobada' ? 'No aprobada' : '');
export const textoComponente = (f: Pick<FilaConsolidado, 'componente'>): string => (f.componente === 'laboral' ? 'Laboral' : 'Comunitaria');

/** CSV UTF-8 con BOM (para que Excel respete los acentos), fechas ISO 8601 y una fila por práctica visible. */
export function construirCsv(filas: readonly FilaConsolidado[]): string {
  const lineas = [
    ENCABEZADO_CSV.join(','),
    ...filas.map((f) => [nombrePropio(f.estudiante), f.periodo, textoComponente(f), f.horasValidadas, f.horasRequeridas, textoResultado(f), f.cierre].map(celda).join(',')),
  ];
  return '\ufeff' + lineas.join('\r\n') + '\r\n';
}

/** Descarga el CSV con un enlace temporal sobre un `Blob`. */
export function descargarCsv(nombre: string, contenido: string): void {
  const blob = new Blob([contenido], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const enlace = document.createElement('a');
  enlace.href = url;
  enlace.download = nombre;
  document.body.appendChild(enlace);
  enlace.click();
  document.body.removeChild(enlace);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
