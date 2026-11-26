import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { distinctUntilChanged, map, switchMap } from 'rxjs';
import { avanceDe, ESTADO_REPORTE, formatoFecha } from '../../core/demo';
import { cargando } from '../../core/estado-ui';
import { Aviso, Insignia, Pasos, Tarjeta, type PasoItem } from '../../shared/ui';
import { EstudianteApi } from './estudiante.api';
import type { ReporteDetalle } from './estudiante.model';
import { aEstado, idPractica, nombrePropio, paramPractica, rangoLargo, rezagada, tipoReporte } from './estudiante.util';
import { EstadoPantalla } from './ui/estado-pantalla';

/** E5 · Reporte semanal (`?s=` semana, `?p=` práctica): observación, horas, actividades, evidencias y seguimiento. */
@Component({
  selector: 'app-reporte-semanal',
  imports: [RouterLink, Tarjeta, Insignia, Pasos, Aviso, EstadoPantalla],
  templateUrl: './reporte-semanal.html',
  styleUrls: ['./pantalla.css', './reporte-semanal.css'],
})
export class ReporteSemana {
  private readonly api = inject(EstudianteApi);
  protected readonly estado = toSignal(
    inject(ActivatedRoute).queryParamMap.pipe(
      map((q) => ({ id: idPractica(q.get('p')), semana: Number(q.get('s')) })),
      distinctUntilChanged((a, b) => a.id === b.id && a.semana === b.semana),
      switchMap(({ id, semana }) => aEstado(this.api.reporte(id, semana))),
    ),
    { initialValue: cargando<ReporteDetalle>() },
  );

  protected readonly estadoTexto = ESTADO_REPORTE;
  protected readonly tipoReporte = tipoReporte;
  protected readonly nombrePropio = nombrePropio;
  protected readonly formatoFecha = formatoFecha;
  protected readonly rangoLargo = rangoLargo;
  protected readonly paramPractica = paramPractica;
  protected readonly avance = avanceDe;
  protected readonly rezagada = rezagada;

  /** La línea de seguimiento depende del estado del reporte. */
  protected pasos(d: ReporteDetalle): PasoItem[] {
    const r = d.reporte;
    const tutor = nombrePropio(r.validadoPor);
    const enviado: PasoItem = { estado: 'done', titulo: 'Reporte enviado', detalle: `${r.enviadoEl ? formatoFecha(r.enviadoEl) : '—'} · queda en revisión` };
    const decision = formatoFecha(r.validadoEl ?? r.hasta);
    switch (r.estado) {
      case 'validado':
        return [
          enviado,
          { estado: 'done', titulo: 'Revisado por el tutor académico', detalle: `${tutor} · ${decision}` },
          { estado: 'done', titulo: 'Validación', detalle: 'Las horas pasan a su avance' },
        ];
      case 'en_revision':
        return [
          enviado,
          { estado: 'now', titulo: 'Revisión del tutor académico', detalle: 'Está aquí: espera la validación' },
          { estado: 'pendiente', titulo: 'Validación', detalle: 'Las horas pasan a su avance' },
        ];
      case 'devuelto':
        return [
          enviado,
          { estado: 'bad', titulo: 'Devuelto por el tutor académico', detalle: `${decision} · con observación` },
          { estado: 'now', titulo: 'Corrección del estudiante', detalle: 'Está aquí: corrige y reenvía, vuelve a «en revisión»' },
          { estado: 'pendiente', titulo: 'Validación', detalle: 'Las horas pasan a su avance' },
        ];
      default:
        return [
          { estado: 'now', titulo: 'Reporte por enviar', detalle: 'Está aquí: registre las horas de la semana' },
          { estado: 'pendiente', titulo: 'Revisión del tutor académico', detalle: 'Aprueba o devuelve' },
          { estado: 'pendiente', titulo: 'Validación', detalle: 'Las horas pasan a su avance' },
        ];
    }
  }
}
