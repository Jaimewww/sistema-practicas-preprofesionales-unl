import { firstValueFrom } from 'rxjs';
import { EstudianteMock } from './estudiante.mock';

describe('EstudianteMock', () => {
  const mock = () => Object.assign(new EstudianteMock(), { demoraMs: 0 });

  it('devuelve las dos prácticas de la estudiante', async () => {
    const lista = await firstValueFrom(mock().misPracticas());
    expect(lista.map((p) => p.tipo)).toEqual(['laboral', 'comunitaria']);
  });

  it('una práctica inexistente falla con 404', async () => {
    await expect(firstValueFrom(mock().practica(99))).rejects.toMatchObject({ status: 404, detail: 'No encontrado.' });
  });

  it('rechaza enviar un plan sin actividades y deja el plan como estaba', async () => {
    const api = mock();
    await expect(firstValueFrom(api.enviarPlan(1, [{ descripcion: '  ', herramientas: 'x', entregable: 'y' }]))).rejects.toMatchObject({ status: 400 });
    expect((await firstValueFrom(api.plan(1))).estado).toBe('validado');
  });

  it('al enviar un plan, queda «en revisión» con una versión más', async () => {
    const api = mock();
    await firstValueFrom(api.enviarPlan(1, [{ descripcion: 'Una actividad', herramientas: '', entregable: '' }]));
    const plan = await firstValueFrom(api.plan(1));
    expect(plan.estado).toBe('en_revision');
    expect(plan.version).toBe(3);
    expect(plan.actividades).toHaveLength(1);
  });

  it('el informe final solo se presenta con la práctica en revisión final', async () => {
    await expect(firstValueFrom(mock().presentarInforme(1, 'Resumen', 'informe.pdf'))).rejects.toMatchObject({ status: 409 });
  });
});
