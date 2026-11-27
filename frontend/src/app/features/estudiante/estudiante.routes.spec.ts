/// <reference types="vitest/globals" />
import { Route } from '@angular/router';
import { InformeFinal } from './informe-final';
import { InformeFinalReal } from './informe-final-real';
import { PlanActividades } from './plan-actividades';
import { PlanActividadesReal } from './plan-actividades-real';
import { PlanInformeHttp } from './plan-informe.http';
import { PracticaPlan } from './practica-plan';
import { PracticaPlanReal } from './practica-plan-real';
import { RUTAS_ESTUDIANTE, rutasEstudiante } from './estudiante.routes';

function aplanar(rutas: Route[], prefijo = ''): Route[] {
  return rutas.flatMap((r) => {
    const ruta = [prefijo, r.path].filter(Boolean).join('/');
    return [{ ...r, path: ruta }, ...aplanar(r.children ?? [], ruta)];
  });
}

describe('Rutas del estudiante', () => {
  const hojas = aplanar(RUTAS_ESTUDIANTE).filter((r) => r.component);

  it('cumple el contrato de rutas', () => {
    expect(hojas.map((r) => r.path)).toEqual([
      '',
      'mis-practicas',
      'practica',
      'practica',
      'practica/plan',
      'practica/reportes',
      'plan',
      'reportes/nuevo',
      'reporte',
      'informe-final',
    ]);
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

/**
 * El modo real no toca los `path`: solo cambia el componente de las tres pantallas que ya
 * tienen variante real y les provee `PlanInformeHttp`. Las demás entradas quedan iguales.
 */
describe('Rutas del estudiante según environment.useMock', () => {
  const demo = aplanar(rutasEstudiante(true)).filter((r) => r.component);
  const real = aplanar(rutasEstudiante(false)).filter((r) => r.component);
  const ruta = (rutas: Route[], path: string): Route | undefined =>
    rutas.find((r) => r.path === path);
  const PLAN = ['plan', 'practica/plan', 'informe-final'];

  it('el modo real conserva exactamente las mismas rutas que el simulado', () => {
    expect(real.map((r) => r.path)).toEqual(demo.map((r) => r.path));
  });

  it('en modo real las tres pantallas usan su componente real y proveen el adaptador del API', () => {
    expect(ruta(real, 'plan')?.component).toBe(PlanActividadesReal);
    expect(ruta(real, 'practica/plan')?.component).toBe(PracticaPlanReal);
    expect(ruta(real, 'informe-final')?.component).toBe(InformeFinalReal);
    for (const path of PLAN) {
      expect(ruta(real, path)?.providers, path).toEqual([PlanInformeHttp]);
    }
  });

  it('en modo simulado se conservan los componentes de demostración, sin proveer el adaptador real', () => {
    expect(ruta(demo, 'plan')?.component).toBe(PlanActividades);
    expect(ruta(demo, 'practica/plan')?.component).toBe(PracticaPlan);
    expect(ruta(demo, 'informe-final')?.component).toBe(InformeFinal);
    for (const path of PLAN) {
      expect(ruta(demo, path)?.providers ?? [], path).toEqual([]);
    }
  });

  it('las demás pantallas del estudiante no cambian de componente entre modos', () => {
    const otrasDemo = demo.filter((r) => !PLAN.includes(r.path ?? ''));
    const otrasReal = real.filter((r) => !PLAN.includes(r.path ?? ''));
    expect(otrasReal.map((r) => r.path)).toEqual(otrasDemo.map((r) => r.path));
    expect(otrasReal.map((r) => r.component)).toEqual(otrasDemo.map((r) => r.component));
  });
});
