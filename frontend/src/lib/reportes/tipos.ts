/**
 * Tipos del reporte semanal, tomados de ReporteSemanalSerializer y del
 * esquema OpenAPI (GET /api/v1/schema/). Si el contrato cambia, se cambia acá.
 */

/** Cuerpo de POST /practicas/{practica_id}/reportes/. Solo estos dos campos: cualquier otro es 400. */
export interface ReporteCrear {
  semana: number;
  /** Entre 1 y 168; en ayudantías, máximo 10 (Art. 341). */
  horas_reportadas: number;
}

export type EstadoReporte = 'en_revision' | 'validado' | 'devuelto';

/** Respuesta 201: los campos de solo lectura los fija el servidor. */
export interface Reporte extends ReporteCrear {
  id: number;
  practica_id: number;
  estado: EstadoReporte;
  requiere_revision: boolean;
  fecha_registro: string;
}

/** GET /practicas/{practica_id}/horas/ (HorasPracticaSerializer). */
export interface HorasPractica {
  horas_validadas: number;
  horas_en_revision: number;
  horas_requeridas: number;
  horas_faltantes: number;
  semana_en_revision: boolean;
}

/** Lo que el componente necesita del servicio; la versión real y el mock lo cumplen. */
export interface ReportesApi {
  crear(practicaId: number, cuerpo: ReporteCrear): Promise<Reporte>;
  horas(practicaId: number): Promise<HorasPractica>;
}
