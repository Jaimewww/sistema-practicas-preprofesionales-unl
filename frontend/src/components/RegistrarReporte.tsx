import { useState, type FormEvent } from 'react';
import { reportesApi, type Reporte } from '../lib/reportes';
import { cargando, exito, inicial, type EstadoUi } from '../lib/estado-ui';
import { estadoDeError } from '../lib/errores';

/**
 * Pantalla E4: registrar horas semanales (F-002).     RESPONSABLE: Melissa
 *
 * El esqueleto deja el flujo mínimo funcionando contra el mock para probar el
 * cableado. Pendiente (Melissa): diseño del formulario, confirmación del 201,
 * horas acumuladas con reportesApi.horas() y recibir practicaId del selector.
 */
export default function RegistrarReporte({ practicaId = 1 }: { practicaId?: number }) {
  const [estado, setEstado] = useState<EstadoUi<Reporte>>(inicial());

  async function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const form = new FormData(evento.currentTarget);
    setEstado(cargando());
    try {
      const reporte = await reportesApi.crear(practicaId, {
        semana: Number(form.get('semana')),
        horas_reportadas: Number(form.get('horas_reportadas')),
      });
      setEstado(exito(reporte));
    } catch (e) {
      setEstado(estadoDeError(e));
    }
  }

  return (
    <form onSubmit={enviar}>
      <label>
        Semana <input name="semana" type="number" required />
      </label>
      <label>
        Horas <input name="horas_reportadas" type="number" required />
      </label>
      <button type="submit" disabled={estado.tipo === 'cargando'}>
        {estado.tipo === 'cargando' ? 'Enviando…' : 'Registrar'}
      </button>

      {estado.tipo === 'exito' && (
        <p role="status">Reporte de la semana {estado.datos.semana} enviado ({estado.datos.estado}).</p>
      )}
      {estado.tipo === 'error' && <p role="alert">{estado.mensaje}</p>}
    </form>
  );
}
