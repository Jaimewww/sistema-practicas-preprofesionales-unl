/// <reference types="vitest/globals" />
import { Route } from '@angular/router';
import { DirectorApi } from './director.api';
import { DirectorMock } from './director.mock';
import { RUTAS_DIRECTOR } from './director.routes';

function aplanar(rutas: Route[], prefijo = ''): Route[] {
  return rutas.flatMap((r) => {
    const ruta = [prefijo, r.path].filter(Boolean).join('/');
    return [{ ...r, path: ruta }, ...aplanar(r.children ?? [], ruta)];
  });
}

describe('Rutas del director', () => {
  const hojas = aplanar(RUTAS_DIRECTOR).filter((r) => r.component && r.data);

  it('cumple el contrato de rutas', () => {
    expect(hojas.map((r) => r.path)).toEqual(['', 'cierres', 'cierre', 'cierre/historial']);
  });

  it('cada pantalla fija su título y sus migas', () => {
    for (const ruta of hojas) {
      expect(ruta.data?.['titulo'], ruta.path).toBeTruthy();
      expect(ruta.data?.['migas'], ruta.path).toBeInstanceOf(Array);
      expect(ruta.title, ruta.path).toBeTruthy();
    }
    expect(hojas.find((r) => r.path === '')?.data?.['foto']).toBe(true);
  });

  it('registra DirectorApi → DirectorMock en los providers del padre', () => {
    expect(RUTAS_DIRECTOR[0].providers).toEqual([{ provide: DirectorApi, useClass: DirectorMock }]);
  });
});
