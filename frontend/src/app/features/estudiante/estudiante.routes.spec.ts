import { Route } from '@angular/router';
import { RUTAS_ESTUDIANTE } from './estudiante.routes';

function aplanar(rutas: Route[], prefijo = ''): Route[] {
  return rutas.flatMap((r) => {
    const ruta = [prefijo, r.path].filter(Boolean).join('/');
    return [{ ...r, path: ruta }, ...aplanar(r.children ?? [], ruta)];
  });
}

describe('Rutas del estudiante', () => {
  const hojas = aplanar(RUTAS_ESTUDIANTE).filter((r) => r.component);

  it('cumple el contrato de rutas', () => {
    expect(hojas.map((r) => r.path)).toEqual(['', 'mis-practicas', 'practica', 'practica', 'practica/plan', 'practica/reportes', 'plan', 'reportes/nuevo', 'reporte', 'informe-final']);
  });

  it('cada pantalla fija su título y sus migas', () => {
    for (const ruta of hojas.filter((r) => r.path !== 'practica' || r.title)) {
      if (!ruta.data) continue;
      expect(ruta.data['titulo'], ruta.path).toBeTruthy();
      expect(ruta.data['migas'], ruta.path).toBeInstanceOf(Array);
    }
    expect(hojas.find((r) => r.path === '')?.data?.['foto']).toBe(true);
  });

  it('registra EstudianteApi en los providers del padre', () => {
    expect(RUTAS_ESTUDIANTE[0].providers).toHaveLength(1);
  });
});
