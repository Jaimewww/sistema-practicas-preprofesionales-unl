import { TOTAL_SEMANAS, UMBRAL_REZAGO } from './constantes';
import { estaRezagada, horasEnRevision, horasEsperadas, horasMinimas, horasValidadas } from './horas';

describe('horas de la práctica (datos de demostración)', () => {
  it('las horas esperadas son proporcionales a las 16 semanas', () => {
    expect(TOTAL_SEMANAS).toBe(16);
    expect(horasEsperadas(240, 9)).toBe(135);
    expect(horasEsperadas(160, 9)).toBe(90);
  });

  it('el mínimo es el 80 % de las esperadas', () => {
    expect(UMBRAL_REZAGO).toBe(80);
    expect(horasMinimas(135)).toBe(108);
    expect(horasMinimas(135, 50)).toBe(68);
  });

  it('las horas en revisión cuentan para no estar rezagada, pero no para validar', () => {
    // 96 validadas + 16 en revisión = 112 >= 108: al día. Solo las 96 validadas: rezagada.
    expect(estaRezagada(96, 16, 135)).toBe(false);
    expect(estaRezagada(96, 0, 135)).toBe(true);
    expect(estaRezagada(108, 0, 135)).toBe(false);
  });

  it('suma por estado de reporte y no mezcla validadas con en revisión', () => {
    const p = {
      reportes: [
        { estado: 'validado', horas: 16 },
        { estado: 'validado', horas: 16 },
        { estado: 'en_revision', horas: 8 },
        { estado: 'devuelto', horas: 8 },
      ],
    } as Parameters<typeof horasValidadas>[0];
    expect(horasValidadas(p)).toBe(32);
    expect(horasEnRevision(p)).toBe(8);
  });
});
