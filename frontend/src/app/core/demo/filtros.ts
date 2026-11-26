import type { EstadoPractica, Practica, TipoAlerta, TipoPractica } from './modelos';
import { alertasDe } from './alertas';

export interface FiltroPracticas {
  periodo?: string;
  tipo?: TipoPractica;
  estado?: EstadoPractica;
  alerta?: TipoAlerta;
  /** Texto dentro del nombre del estudiante, sin importar mayúsculas. */
  busqueda?: string;
}

/** Filtros de C1: periodo, tipo, estado, alerta y búsqueda por estudiante. */
export function filtrarPracticas(practicas: readonly Practica[], f: FiltroPracticas): Practica[] {
  const texto = f.busqueda?.trim().toUpperCase();
  return practicas.filter(
    (p) =>
      (!f.periodo || p.periodo === f.periodo) &&
      (!f.tipo || p.tipo === f.tipo) &&
      (!f.estado || p.estado === f.estado) &&
      (!f.alerta || alertasDe(p).some((a) => a.tipo === f.alerta)) &&
      (!texto || p.estudiante.toUpperCase().includes(texto)),
  );
}

/** Periodos presentes en las prácticas, del más reciente al más viejo (por texto). */
export const periodosDe = (practicas: readonly Practica[]): string[] => [...new Set(practicas.map((p) => p.periodo))].sort().reverse();
