import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { cargando } from '../../core/estado-ui';
import { ESTADO_PRACTICA } from '../../core/demo';
import { Insignia, Kpi, KpiGrid, Tarjeta } from '../../shared/ui';
import { CoordinadorApi } from './coordinador.api';
import type { ResumenCarrera } from './coordinador.model';
import { aEstado, componente, nombrePropio, paramsPractica, textoAlerta, textoEstado, tipoAlerta, tipoEstado } from './coordinador.util';
import { EstadoPantalla } from './ui/estado-pantalla';

/** C0 · Tablero del coordinador: indicadores de la carrera, acciones rápidas y decisiones pendientes. */
@Component({
  selector: 'app-tablero-coordinador',
  imports: [RouterLink, Tarjeta, Insignia, Kpi, KpiGrid, EstadoPantalla],
  templateUrl: './tablero-coordinador.html',
  styleUrls: ['./pantalla.css', './tablero-coordinador.css'],
})
export class TableroCoordinador {
  private readonly api = inject(CoordinadorApi);
  protected readonly estado = toSignal(aEstado(this.api.resumen(), (r) => r.total === 0), { initialValue: cargando<ResumenCarrera>() });

  protected readonly textoEstadoDe = (estado: string) => ESTADO_PRACTICA[estado as keyof typeof ESTADO_PRACTICA];
  protected readonly textoEstado = textoEstado;
  protected readonly tipoEstado = tipoEstado;
  protected readonly textoAlerta = textoAlerta;
  protected readonly tipoAlerta = tipoAlerta;
  protected readonly componente = componente;
  protected readonly nombrePropio = nombrePropio;
  protected readonly paramsPractica = paramsPractica;
  protected readonly proporcion = (cantidad: number, total: number): number => (total ? Math.round((cantidad / total) * 100) : 0);
  protected readonly nota = (r: ResumenCarrera): string =>
    r.porAlerta.map((a) => `${a.cantidad} ${{ reporte_no_enviado: 'sin reporte', revision_pendiente: 'revisiones', rezago: 'rezagos', incumplimiento: a.cantidad === 1 ? 'incumplimiento' : 'incumplimientos' }[a.tipo]}`).join(' · ');
  /** Solo las primeras decisiones: la lista completa está en «Prácticas de la carrera». */
  protected readonly primeras = (r: ResumenCarrera) => r.decisiones.slice(0, 6);
  protected readonly estadoFiltro = (estado: string) => ({ estado });
}
