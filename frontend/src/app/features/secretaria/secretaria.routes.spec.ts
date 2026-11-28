/// <reference types="vitest/globals" />
import { Route } from '@angular/router';
import { SecretariaApi } from './secretaria.api';
import { SecretariaMock } from './secretaria.mock';
import { RUTAS_SECRETARIA } from './secretaria.routes';

function aplanar(rutas: Route[], prefijo = ''): Route[] {
  return rutas.flatMap((r) => {
    const ruta = [prefijo, r.path].filter(Boolean).join('/');
    return [{ ...r, path: ruta }, ...aplanar(r.children ?? [], ruta)];
  });
}

describe('Rutas de secretaría', () => {
  const pantallas = aplanar(RUTAS_SECRETARIA).filter((r) => r.component);

  it('cumple el contrato de rutas', () => {
    expect(pantallas.map((r) => r.path).sort()).toEqual(['', 'anexos', 'legalizar']);
  });

  it('cada pantalla fija su título y sus migas; el tablero lleva foto', () => {
    for (const ruta of pantallas) {
      expect(ruta.title, ruta.path).toBeTruthy();
      expect(ruta.data?.['titulo'], ruta.path).toBeTruthy();
      expect(ruta.data?.['migas'], ruta.path).toBeInstanceOf(Array);
    }
    expect(pantallas.find((r) => r.path === '')?.data?.['foto']).toBe(true);
  });

  it('registra SecretariaApi → SecretariaMock en los providers del padre', () => {
    expect(RUTAS_SECRETARIA[0].providers).toEqual([{ provide: SecretariaApi, useClass: SecretariaMock }]);
  });
});
