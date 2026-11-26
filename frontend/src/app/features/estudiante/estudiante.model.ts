import type { Fecha, Practica, ReporteSemanal } from '../../core/demo';

/** Una actividad del plan: qué hará, con qué herramientas y qué entregará. */
export interface ActividadPlan {
  descripcion: string;
  herramientas: string;
  entregable: string;
}

/** Una versión del plan: se devuelve con observación o se aprueba. */
export interface VersionPlan {
  numero: number;
  estado: 'devuelta' | 'aprobada' | 'en_revision';
  enviadaEl: Fecha;
  decididaEl: Fecha | null;
  decididaPor: string;
  observacion: string;
}

/** Plan vigente de la práctica (pestaña «Plan», E2b). */
export interface PlanDetalle {
  practica: Practica;
  version: number;
  estado: 'validado' | 'en_revision' | 'devuelto';
  decididoPor: string;
  decididoEl: Fecha | null;
  actividades: ActividadPlan[];
  versiones: VersionPlan[];
}

/** Lo que necesita el formulario E3 para corregir o registrar el plan. */
export interface PlanEditable {
  practica: Practica;
  /** Versión que se va a enviar. */
  version: number;
  /** Observación de la versión devuelta, si la hay. */
  observacion: { texto: string; autor: string; fecha: Fecha } | null;
  /** Versiones ya enviadas (para el recorrido). */
  versiones: VersionPlan[];
  actividades: ActividadPlan[];
}

export interface EvidenciaReporte {
  nombre: string;
  tamano: string;
  version: number;
}

/** Reporte semanal con todo lo que muestra E5. */
export interface ReporteDetalle {
  practica: Practica;
  reporte: ReporteSemanal;
  evidencias: EvidenciaReporte[];
  /** Nombre del tutor de la entidad que confirma; vacío si no aplica. */
  tutorEntidad: string;
}
