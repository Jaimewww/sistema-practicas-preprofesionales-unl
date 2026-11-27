import { firstValueFrom } from 'rxjs';
import { TutorEntidadMock } from './tutor-entidad.mock';

describe('TutorEntidadMock', () => {
  const mock = () => Object.assign(new TutorEntidadMock(), { demoraMs: 0 });
  const pdf = { nombre: 'informe.pdf', bytes: 1024 };

  it('solo devuelve los practicantes de práctica laboral de la tutora', async () => {
    const lista = await firstValueFrom(mock().practicantes());
    expect(lista.map((p) => p.id)).toEqual([1, 3]);
  });

  it('tiene tres reportes por confirmar y al confirmar uno deja dos', async () => {
    const api = mock();
    expect((await firstValueFrom(api.reportesPorConfirmar())).map((r) => r.codigo)).toEqual(['l7', 'l8', 'd7']);
    const c = await firstValueFrom(api.confirmarReporte('l8'));
    expect(c.por).toBe('CELI ARMIJOS MARTHA CECILIA');
    expect((await firstValueFrom(api.reportesPorConfirmar())).map((r) => r.codigo)).toEqual(['l7', 'd7']);
    expect((await firstValueFrom(api.reporte('l8'))).confirmacion).toEqual(c);
  });

  it('no confirma dos veces ni un reporte inexistente', async () => {
    const api = mock();
    await expect(firstValueFrom(api.confirmarReporte('d8'))).rejects.toMatchObject({ status: 409 });
    await expect(firstValueFrom(api.reporte('x1'))).rejects.toMatchObject({ status: 404 });
  });

  it('rechaza el informe sin valoración o con un archivo que no es PDF y no registra nada', async () => {
    const api = mock();
    await expect(firstValueFrom(api.registrarInformeExterno(1, '  ', pdf))).rejects.toMatchObject({ status: 400 });
    await expect(firstValueFrom(api.registrarInformeExterno(1, 'Bien', { nombre: 'a.docx', bytes: 10 }))).rejects.toMatchObject({ status: 400 });
    await expect(firstValueFrom(api.registrarInformeExterno(1, 'Bien', { nombre: 'a.pdf', bytes: 6 * 1048576 }))).rejects.toMatchObject({ status: 400 });
    expect((await firstValueFrom(api.practicantes()))[0].informeExterno).toBeNull();
  });

  it('registra el informe y el incumplimiento', async () => {
    const api = mock();
    await firstValueFrom(api.registrarInformeExterno(1, 'Cumplió', pdf));
    await expect(firstValueFrom(api.reportarIncumplimiento(1, ' '))).rejects.toMatchObject({ status: 400 });
    const r = await firstValueFrom(api.reportarIncumplimiento(3, 'No asistió'));
    expect(r.avisadoA).toBe('PAREDES JARAMILLO ROBERTO ANDRÉS');
    const [luciana, diego] = await firstValueFrom(api.practicantes());
    expect(luciana.informeExterno?.archivo).toBe('informe.pdf');
    expect(luciana.incumplimientos).toHaveLength(1);
    expect(diego.incumplimientos).toHaveLength(1);
  });
});
