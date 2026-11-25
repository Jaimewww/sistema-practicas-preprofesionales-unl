/** Tarjeta de práctica (PracticaCardSerializer): GET /practicas/ y GET /practicas/{id}/. */
export interface Practica {
  id: number;
  estudiante_id: number;
  tipo: string;
  subtipo: string;
  estado: string;
  horas_requeridas: number;
}

export interface PracticasApi {
  /** Lista vacía = estado «vacío», no error. */
  listar(): Promise<Practica[]>;
}
