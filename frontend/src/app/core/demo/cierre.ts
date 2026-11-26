import { formatoFecha } from './fechas';
import { avanceDe } from './horas';
import type { EntradaHistorial, Practica } from './modelos';

export interface RequisitoCierre {
  clave: 'horas' | 'informe_final' | 'informe_externo' | 'evaluacion';
  requisito: string;
  cumplido: boolean;
  detalle: string;
  nota?: string;
}

/** Los requisitos de RF-09/COR-02 para cerrar una práctica y si cada uno se cumple. */
export function requisitosCierre(p: Practica): RequisitoCierre[] {
  const laboral = p.tipo === 'laboral';
  const { validadas } = avanceDe(p);
  const final = p.informeFinal;
  const ext = p.informeExterno;
  const ev = p.evaluacion;
  const finalOk = !!final && final.estado === 'validado';
  return [
    {
      clave: 'horas',
      requisito: 'El 100 % de las horas requeridas validadas',
      cumplido: validadas >= p.horasRequeridas,
      detalle: `${validadas} h validadas de ${p.horasRequeridas} h requeridas`,
    },
    {
      clave: 'informe_final',
      requisito: 'El informe final del estudiante revisado',
      cumplido: finalOk,
      detalle: finalOk && final.validadoEl ? `${final.archivo}, revisado el ${formatoFecha(final.validadoEl)}` : 'sin informe final revisado',
    },
    {
      clave: 'informe_externo',
      requisito: laboral ? 'El informe externo del tutor de la entidad' : 'El informe del proyecto de vinculación',
      cumplido: !!ext,
      detalle: ext ? `registrado por ${ext.registradoPor} el ${formatoFecha(ext.registradoEl)}` : 'sin informe externo registrado',
      nota: laboral ? '' : 'El actor que registra este informe está por definir (spec, sección 6).',
    },
    {
      clave: 'evaluacion',
      requisito: 'La evaluación final registrada',
      cumplido: !!ev,
      detalle: ev ? `${ev.porcentaje} % — ${ev.resultado === 'aprobada' ? 'Aprobada' : 'No aprobada'}` : 'sin evaluación final registrada',
    },
  ];
}

/** Lo que le falta a la práctica para poder cerrarse (CE-05). */
export const faltantesCierre = (p: Practica): string[] => requisitosCierre(p).filter((r) => !r.cumplido).map((r) => r.requisito);

/** Fecha del último cambio de estado a «cerrada», si la práctica se cerró. */
export function fechaCierre(p: Practica): string | null {
  const entrada: EntradaHistorial | undefined = [...p.historial].reverse().find((e) => e.estadoNuevo === 'cerrada');
  return entrada?.fecha ?? null;
}
