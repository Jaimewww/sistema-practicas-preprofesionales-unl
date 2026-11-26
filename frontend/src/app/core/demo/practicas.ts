import { CARRERA, ESTADO_ANEXO, ESTADO_PRACTICA, PERIODO, RESULTADO_PRACTICA, TOTAL_SEMANAS } from './constantes';
import { fecha } from './fechas';
import type { Fecha } from './fechas';
import type { Anexo, EntradaHistorial, EstadoPractica, Evaluacion, InformeExterno, InformeFinal, Practica, ReporteSemanal, TipoPractica } from './modelos';
import { COORDINADOR, ESTUDIANTE, SECRETARIA, TUTOR_ACADEMICO, TUTOR_CARRERA, TUTOR_COMUNITARIA, TUTOR_ENTIDAD, TUTOR_ENTIDAD_SUR } from './personas';
import { informeFinal, plan, reporte, validado } from './reportes';

export const ENTIDAD_UNL = 'Universidad Nacional de Loja - Carrera de Computación';
export const ENTIDAD_SUR = 'Soluciones Informáticas del Sur Cía. Ltda.';
export const ENTIDAD_NORTE = 'Agroindustrias del Norte Cía. Ltda.';

const historialInicial = (p: Practica): EntradaHistorial[] => {
  const entrada = (anterior: EstadoPractica | '', nuevo: EstadoPractica, f: Fecha, motivo = ''): EntradaHistorial => ({
    estadoAnterior: anterior,
    estadoNuevo: nuevo,
    autor: nuevo === 'suspendida' || nuevo === 'cancelada' || nuevo === 'cerrada' ? COORDINADOR : p.tutorAcademico,
    fecha: f,
    motivo,
  });
  const lista: EntradaHistorial[] = [{ estadoAnterior: '', estadoNuevo: 'asignada', autor: 'SISTEMA', fecha: fecha(2026, 4, 6), motivo: '' }];
  if (p.estado !== 'asignada') lista.push(entrada('asignada', 'en_curso', fecha(2026, 4, 10)));
  if (p.estado === 'en_revision_final' || p.estado === 'cerrada') lista.push(entrada('en_curso', 'en_revision_final', fecha(2026, 6, 3)));
  if (p.estado === 'suspendida' || p.estado === 'cancelada') {
    lista.push(entrada('en_curso', 'suspendida', fecha(2026, 5, 20), 'La entidad receptora informó que la persona practicante cumplió un período de licencia.'));
  }
  if (p.estado === 'cancelada') lista.push(entrada('suspendida', 'cancelada', fecha(2026, 5, 28), 'La práctica se abandonó.'));
  if (p.estado === 'cerrada') lista.push(entrada('en_revision_final', 'cerrada', fecha(2026, 6, 4), 'Práctica cerrada con el resultado de la evaluación final.'));
  return lista;
};

const anexo = (id: number, nombre: string, tipo: Anexo['tipo'], archivo: string): Anexo => ({
  id,
  nombre,
  tipo,
  archivo,
  estado: 'pendiente',
  legalizadoPor: '',
  legalizadoEl: null,
});

/** Anexos de cierre que Secretaría legaliza: solo en revisión final o cerrada. */
function anexosPorDefecto(p: Practica): Anexo[] {
  if (p.estado !== 'en_revision_final' && p.estado !== 'cerrada') return [];
  const base = p.id * 100;
  const anexos: Anexo[] = [];
  if (p.informeFinal) anexos.push(anexo(base + 1, 'Informe final del estudiante', 'informe_final', p.informeFinal.archivo));
  if (p.informeExterno) {
    const nombre = p.tipo === 'laboral' ? 'Informe externo del tutor de la entidad' : 'Informe del proyecto de vinculación';
    anexos.push(anexo(base + 2, nombre, 'informe_externo', p.informeExterno.archivo));
  }
  // Variedad: la práctica 8 ya tiene su primer anexo legalizado.
  if (p.id === 8 && anexos.length) anexos[0] = { ...anexos[0], estado: 'legalizado', legalizadoPor: SECRETARIA, legalizadoEl: fecha(2026, 6, 5) };
  return anexos;
}

export const etiquetaEstadoAnexo = (a: Anexo): string => ESTADO_ANEXO[a.estado];

