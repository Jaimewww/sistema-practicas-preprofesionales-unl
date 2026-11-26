/** Clave de cada rol (la de los prototipos). */
export type ClaveRol =
  | 'estudiante'
  | 'tutor_academico'
  | 'tutor_entidad'
  | 'coordinador'
  | 'director'
  | 'secretaria'
  | 'analista'
  | 'entidad';

/** Toda persona es inventada (como en `sample_data.py`). */
export const ESTUDIANTE = 'MENDIETA SARANGO LUCIANA BELÉN';
export const TUTOR_ACADEMICO = 'PAREDES JARAMILLO ROBERTO ANDRÉS';
export const TUTOR_ENTIDAD = 'CELI ARMIJOS MARTHA CECILIA';
export const TUTOR_ENTIDAD_SUR = 'VIVANCO LEÓN PABLO ESTEBAN';
export const TUTOR_COMUNITARIA = 'ORDOÑEZ BRAVO CARLOS EDUARDO';
export const TUTOR_CARRERA = 'CAÑAR MERCHÁN WASHINGTON EDUARDO';
export const DIRECTOR = 'ESPINOZA CASTRO MARCO VINICIO';
export const SECRETARIA = 'TORRES REYES GLADYS ELENA';
export const COORDINADOR = 'MENDOZA ARÉVALO CARLOS ANDRÉS';
export const ANALISTA_DVS = 'PACHECO LOORO VERÓNICA ELENA';
export const USUARIO_ENTIDAD = 'SALINAS ORDÓÑEZ RODRIGO XAVIER';

/** Quién es la persona de la demostración en cada rol (nombre completo). */
export const PERSONA_POR_ROL: Record<ClaveRol, string> = {
  estudiante: ESTUDIANTE,
  tutor_academico: TUTOR_ACADEMICO,
  tutor_entidad: TUTOR_ENTIDAD,
  coordinador: COORDINADOR,
  director: DIRECTOR,
  secretaria: SECRETARIA,
  analista: ANALISTA_DVS,
  entidad: USUARIO_ENTIDAD,
};

/** Tutores académicos de la carrera (reparto de las prácticas de ejemplo). */
export const TUTORES_CARRERA = [
  TUTOR_CARRERA,
  'CORDOVA PINTO MARIA ELENA',
  'ENRIQUEZ VARGAS JORGE LUIS',
  'LOAIZA TORRES SANDRA VERONICA',
  'ROSALES VILLALTA PEDRO PABLO',
  'SOLIS REYES ANA CECILIA',
] as const;

export const TUTORES_ENTIDAD = ['ALVARADO GUERRERO NORMAN EDUARDO', 'CHIMBORAZO LOBO MARITZA SOFIA', 'TORRES CAÑAVERA HENRY ALBERTO'] as const;

const APELLIDOS = ['AGUILAR', 'BENÍTEZ', 'CÁRDENAS', 'DÍAZ', 'ESPINOZA', 'FRANCO', 'GARCÍA', 'HERRERA', 'JARAMILLO', 'LOAIZA', 'MERCHÁN', 'NARVÁEZ', 'ORDOÑEZ', 'PÁEZ', 'QUISHPE'];
const APELLIDOS_SEGUNDOS = ['ACOSTA', 'BOADA', 'CARVAJAL', 'DOMÍNGUEZ', 'ESTRELLA', 'FONSECA', 'GUZMÁN', 'HURTADO', 'IBARRA', 'JUMBO'];
const NOMBRES = ['ANA LUCÍA', 'BRAYAN ANDRÉS', 'CAMILA SOFÍA', 'DIEGO FERNANDO', 'ELENA VERÓNICA', 'FABIO ANDRÉS', 'GABRIELA ELENA', 'HUMBERTO JOSÉ', 'ISABEL MARGARITA', 'JORGE LUIS', 'KATHERINE SOFÍA', 'LENIN ANTONIO', 'MARCELA BEATRIZ', 'NELSON IVÁN', 'OFELIA DEL CARMEN'];

/** Nombre de estudiante de ejemplo número `i` (todos distintos entre sí). */
export const nombreEstudiante = (i: number): string =>
  `${APELLIDOS[i % APELLIDOS.length]} ${APELLIDOS_SEGUNDOS[i % APELLIDOS_SEGUNDOS.length]} ${NOMBRES[Math.floor(i / APELLIDOS_SEGUNDOS.length) % NOMBRES.length]}`;
