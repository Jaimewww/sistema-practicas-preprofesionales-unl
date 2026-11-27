/// <reference types="vitest/globals" />
import { Route } from '@angular/router';
import { TutorAcademicoApi } from './tutor-academico.api';
import { TutorAcademicoMock } from './tutor-academico.mock';
import { RUTAS_TUTOR_ACADEMICO } from './tutor-academico.routes';

function aplanar(rutas: Route[], prefijo = ''): Route[] {
  return rutas.flatMap((r) => {
    const ruta = [prefijo, r.path].filter(Boolean).join('/');
    return [{ ...r, path: ruta }, ...aplanar(r.children ?? [], ruta)];
  });
}

describe('Rutas del tutor académico', () => {
  const hojas = aplanar(RUTAS_TUTOR_ACADEMICO).filter((r) => r.component);

  it('cumple el contrato de rutas', () => {
    expect(hojas.map((r) => r.path)).toEqual(['', 'pendientes', 'revisar/reporte', 'revisar/plan', 'revisar/informe', 'tutorados', 'practica', 'evaluacion']);
  });

  it('cada pantalla fija su título y sus migas', () => {
    for (const ruta of hojas) {
      expect(ruta.data?.['titulo'], ruta.path).toBeTruthy();
      expect(ruta.data?.['migas'], ruta.path).toBeInstanceOf(Array);
      expect(ruta.title, ruta.path).toBeTruthy();
    }
    expect(hojas.find((r) => r.path === '')?.data?.['foto']).toBe(true);
  });

  it('las migas llevan texto y, si enlazan, enlace dentro del rol', () => {
    for (const ruta of hojas) {
      for (const miga of ruta.data!['migas'] as Array<{ texto: string; enlace?: string }>) {
        expect(miga.texto).toBeTruthy();
        if (miga.enlace) expect(miga.enlace.startsWith('/tutor-academico')).toBe(true);
      }
    }
  });

  it('registra TutorAcademicoApi → TutorAcademicoMock en los providers del padre', () => {
    expect(RUTAS_TUTOR_ACADEMICO[0].providers).toEqual([{ provide: TutorAcademicoApi, useClass: TutorAcademicoMock }]);
  });
});
