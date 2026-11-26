import { CANTIDAD_PRACTICAS_CARRERA, CARRERA, CARRERAS_OTRAS, CONFIGURACION_CARRERA, PERIODO, PERIODO_ANTERIOR, TOTAL_SEMANAS } from './constantes';
import { fecha } from './fechas';
import type { Fecha } from './fechas';
import type { EstadoPractica, InformeExterno, Practica, ReporteSemanal, TipoPractica } from './modelos';
import { nombreEstudiante, TUTORES_CARRERA, TUTORES_ENTIDAD } from './personas';
import { crearPractica, PRACTICAS_DE_EJEMPLO } from './practicas';
import { informeFinal, plan, reporte, validado } from './reportes';

const ENTIDADES = [
  'Soluciones Informáticas del Sur Cía. Ltda.',
  'Agroindustrias del Norte Cía. Ltda.',
  'Cooperativa de Cafetaleros de Loja',
  'Museo Provincial de Loja',
  'Fundación Provincial de Alfabetización',
];

const PROYECTOS = [
  'Alfabetización digital para adultos mayores del cantón Loja',
  'Sitio web informativo para el GAD parroquial de Vilcabamba',
  'Capacitación en herramientas digitales para productores',
  'Recuperación de áreas verdes en el barrio Lapapaya',
];

/** Estados repartidos entre las prácticas de ejemplo para que filtros y alertas tengan de todo. */
const ESTADOS: readonly EstadoPractica[] = ['en_curso', 'en_curso', 'en_revision_final', 'asignada', 'suspendida', 'en_curso', 'en_revision_final', 'cancelada', 'en_curso', 'cerrada'];

/** (estudiante, tipo) por práctica: los primeros 54 estudiantes tienen laboral y comunitaria (Art. 334). */
function componentes(cantidad: number): Array<[string, TipoPractica]> {
  const lista: Array<[string, TipoPractica]> = [];
  for (let i = 0; lista.length < cantidad; i++) {
    const tipos: TipoPractica[] = i < 54 ? ['laboral', 'comunitaria'] : [i % 2 === 0 ? 'laboral' : 'comunitaria'];
    for (const tipo of tipos) if (lista.length < cantidad) lista.push([nombreEstudiante(i), tipo]);
  }
  return lista;
}

const semanaDe = (estado: EstadoPractica, i: number): number =>
  estado === 'cerrada' || estado === 'en_revision_final' ? 8 : estado === 'asignada' ? 1 + (i % 4) : 2 + (i % 7);

function reportesDe(estado: EstadoPractica, horas: number, semanaActual: number, i: number): ReporteSemanal[] {
  if (estado === 'asignada') return [];
  if (estado === 'cerrada') return Array.from({ length: 8 }, (_, k) => validado(k + 1, horas, { confirmadoPorEntidad: true }));
  const sinReporte = (estado === 'en_curso' || estado === 'suspendida' || estado === 'cancelada') && i % 3 === 0;
  const enRevision = (estado === 'en_curso' || estado === 'en_revision_final') && i % 3 === 1;
  const lista: ReporteSemanal[] = [];
  for (let semana = 1; semana <= semanaActual; semana++) {
    if (semana === semanaActual && sinReporte) lista.push(reporte(semana, 0, 'sin_reporte'));
    else if (semana === semanaActual && enRevision) lista.push(reporte(semana, horas, 'en_revision'));
    else lista.push(validado(semana, horas, { confirmadoPorEntidad: true }));
  }
  return lista;
}