/** Crea una práctica con los valores por defecto de `sample_data.py` y el resto en `datos`. */
export function crearPractica(id: number, estudiante: string, tipo: TipoPractica, estado: EstadoPractica, reportes: ReporteSemanal[], datos: Partial<Practica> = {}): Practica {
  const p: Practica = {
    id,
    estudiante,
    estado,
    tipo,
    subtipo: '',
    esAyudantia: false,
    entidad: '',
    tutorAcademico: TUTOR_ACADEMICO,
    tutorEntidad: '',
    proyectoVinculacion: '',
    periodo: PERIODO,
    carrera: CARRERA,
    horasRequeridas: 160,
    semanaActual: 9,
    plan: plan('validado', ['Actividades de la práctica.'], fecha(2026, 4, 8)),
    reportes,
    informeFinal: null,
    informeExterno: null,
    evaluacion: null,
    resultado: '',
    historial: [],
    incumplimientos: [],
    anexos: [],
    ...datos,
  };
  if (estado === 'cerrada') p.resultado = datos.resultado ?? 'aprobada';
  p.historial = datos.historial ?? historialInicial(p);
  p.anexos = datos.anexos ?? anexosPorDefecto(p);
  return p;
}

const evaluacion = (porcentaje: number, resultado: Evaluacion['resultado'], por: string): Evaluacion => ({
  porcentaje,
  resultado,
  registradoPor: por,
  registradoEl: fecha(2026, 6, 3),
});

const externo = (por: string, el: Fecha, valoracion: string, archivo: string): InformeExterno => ({ registradoPor: por, registradoEl: el, valoracion, archivo });

// --- Las dos prácticas de la estudiante (ids 1 y 2) ---------------------------

function laboral(): Practica {
  return crearPractica(
    1,
    ESTUDIANTE,
    'laboral',
    'en_curso',
    [
      validado(1, 8, { confirmadoPorEntidad: true }),
      validado(2, 8, { confirmadoPorEntidad: true }),
      validado(3, 6, { confirmadoPorEntidad: true }),
      validado(4, 8, { confirmadoPorEntidad: true }),
      reporte(5, 6, 'devuelto', {
        confirmadoPorEntidad: true,
        observacion: 'Falta detallar qué talleres calificó. Agregue el nombre de cada taller y vuelva a enviar el reporte con la lista firmada.',
      }),
      validado(6, 4, { confirmadoPorEntidad: true }),
      validado(7, 8, { confirmadoPorEntidad: false }),
      reporte(8, 8, 'en_revision', {
        confirmadoPorEntidad: false,
        actividades: ['Calificación de los talleres 7 y 8 de Programación.', 'Dos tutorías de refuerzo a estudiantes de primer ciclo.'],
        evidencias: ['talleres-semana-8.pdf', 'asistencia-tutorias.pdf'],
      }),
      reporte(9, 0, 'sin_reporte'),
    ],
    {
      subtipo: 'ayudantia_docencia',
      esAyudantia: true,
      entidad: ENTIDAD_UNL,
      tutorEntidad: TUTOR_ENTIDAD,
      plan: plan(
        'validado',
        ['Apoyo en la calificación de talleres de Programación.', 'Tutorías de refuerzo a estudiantes de primer ciclo.', 'Preparación de material para laboratorios.'],
        fecha(2026, 4, 10),
      ),
      incumplimientos: [
        {
          descripcion: 'No asistió dos días consecutivos a las tutorías de refuerzo sin presentar justificativo.',
          reportadoPor: TUTOR_ENTIDAD,
          reportadoEl: fecha(2026, 5, 18),
        },
      ],
    },
  );
}

function comunitaria(): Practica {
  const reportes: ReporteSemanal[] = [6, 6, 8, 6, 6, 8, 6, 6].map((h, i) => validado(i + 1, h, {}, TUTOR_COMUNITARIA));
  reportes.push(reporte(9, 6, 'en_revision'), reporte(10, 0, 'sin_reporte'));
  return crearPractica(2, ESTUDIANTE, 'comunitaria', 'en_curso', reportes, {
    entidad: 'Junta Parroquial de San Lucas',
    tutorAcademico: TUTOR_COMUNITARIA,
    proyectoVinculacion: 'Alfabetización digital para adultos mayores del cantón Loja',
    horasRequeridas: 96,
    semanaActual: 10,
    plan: plan(
      'validado',
      ['Talleres semanales de uso básico del teléfono y del correo.', 'Elaboración de guías impresas para los participantes.'],
      fecha(2026, 4, 9),
      TUTOR_COMUNITARIA,
    ),
  });
}

