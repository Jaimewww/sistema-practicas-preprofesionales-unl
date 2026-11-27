import type { AlertaPractica, AvanceHoras, ConfiguracionCarrera, EntradaHistorial, EstadoPractica, Practica, ResultadoPractica, TipoAlerta, TipoPractica } from '../../core/demo';

/** Una fila de «Prácticas de la carrera» (C1): la práctica con su avance y sus alertas activas. */
export interface FilaPractica {
  practica: Practica;
  avance: AvanceHoras;
  alertas: AlertaPractica[];
}

/** Una alerta activa con el contexto que pinta C2. */
export interface FilaAlerta {
  alerta: AlertaPractica;
  estudiante: string;
  tipoPractica: TipoPractica;
  tutorAcademico: string;
}

export interface CantidadPorEstado {
  estado: EstadoPractica;
  cantidad: number;
}

export interface CantidadPorAlerta {
  tipo: TipoAlerta;
  cantidad: number;
}

/** Todo lo que muestra el tablero del coordinador (C0). */
export interface ResumenCarrera {
  periodo: string;
  total: number;
  enCurso: number;
  rezagadas: number;
  alertasActivas: number;
  porEstado: CantidadPorEstado[];
  porAlerta: CantidadPorAlerta[];
  /** En revisión final (cerrar) y suspendidas (reanudar o cancelar). */
  decisiones: Practica[];
}

/** Detalle de una práctica para C3, C4 y C5. */
export interface DetallePractica {
  practica: Practica;
  alertas: AlertaPractica[];
  historial: EntradaHistorial[];
}

/** Una fila del consolidado (C6): una práctica cerrada. */
export interface FilaConsolidado {
  estudiante: string;
  periodo: string;
  componente: TipoPractica;
  horasValidadas: number;
  horasRequeridas: number;
  resultado: ResultadoPractica | '';
  /** Fecha ISO `AAAA-MM-DD` (vacía si no consta). */
  cierre: string;
}

export type { ConfiguracionCarrera };
