import { firstValueFrom } from 'rxjs';
import { ApiError } from '../../core/api/envelope';
import { CoordinadorMock } from './coordinador.mock';

function mock(): CoordinadorMock {
  const m = new CoordinadorMock();
  m.demoraMs = 0;
  return m;
}

describe('CoordinadorMock', () => {
  it('resume las 150 prácticas de la carrera', async () => {
    const r = await firstValueFrom(mock().resumen());
    expect(r.total).toBe(150);
    expect(r.porEstado.reduce((n, e) => n + e.cantidad, 0)).toBe(150);
    expect(r.alertasActivas).toBe(r.porAlerta.reduce((n, a) => n + a.cantidad, 0));
  });

  it('suspender exige motivo y una práctica en curso, y deja la entrada en el historial', async () => {
    const m = mock();
    await expect(firstValueFrom(m.suspender(1, '  '))).rejects.toMatchObject({ status: 400, campos: { motivo: ['Escriba el motivo de la decisión.'] } });
    await expect(firstValueFrom(m.suspender(7, 'x'))).rejects.toBeInstanceOf(ApiError);
    const antes = (await firstValueFrom(m.practica(1))).historial.length;
    const d = await firstValueFrom(m.suspender(1, 'Licencia'));
    expect(d.practica.estado).toBe('suspendida');
    expect(d.historial).toHaveLength(antes + 1);
    expect(d.historial.at(-1)).toMatchObject({ estadoAnterior: 'en_curso', estadoNuevo: 'suspendida', motivo: 'Licencia' });
    await expect(firstValueFrom(m.suspender(1, 'otra vez'))).rejects.toMatchObject({ status: 409 });
  });

  it('guarda la configuración válida y rechaza una inválida sin cambiarla', async () => {
    const m = mock();
    const base = await firstValueFrom(m.configuracion());
    await expect(firstValueFrom(m.guardarConfiguracion({ ...base, umbralRezago: 0 }))).rejects.toMatchObject({ status: 400 });
    expect((await firstValueFrom(m.configuracion())).umbralRezago).toBe(80);
    await firstValueFrom(m.guardarConfiguracion({ ...base, umbralRezago: 60 }));
    expect((await firstValueFrom(m.configuracion())).umbralRezago).toBe(60);
  });
});