// --- Otras prácticas de ejemplo (ids 3 a 10) ----------------------------------

function ayudantiaInvestigacion(): Practica {
  const reportes = [8, 8, 10, 8, 6, 8].map((h, i) => validado(i + 1, h, { confirmadoPorEntidad: true }));
  reportes.push(
    reporte(7, 8, 'en_revision', {
      confirmadoPorEntidad: false,
      actividades: ['Limpieza del conjunto de datos de matrícula 2020-2025.', 'Reunión de avance con el grupo de investigación.'],
      evidencias: ['limpieza-datos-semana-7.pdf'],
    }),
    reporte(8, 10, 'en_revision', {
      confirmadoPorEntidad: true,
      actividades: ['Primer modelo de predicción de deserción y su informe.'],
      evidencias: ['modelo-desercion-v1.pdf'],
    }),
    reporte(9, 0, 'sin_reporte'),
  );
  return crearPractica(3, 'JIMÉNEZ CASTILLO DIEGO ALEJANDRO', 'laboral', 'en_curso', reportes, {
    subtipo: 'ayudantia_investigacion',
    esAyudantia: true,
    entidad: ENTIDAD_UNL,
    tutorEntidad: TUTOR_ENTIDAD,
    plan: plan('validado', ['Preparación de datos y modelos para el proyecto de deserción estudiantil.'], fecha(2026, 4, 9)),
  });
}

const comunitariaAsignada = (): Practica =>
  crearPractica(4, 'QUIZHPE GUAMÁN ANDREA SOFÍA', 'comunitaria', 'asignada', [], {
    entidad: 'GAD Parroquial de Vilcabamba',
    proyectoVinculacion: 'Sitio web informativo para el GAD parroquial de Vilcabamba',
    horasRequeridas: 96,
    plan: plan(
      'en_revision',
      ['Levantamiento de la información que publicará el GAD.', 'Diseño y publicación del sitio web.', 'Capacitación al personal que lo actualizará.'],
      fecha(2026, 5, 29),
    ),
  });

/** Pasantía con sus 160 h cumplidas que espera los informes de cierre. */
const pasantia = (id: number, estudiante: string, final: InformeFinal, ext: InformeExterno | null): Practica =>
  crearPractica(id, estudiante, 'laboral', 'en_revision_final', Array.from({ length: 8 }, (_, i) => validado(i + 1, 20, { confirmadoPorEntidad: true })), {
    subtipo: 'pasantia',
    entidad: ENTIDAD_SUR,
    tutorEntidad: TUTOR_ENTIDAD_SUR,
    plan: plan('validado', ['Desarrollo del módulo de inventario del sistema de la empresa.'], fecha(2026, 4, 8)),
    informeFinal: final,
    informeExterno: ext,
  });

const pasantiaListaParaEvaluar = (): Practica =>
  pasantia(
    5,
    'TORRES VIVANCO MATEO JOSÉ',
    informeFinal('validado', fecha(2026, 6, 1), 'informe-final-torres.pdf', { validadoPor: TUTOR_ACADEMICO, validadoEl: fecha(2026, 6, 3) }),
    externo(TUTOR_ENTIDAD_SUR, fecha(2026, 6, 2), 'Cumplió las actividades del plan con autonomía y puntualidad.', 'informe-entidad-torres.pdf'),
  );

const pasantiaConInformeEnRevision = (): Practica =>
  pasantia(6, 'CUENCA ROJAS VALERIA ISABEL', informeFinal('en_revision', fecha(2026, 6, 2), 'informe-final-cuenca.pdf'), null);

/** C4: todo listo para que el coordinador la cierre. */
const pasantiaListaParaCerrar = (): Practica =>
  crearPractica(7, 'ZAMBRANO ORTIZ ANDREA PAOLA', 'laboral', 'en_revision_final', Array.from({ length: 8 }, (_, i) => validado(i + 1, 20, { confirmadoPorEntidad: true }, TUTOR_CARRERA)), {
    subtipo: 'pasantia',
    entidad: ENTIDAD_NORTE,
    tutorAcademico: TUTOR_CARRERA,
    tutorEntidad: TUTOR_ENTIDAD_SUR,
    plan: plan('validado', ['Desarrollo del módulo de inventario de la empresa.'], fecha(2026, 4, 8), TUTOR_CARRERA),
    informeFinal: informeFinal('validado', fecha(2026, 6, 1), 'informe-final-zambrano.pdf', { validadoPor: TUTOR_CARRERA, validadoEl: fecha(2026, 6, 3) }),
    informeExterno: externo(TUTOR_ENTIDAD_SUR, fecha(2026, 6, 2), 'Cumplió con el plan y presentó el informe de la empresa.', 'informe-entidad-zambrano.pdf'),
    evaluacion: evaluacion(88, 'aprobada', TUTOR_CARRERA),
  });

