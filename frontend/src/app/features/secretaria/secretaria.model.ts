import type { Anexo, Practica } from '../../core/demo';

/** Un anexo de cierre con la práctica a la que pertenece. */
export interface FilaAnexo {
  anexo: Anexo;
  practica: Practica;
}

/** Cifras del tablero de Secretaría. */
export interface ResumenSecretaria {
  porLegalizar: number;
  legalizados: number;
  practicasConAnexos: number;
  /** Los primeros anexos pendientes. */
  siguientes: FilaAnexo[];
}