function sintetica(i: number, estudiante: string, tipo: TipoPractica, carrera: string, periodo: string, idBase: number): Practica {
  const estado = ESTADOS[i % ESTADOS.length];
  const requeridas = tipo === 'laboral' ? CONFIGURACION_CARRERA.horasLaboral : CONFIGURACION_CARRERA.horasComunitaria;
  const horasSemana = Math.floor(requeridas / (estado === 'cerrada' || estado === 'en_revision_final' ? 8 : TOTAL_SEMANAS));
  const semanaActual = semanaDe(estado, i);
  const tutorAcademico = TUTORES_CARRERA[i % TUTORES_CARRERA.length];
  const tutorEntidad = tipo === 'laboral' ? TUTORES_ENTIDAD[i % TUTORES_ENTIDAD.length] : '';
  const datos: Partial<Practica> = {
    carrera,
    periodo,
    tutorAcademico,
    semanaActual,
    horasRequeridas: requeridas,
    subtipo: tipo === 'laboral' ? 'pasantia' : '',
    entidad: tipo === 'laboral' ? ENTIDADES[i % ENTIDADES.length] : '',
    tutorEntidad,
    proyectoVinculacion: tipo === 'laboral' ? '' : PROYECTOS[i % PROYECTOS.length],
    plan: plan(estado === 'asignada' ? 'en_revision' : 'validado', [1, 2, 3].map((n) => `Actividad ${n} del plan de ${tipo}.`), fecha(2026, 4, 9), tutorAcademico),
  };
  const id = idBase + i;
  const validadoInforme = (enviado: Fecha) => informeFinal('validado', enviado, `informe-final-${id}.pdf`, { validadoPor: tutorAcademico, validadoEl: fecha(2026, 6, 3) });
  if (estado === 'en_revision_final') {
    datos.informeFinal = validadoInforme(fecha(2026, 6, 1));
    if (tipo === 'laboral') {
      datos.informeExterno = { registradoPor: tutorEntidad, registradoEl: fecha(2026, 6, 2), valoracion: 'Cumplió las actividades del plan de la práctica.', archivo: `informe-entidad-${id}.pdf` };
    }
  }
  if (estado === 'cerrada') {
    datos.informeFinal = validadoInforme(fecha(2026, 6, 3));
    const ext: InformeExterno = { registradoPor: tutorEntidad || 'PROYECTO DE VINCULACIÓN', registradoEl: fecha(2026, 6, 3), valoracion: 'Cumplimiento satisfactorio del plan de actividades.', archivo: `informe-externo-${id}.pdf` };
    datos.informeExterno = ext;
    const resultado = i % 4 === 3 ? 'no_aprobada' : 'aprobada';
    datos.evaluacion = { porcentaje: resultado === 'no_aprobada' ? 64 : 88, resultado, registradoPor: tutorAcademico, registradoEl: fecha(2026, 6, 3) };
    datos.resultado = resultado;
  }
  return crearPractica(id, estudiante, tipo, estado, reportesDe(estado, horasSemana, semanaActual, i), datos);
}

const sinteticas = (carrera: string, periodo: string, lista: Array<[string, TipoPractica]>, idBase: number): Practica[] =>
  lista.map(([estudiante, tipo], i) => sintetica(i, estudiante, tipo, carrera, periodo, idBase));

/** C1: las 150 prácticas de la carrera del coordinador (las 10 de ejemplo y el resto sintéticas). */
export const PRACTICAS_CARRERA: readonly Practica[] = [
  ...PRACTICAS_DE_EJEMPLO.filter((p) => p.carrera === CARRERA),
  ...sinteticas(CARRERA, PERIODO, componentes(CANTIDAD_PRACTICAS_CARRERA - PRACTICAS_DE_EJEMPLO.length), 100),
];

/** Prácticas de otras carreras: el coordinador no puede verlas (RF-11). */
export const PRACTICAS_OTRAS_CARRERAS: readonly Practica[] = CARRERAS_OTRAS.flatMap((carrera, i) =>
  sinteticas(carrera, i === 0 ? PERIODO : PERIODO_ANTERIOR, componentes(20), 1000 + i * 20),
);

/** A1: todas las prácticas de todas las carreras. */
export const PRACTICAS_TODAS: readonly Practica[] = [...PRACTICAS_CARRERA, ...PRACTICAS_OTRAS_CARRERAS];