/** C6: una práctica cerrada con el resultado de su evaluación final (Art. 339). */
function practicaCerrada(id: number, estudiante: string, porcentaje: number, resultado: Evaluacion['resultado'], tipo: TipoPractica = 'laboral'): Practica {
  const horas = tipo === 'laboral' ? 160 : 96;
  const laboralTipo = tipo === 'laboral';
  return crearPractica(
    id,
    estudiante,
    tipo,
    'cerrada',
    Array.from({ length: 8 }, (_, i) => validado(i + 1, horas / 8, { confirmadoPorEntidad: true }, TUTOR_CARRERA)),
    {
      subtipo: laboralTipo ? 'pasantia' : '',
      entidad: laboralTipo ? ENTIDAD_NORTE : 'GAD Municipal de Catamayo',
      tutorAcademico: TUTOR_CARRERA,
      tutorEntidad: laboralTipo ? TUTOR_ENTIDAD_SUR : '',
      proyectoVinculacion: laboralTipo ? '' : 'Alfabetización digital en el GAD de Catamayo',
      plan: plan('validado', ['Actividades del plan aprobado por el tutor académico.'], fecha(2026, 4, 8), TUTOR_CARRERA),
      informeFinal: informeFinal('validado', fecha(2026, 6, 3), `informe-final-cerrada-${id}.pdf`, { validadoPor: TUTOR_CARRERA, validadoEl: fecha(2026, 6, 3) }),
      informeExterno: externo(laboralTipo ? TUTOR_ENTIDAD_SUR : 'PROYECTO DE VINCULACIÓN', fecha(2026, 6, 3), 'Cumplimiento satisfactorio del plan de actividades.', `informe-externo-cerrada-${id}.pdf`),
      evaluacion: evaluacion(porcentaje, resultado, TUTOR_CARRERA),
      resultado,
      horasRequeridas: horas,
      semanaActual: TOTAL_SEMANAS,
    },
  );
}

function pasantiaNoAprobada(): Practica {
  const base = pasantiaListaParaCerrar();
  return crearPractica(10, 'SALAZAR VEGA MARÍA JOSÉ', 'laboral', 'en_revision_final', base.reportes, {
    ...base,
    id: 10,
    estudiante: 'SALAZAR VEGA MARÍA JOSÉ',
    evaluacion: evaluacion(64, 'no_aprobada', TUTOR_CARRERA),
    historial: undefined,
    anexos: undefined,
  });
}

/** Las 10 prácticas escritas a mano (ids 1 a 10); las dos primeras son de la estudiante. */
export const PRACTICAS_DE_EJEMPLO: readonly Practica[] = [
  laboral(),
  comunitaria(),
  ayudantiaInvestigacion(),
  comunitariaAsignada(),
  pasantiaListaParaEvaluar(),
  pasantiaConInformeEnRevision(),
  pasantiaListaParaCerrar(),
  practicaCerrada(8, 'CORDOVA VAZQUEZ JOSE LUIS', 92, 'aprobada'),
  practicaCerrada(9, 'AYOVI CANDO MARIA FERNANDA', 64, 'no_aprobada', 'comunitaria'),
  pasantiaNoAprobada(),
];

/** La práctica 1 (laboral) y la 2 (comunitaria) de la estudiante de la demostración. */
export const PRACTICAS_DE_LA_ESTUDIANTE: readonly Practica[] = PRACTICAS_DE_EJEMPLO.slice(0, 2);

/** Etiqueta del estado, con el resultado si está cerrada: «Cerrada (aprobada)». */
export const etiquetaEstadoPractica = (p: Practica): string =>
  p.estado === 'cerrada' && p.resultado ? `${ESTADO_PRACTICA.cerrada} (${RESULTADO_PRACTICA[p.resultado].toLowerCase()})` : ESTADO_PRACTICA[p.estado];
