import { avanceDe, formatoFecha } from '../../core/demo';
import type { Practica } from '../../core/demo';

export type CasoCierre = 'real' | 'completo' | 'falta';

/** Lo que se evalúa para cerrar: los datos reales de la práctica o un caso simulado de la demostración. */
export interface DatosCierre {
  horas: number;
  informe: 'validado' | 'en_revision' | null;
  informeFecha: string;
  externo: boolean;
  externoFecha: string;
  evaluacion: number | null;
}

export interface Requisito {
  clave: 'horas' | 'informe_final' | 'informe_externo' | 'evaluacion';
  titulo: string;
  cumplido: boolean;
  detalle: string;
}

/** Evaluación mínima para aprobar (RF-09). */
export const MINIMO_EVALUACION = 70;

export function datosDeCierre(p: Practica, caso: CasoCierre): DatosCierre {
  if (caso === 'completo') return { horas: p.horasRequeridas, informe: 'validado', informeFecha: '03/06/2026', externo: true, externoFecha: '02/06/2026', evaluacion: 88 };
  if (caso === 'falta') return { horas: Math.max(p.horasRequeridas - 20, 0), informe: 'en_revision', informeFecha: '', externo: false, externoFecha: '', evaluacion: null };
  return {
    horas: avanceDe(p).validadas,
    informe: p.informeFinal?.estado === 'validado' || p.informeFinal?.estado === 'en_revision' ? p.informeFinal.estado : null,
    informeFecha: p.informeFinal?.validadoEl ? formatoFecha(p.informeFinal.validadoEl) : '',
    externo: !!p.informeExterno,
    externoFecha: p.informeExterno ? formatoFecha(p.informeExterno.registradoEl) : '',
    evaluacion: p.evaluacion?.porcentaje ?? null,
  };
}

/** Los cuatro requisitos de RF-09 y si cada uno se cumple. */
export function requisitos(p: Practica, d: DatosCierre): Requisito[] {
  const faltan = p.horasRequeridas - d.horas;
  const ev = d.evaluacion;
  return [
    {
      clave: 'horas',
      titulo: 'El 100 % de las horas requeridas validadas',
      cumplido: d.horas >= p.horasRequeridas,
      detalle: `${d.horas} h validadas de ${p.horasRequeridas} h requeridas${faltan > 0 ? ` · faltan ${faltan} h` : ''}`,
    },
    {
      clave: 'informe_final',
      titulo: 'El informe final del estudiante revisado',
      cumplido: d.informe === 'validado',
      detalle: d.informe === 'validado' ? `informe final revisado${d.informeFecha ? ` el ${d.informeFecha}` : ''}` : d.informe === 'en_revision' ? 'el informe final sigue en revisión' : 'sin informe final revisado',
    },
    {
      clave: 'informe_externo',
      titulo: p.tipo === 'laboral' ? 'El informe externo del tutor de la entidad' : 'El informe del proyecto de vinculación',
      cumplido: d.externo,
      detalle: d.externo ? `registrado${d.externoFecha ? ` el ${d.externoFecha}` : ''}` : 'sin informe externo registrado',
    },
    {
      clave: 'evaluacion',
      titulo: `La evaluación final registrada con ${MINIMO_EVALUACION} % o más`,
      cumplido: ev !== null && ev >= MINIMO_EVALUACION,
      detalle: ev === null ? 'sin evaluación final registrada' : `${ev} % — ${ev >= MINIMO_EVALUACION ? 'Aprobada' : `por debajo del ${MINIMO_EVALUACION} %`}`,
    },
  ];
}
