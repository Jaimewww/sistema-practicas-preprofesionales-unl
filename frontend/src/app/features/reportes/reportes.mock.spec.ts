import { firstValueFrom } from 'rxjs';
import { ApiError } from '../../core/api/envelope';
import { ReportesMock } from './reportes.mock';

describe('ReportesMock (escenarios del README)', () => {
  const mock = () => Object.assign(new ReportesMock(), { demoraMs: 0 });
  const codigo = (p: Promise<unknown>) => p.then(() => 'ok', (e: ApiError) => `${e.status} ${e.code}`);

  it('201 normal y con requiere_revision si supera 40 horas', async () => {
    const m = mock();
    expect((await firstValueFrom(m.crear(1, { semana: 1, horas_reportadas: 12 }))).requiere_revision).toBe(false);
    expect((await firstValueFrom(m.crear(1, { semana: 2, horas_reportadas: 50 }))).requiere_revision).toBe(true);
  });

  it('errores: 400, 409 duplicada, 409 no en curso, 404', async () => {
    const m = mock();
    await firstValueFrom(m.crear(1, { semana: 3, horas_reportadas: 8 }));
    expect(await codigo(firstValueFrom(m.crear(1, { semana: 4, horas_reportadas: 0 })))).toBe('400 validacion');
    expect(await codigo(firstValueFrom(m.crear(1, { semana: 3, horas_reportadas: 8 })))).toBe('409 semana_duplicada');
    expect(await codigo(firstValueFrom(m.crear(409, { semana: 1, horas_reportadas: 8 })))).toBe('409 practica_no_en_curso');
    expect(await codigo(firstValueFrom(m.crear(404, { semana: 1, horas_reportadas: 8 })))).toBe('404 no_encontrado');
  });
});
