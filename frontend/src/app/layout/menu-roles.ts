import type { ClaveRol } from '../core/demo';

export type { ClaveRol };

export interface ItemMenu {
  etiqueta: string;
  /** Ruta absoluta, siempre bajo el prefijo del rol. */
  ruta: string;
}

export interface RolMenu {
  clave: ClaveRol;
  /** Primer segmento de la URL del rol, sin barras: `coordinador`, `tutor-academico`… */
  prefijo: string;
  etiqueta: string;
  /** Persona de la demostración. */
  persona: { nombre: string; siglas: string };
  /** Entradas del submenú «Prácticas». */
  menu: readonly ItemMenu[];
  /** Notificaciones sin leer que muestra la campana. */
  campana: number;
}

const item = (prefijo: string, etiqueta: string, ruta: string): ItemMenu => ({ etiqueta, ruta: `/${prefijo}/${ruta}` });

function rol(
  clave: ClaveRol,
  prefijo: string,
  etiqueta: string,
  nombre: string,
  siglas: string,
  campana: number,
  menu: ReadonlyArray<readonly [string, string]>,
): RolMenu {
  return { clave, prefijo, etiqueta, persona: { nombre, siglas }, campana, menu: menu.map(([e, r]) => item(prefijo, e, r)) };
}

/** Los 8 roles, en el orden del selector de demostración. */
export const ROLES: readonly RolMenu[] = [
  rol('estudiante', 'estudiante', 'Estudiante', 'Luciana Mendieta', 'LM', 3, [['Mis prácticas', 'mis-practicas']]),
  rol('tutor_academico', 'tutor-academico', 'Tutor académico', 'Roberto Paredes', 'RP', 4, [
    ['Pendientes de revisión', 'pendientes'],
    ['Mis tutorados', 'tutorados'],
  ]),
  rol('tutor_entidad', 'tutor-entidad', 'Tutor de la entidad', 'Martha Celi', 'MC', 2, [
    ['Mis practicantes', 'practicantes'],
    ['Reportes por confirmar', 'reportes-por-confirmar'],
  ]),
  rol('coordinador', 'coordinador', 'Coordinador de prácticas', 'Coordinador de Computación', 'CC', 5, [
    ['Prácticas de la carrera', 'practicas'],
    ['Alertas', 'alertas'],
    ['Consolidado', 'consolidado'],
    ['Configuración', 'configuracion'],
  ]),
  rol('director', 'director', 'Director de carrera', 'Marco Espinoza', 'ME', 1, [['Cierres de mi carrera', 'cierres']]),
  rol('secretaria', 'secretaria', 'Secretaría de carrera', 'Gladys Torres', 'GT', 0, [['Anexos por legalizar', 'anexos']]),
  rol('analista', 'analista', 'Analista de prácticas (DVS)', 'Analista DVS', 'AD', 0, [['Consolidado general', 'consolidado']]),
  rol('entidad', 'entidad-receptora', 'Entidad receptora · Rectorado/Decanato', 'Rectorado UNL', 'RU', 0, [
    ['Catálogo de entidades', 'catalogo'],
    ['Convenios', 'convenios'],
  ]),
];

/** Rol que se muestra fuera de los prefijos de rol (`/`, `/login`, `/reportes/nuevo`). */
export const ROL_POR_DEFECTO: RolMenu = ROLES[0];

/** Ruta del tablero de un rol. */
export const rutaTablero = (r: RolMenu): string => `/${r.prefijo}`;

/** Rol cuyo prefijo es el primer segmento de la URL; sin coincidencia, el estudiante. */
export function rolDeUrl(url: string): RolMenu {
  const primero = url.split(/[?#]/)[0].split('/').filter(Boolean)[0];
  return ROLES.find((r) => r.prefijo === primero) ?? ROL_POR_DEFECTO;
}
