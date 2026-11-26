import { ROLES, ROL_POR_DEFECTO, rolDeUrl, rutaTablero } from './menu-roles';

describe('menu-roles', () => {
  it('define los 8 roles con prefijos, claves y siglas únicos', () => {
    expect(ROLES.map((r) => r.prefijo)).toEqual([
      'estudiante',
      'tutor-academico',
      'tutor-entidad',
      'coordinador',
      'director',
      'secretaria',
      'analista',
      'entidad-receptora',
    ]);
    expect(new Set(ROLES.map((r) => r.clave)).size).toBe(8);
    expect(new Set(ROLES.map((r) => r.persona.siglas)).size).toBe(8);
  });

  it('el menú de cada rol es el de la especificación y cuelga de su prefijo', () => {
    const etiquetas = Object.fromEntries(ROLES.map((r) => [r.prefijo, r.menu.map((i) => i.etiqueta)]));
    expect(etiquetas).toEqual({
      estudiante: ['Mis prácticas'],
      'tutor-academico': ['Pendientes de revisión', 'Mis tutorados'],
      'tutor-entidad': ['Mis practicantes', 'Reportes por confirmar'],
      coordinador: ['Prácticas de la carrera', 'Alertas', 'Consolidado', 'Configuración'],
      director: ['Cierres de mi carrera'],
      secretaria: ['Anexos por legalizar'],
      analista: ['Consolidado general'],
      'entidad-receptora': ['Catálogo de entidades', 'Convenios'],
    });
    for (const r of ROLES) {
      for (const i of r.menu) expect(i.ruta.startsWith(`/${r.prefijo}/`)).toBe(true);
    }
  });

  it('rutas del coordinador y contadores de campana', () => {
    const co = ROLES.find((r) => r.clave === 'coordinador')!;
    expect(co.menu.map((i) => i.ruta)).toEqual(['/coordinador/practicas', '/coordinador/alertas', '/coordinador/consolidado', '/coordinador/configuracion']);
    expect(ROLES.map((r) => r.campana)).toEqual([3, 4, 2, 5, 1, 0, 0, 0]);
    expect(rutaTablero(co)).toBe('/coordinador');
  });

  it('rolDeUrl lee el primer segmento y cae en el estudiante', () => {
    expect(rolDeUrl('/tutor-entidad/practicantes?x=1').clave).toBe('tutor_entidad');
    expect(rolDeUrl('/entidad-receptora').clave).toBe('entidad');
    expect(rolDeUrl('/')).toBe(ROL_POR_DEFECTO);
    expect(rolDeUrl('/login')).toBe(ROL_POR_DEFECTO);
    expect(rolDeUrl('/reportes/nuevo')).toBe(ROL_POR_DEFECTO);
  });
});
