import { of } from 'rxjs';
import { PRACTICAS_DE_LA_ESTUDIANTE } from '../../core/demo';
import type { Practica } from '../../core/demo';
import { EstudianteMock } from './estudiante.mock';
import { abrir, textoDe } from './pruebas';

describe('Informe final (E6)', () => {
  it('con la práctica en curso está bloqueado y dice por qué', async () => {
    const { vista } = await abrir('/estudiante/informe-final');
    const texto = textoDe(vista);
    expect(texto).toContain('Aún no está disponible.');
    expect(texto).toContain('Se habilita cuando su práctica pase a «revisión final». Hoy está «en curso» con 42 de 160 h validadas.');
    expect(vista.querySelector('fieldset')?.disabled).toBe(true);
    expect(vista.querySelector<HTMLTextAreaElement>('#resumen')?.matches(':disabled')).toBe(true);
    expect(vista.querySelector<HTMLButtonElement>('button[type="submit"]')?.matches(':disabled')).toBe(true);
  });

  it('muestra el camino al cierre con el primer paso como actual', async () => {
    const { vista } = await abrir('/estudiante/informe-final');
    const pasos = [...vista.querySelectorAll('app-pasos li')].map((li) => li.querySelector('strong')?.textContent?.replace(/\s+/g, ' ').trim());
    expect(pasos).toEqual([
      'Completar las 160 h (En curso)',
      'Revisión final (Pendiente)',
      'Presentar el informe (Pendiente)',
      'Revisión del tutor académico (Pendiente)',
      'Evaluación y cierre (Pendiente)',
    ]);
    expect(textoDe(vista)).toContain('42 h validadas hasta hoy');
  });

  describe('en revisión final', () => {
    afterEach(() => vi.restoreAllMocks());

    const enRevisionFinal: Practica = { ...PRACTICAS_DE_LA_ESTUDIANTE[0], estado: 'en_revision_final' };

    async function abrirDesbloqueado() {
      vi.spyOn(EstudianteMock.prototype, 'practica').mockReturnValue(of(enRevisionFinal));
      return abrir('/estudiante/informe-final');
    }

    it('se habilita el formulario y exige el resumen y el PDF', async () => {
      const { vista, esperar } = await abrirDesbloqueado();
      expect(textoDe(vista)).not.toContain('Aún no está disponible.');
      expect(vista.querySelector('fieldset')?.disabled).toBe(false);
      vista.querySelector<HTMLButtonElement>('button[type="submit"]')!.click();
      await esperar();
      const errores = [...vista.querySelectorAll('.resumen-error li')].map((li) => li.textContent);
      expect(errores).toEqual(['Escriba el resumen de su experiencia.', 'Adjunte su informe final en PDF.']);
    });
  });
});
