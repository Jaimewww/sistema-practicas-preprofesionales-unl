/// <reference types="vitest/globals" />
import { Route } from '@angular/router';
import { CoordinadorApi } from './coordinador.api';
import { CoordinadorMock } from './coordinador.mock';
import { RUTAS_COORDINADOR } from './coordinador.routes';

function aplanar(rutas: Route[], prefijo = ''): Route[] {
  return rutas.flatMap((r) => {
    const ruta = [prefijo, r.path].filter(Boolean).join('/');
    return [{ ...r, path: ruta }, ...aplanar(r.children ?? [], ruta)];
  });
}

describe('Rutas del coordinador', () => {
  // `practica` es el marco (con hijos) y su resumen; las demás entradas son pantallas.
  const hojas = aplanar(RUTAS_COORDINADOR).filter((r) => r.component);
  const pantallas = hojas.filter((r) => !r.children);

  it('cumple el contrato de rutas', () => {
    expect(hojas.map((r) => r.path).sort()).toEqual(['', 'alertas', 'cerrar', 'configuracion', 'consolidado', 'practica', 'practica', 'practica/historial', 'practicas', 'suspender-cancelar'].sort());
  });

  it('cada pantalla fija su título y sus migas; el tablero lleva foto', () => {
    for (const ruta of pantallas) {
      expect(ruta.title, ruta.path).toBeTruthy();
      expect(ruta.data?.['titulo'], ruta.path).toBeTruthy();
      expect(ruta.data?.['migas'], ruta.path).toBeInstanceOf(Array);
    }
    expect(pantallas.find((r) => r.path === '')?.data?.['foto']).toBe(true);
  });

  it('registra CoordinadorApi → CoordinadorMock en los providers del padre', () => {
    expect(RUTAS_COORDINADOR[0].providers).toEqual([{ provide: CoordinadorApi, useClass: CoordinadorMock }]);
  });

  it('las rutas del menú lateral existen', () => {
    const rutas = hojas.map((r) => r.path);
    for (const r of ['practicas', 'alertas', 'consolidado', 'configuracion']) expect(rutas).toContain(r);
  });
});
