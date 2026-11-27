import { firstValueFrom } from 'rxjs';
import { ApiError } from '../../core/api/envelope';
import { TutorAcademicoMock } from './tutor-academico.mock';

function mock(): TutorAcademicoMock {
  const m = new TutorAcademicoMock();
  m.demoraMs = 0;
  return m;
}

describe('TutorAcademicoMock', () => {
  it('los tutorados son las cinco prácticas de Roberto Paredes', async () => {
    const lista = await firstValueFrom(mock().tutorados());
    expect(lista.map((p) => p.id)).toEqual([1, 3, 4, 5, 6]);
  });

  it('devolver sin observación falla con la validación y no cambia los pendientes', async () => {
    const m = mock();
    await expect(firstValueFrom(m.decidir('reporte', 'l8', 'devolver', '  '))).rejects.toMatchObject({ status: 400, detail: 'La devolución exige una observación' });
    await expect(firstValueFrom(m.decidir('reporte', 'l8', 'devolver', ''))).rejects.toBeInstanceOf(ApiError);
    expect((await firstValueFrom(m.pendientes())).length).toBe(5);
    expect((await firstValueFrom(m.revision('reporte', 'l8'))).estado).toBe('en_revision');
  });

  it('validar saca el documento de los pendientes y suma las horas validadas', async () => {
    const m = mock();
    await firstValueFrom(m.decidir('reporte', 'l8', 'validar', ''));
    expect((await firstValueFrom(m.pendientes())).map((p) => p.clave)).toEqual(['d7', 'a4', 'd8', 'v6']);
    expect((await firstValueFrom(m.tutorados()))[0].reportes[7].estado).toBe('validado');
  });

  it('decidir dos veces el mismo documento falla', async () => {
    const m = mock();
    await firstValueFrom(m.decidir('plan', 'a4', 'validar', ''));
    await expect(firstValueFrom(m.decidir('plan', 'a4', 'validar', ''))).rejects.toMatchObject({ status: 409 });
    expect((await firstValueFrom(m.practica('4'))).practica.estado).toBe('en_curso');
  });

  it('la evaluación rechaza lo que está fuera de 0–100 y lo que no tiene requisitos', async () => {
    const m = mock();
    await expect(firstValueFrom(m.registrarEvaluacion(5, 101))).rejects.toMatchObject({ status: 400 });
    await expect(firstValueFrom(m.registrarEvaluacion(5, -1))).rejects.toMatchObject({ status: 400 });
    await expect(firstValueFrom(m.registrarEvaluacion(6, 80))).rejects.toMatchObject({ status: 409, code: 'faltan_requisitos' });
    expect((await firstValueFrom(m.evaluacion(5))).evaluacion).toBeNull();
    const r = await firstValueFrom(m.registrarEvaluacion(5, 70));
    expect(r.resultado).toBe('aprobada');
    await expect(firstValueFrom(m.registrarEvaluacion(5, 70))).rejects.toMatchObject({ status: 409 });
  });
});
