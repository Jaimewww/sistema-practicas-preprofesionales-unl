import type { Practica, PracticasApi } from './tipos';

/** Dos prácticas de ejemplo; la 409 simula una práctica que ya no está en curso. */
export class PracticasMock implements PracticasApi {
  async listar(): Promise<Practica[]> {
    await new Promise((r) => setTimeout(r, 400));
    return [
      { id: 1, estudiante_id: 7, tipo: 'practica_laboral', subtipo: 'empresa', estado: 'en_curso', horas_requeridas: 240 },
      { id: 409, estudiante_id: 7, tipo: 'servicio_comunitario', subtipo: 'proyecto', estado: 'cerrada', horas_requeridas: 160 },
    ];
  }
}
