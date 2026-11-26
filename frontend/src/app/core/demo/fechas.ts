/** Fecha de calendario como texto ISO `AAAA-MM-DD` (sin hora ni zona: así se ordena y se compara). */
export type Fecha = string;

const MS_DIA = 86_400_000;

const aMs = (f: Fecha): number => {
  const [a, m, d] = f.split('-').map(Number);
  return Date.UTC(a, m - 1, d);
};
const deMs = (ms: number): Fecha => new Date(ms).toISOString().slice(0, 10);

export const fecha = (anio: number, mes: number, dia: number): Fecha => deMs(Date.UTC(anio, mes - 1, dia));

export const sumarDias = (f: Fecha, dias: number): Fecha => deMs(aMs(f) + dias * MS_DIA);

/** Días de calendario de `desde` a `hasta` (negativo si `hasta` es anterior). */
export const diasEntre = (desde: Fecha, hasta: Fecha): number => Math.round((aMs(hasta) - aMs(desde)) / MS_DIA);

/** 0 = domingo … 6 = sábado. */
const diaSemana = (f: Fecha): number => new Date(aMs(f)).getUTCDay();

/** Días hábiles (lunes a viernes) después de `desde` hasta `hasta` inclusive. */
export function diasHabilesEntre(desde: Fecha, hasta: Fecha): number {
  let total = 0;
  for (let n = 1; n <= diasEntre(desde, hasta); n++) {
    const d = diaSemana(sumarDias(desde, n));
    if (d !== 0 && d !== 6) total++;
  }
  return total;
}

/** La fecha que queda tras sumar `cantidad` días hábiles a `desde`. */
export function sumarDiasHabiles(desde: Fecha, cantidad: number): Fecha {
  let f = desde;
  let falta = cantidad;
  while (falta > 0) {
    f = sumarDias(f, 1);
    const d = diaSemana(f);
    if (d !== 0 && d !== 6) falta--;
  }
  return f;
}

/** `dd/MM/aaaa`, el formato de los prototipos. */
export const formatoFecha = (f: Fecha): string => f.split('-').reverse().join('/');
