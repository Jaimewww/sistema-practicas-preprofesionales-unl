import { RUTAS_TUTOR_ENTIDAD } from './tutor-entidad.routes';

describe('Rutas del tutor de la entidad', () => {
  const hijas = RUTAS_TUTOR_ENTIDAD[0].children ?? [];

  it('provee TutorEntidadApi con el mock en el padre', () => {
    expect(RUTAS_TUTOR_ENTIDAD[0].providers).toHaveLength(1);
  });

  it('tiene las seis pantallas con su ruta', () => {
    expect(hijas.map((r) => r.path)).toEqual(['', 'practicantes', 'reportes-por-confirmar', 'confirmar-reporte', 'informe-externo', 'incumplimiento']);
  });

  it('cada pantalla tiene componente, título de pestaña, título y migas', () => {
    for (const ruta of hijas) {
      const data = ruta.data as { titulo: string; migas: Array<{ texto: string; enlace?: string }> };
      expect(ruta.component, ruta.path).toBeDefined();
      expect(ruta.title, ruta.path).toMatch(/· Prácticas UNL$/);
      expect(data.titulo, ruta.path).toBeTruthy();
      expect(data.migas.length, ruta.path).toBeGreaterThan(0);
      for (const miga of data.migas) expect(miga.texto).toBeTruthy();
    }
  });

  it('solo el tablero lleva la foto', () => {
    expect(hijas.filter((r) => (r.data as { foto?: boolean }).foto).map((r) => r.path)).toEqual(['']);
  });
});
