import { Injectable, inject } from '@angular/core';
import type { Observable } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';

/**
 * Adaptador HTTP del plan de actividades (C-09) y del informe final del estudiante
 * (C-10). Solo habla con el API real: no cae al demo ni inventa respuestas.
 *
 * Contrato verificado en el backend (no en el prototipo):
 *   GET  /practicas/{id}/plan/          -> 200 `PlanActividadesSerializer[]`
 *   POST /practicas/{id}/plan/          {contenido} -> 201 `PlanActividadesSerializer`
 *   GET  /practicas/{id}/informe-final/ -> 200 detalle de la última versión, 404 si no hay
 *   POST /practicas/{id}/informe-final/ multipart `archivo` -> 201 `InformeEstudiante`
 *
 * `ApiClient` arma la URL del environment y desenvuelve `data`; `apiErrorInterceptor`
 * convierte 400/401/403/404/409 en `ApiError`, así que la ausencia de informe llega
 * como `ApiError(404, 'no_encontrado')` y nunca como un detalle fabricado.
 *
 * El plan guarda un único `contenido` de texto: se lee y se escribe tal cual, sin
 * trocearlo en actividades ni sintetizar herramientas o entregables. El informe final
 * del estudiante es un PDF (ADR 0005, ≤ 5 MB) y la corrección tras una devolución es
 * el mismo POST, que crea la versión siguiente: no hay endpoint aparte.
 */
@Injectable()
export class PlanInformeHttp {
  private readonly api = inject(ApiClient);

  /** Versiones del plan de la práctica, de la más nueva a la más antigua; `[]` si aún no hay. */
  versiones(practicaId: number): Observable<PlanVersion[]> {
    return this.api.get<PlanVersion[]>(`/practicas/${practicaId}/plan/`);
  }

  /** Envía el plan (o, tras una devolución, la versión siguiente) con solo `contenido`. */
  enviarPlan(practicaId: number, contenido: string): Observable<PlanVersion> {
    return this.api.post<PlanVersion>(`/practicas/${practicaId}/plan/`, { contenido });
  }

  /** Última versión del informe con su devolución; un 404 significa que todavía no hay. */
  informeFinal(practicaId: number): Observable<InformeFinalEstudianteDetalle> {
    return this.api.get<InformeFinalEstudianteDetalle>(`/practicas/${practicaId}/informe-final/`);
  }

  /**
   * Presenta el PDF del informe final. FormData solo con `archivo`: Angular no fija
   * `Content-Type` y el navegador pone el borde multipart que exige el serializer.
   */
  presentarInformeFinal(practicaId: number, archivo: File): Observable<InformeFinalEstudiante> {
    const cuerpo = new FormData();
    cuerpo.append('archivo', archivo);
    return this.api.post<InformeFinalEstudiante>(`/practicas/${practicaId}/informe-final/`, cuerpo);
  }
}

/** Estados de una versión del plan (`PlanActividades.Estado`). */
export type EstadoPlan = 'en_revision' | 'aprobado' | 'devuelto';

/** `PlanActividadesSerializer`: versión del plan y la última decisión, si la hay. */
export interface PlanVersion {
  id: number;
  practica_id: number;
  version: number;
  /** Texto heredado del plan; se conserva tal cual, sin estructura inventada. */
  contenido: string;
  estado: EstadoPlan;
  /** Observación de la última devolución; `null` si el tutor aún no decidió. */
  observacion: string | null;
  /** Fecha de esa decisión (ISO 8601); `null` si aún no la hay. */
  fecha_validacion: string | null;
}

/** Estados del informe final del estudiante (`InformeEstudiante.Estado`). */
export type EstadoInformeEstudiante = 'en_revision' | 'validado' | 'devuelto';

/** `InformeEstudianteSerializer`: respuesta 201 del POST, sin URL de descarga. */
export interface InformeFinalEstudiante {
  id: number;
  practica_id: number;
  version: number;
  estado: EstadoInformeEstudiante;
  fecha: string;
}

/** `DevolucionSerializer`: lo que el estudiante necesita para corregir. */
export interface DevolucionInformeEstudiante {
  observacion: string;
  autor_id: number;
  fecha: string;
}

/** `InformeEstudianteDetalleSerializer`: última versión leída con su devolución. */
export interface InformeFinalEstudianteDetalle {
  id: number;
  version: number;
  estado: EstadoInformeEstudiante;
  fecha: string;
  devolucion: DevolucionInformeEstudiante | null;
}
