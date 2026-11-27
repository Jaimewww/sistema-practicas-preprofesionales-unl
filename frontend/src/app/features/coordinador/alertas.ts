import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { cargando } from '../../core/estado-ui';
import { CONFIGURACION_CARRERA, formatoFecha } from '../../core/demo';
import type { TipoAlerta } from '../../core/demo';
import { Insignia, Kpi, KpiGrid, Tarjeta, Vacio } from '../../shared/ui';
import { CoordinadorApi } from './coordinador.api';
import type { FilaAlerta } from './coordinador.model';
import { aEstado, CLAVES_ALERTA, nombrePropio, paramsPractica, textoAlerta, textoTipo, tipoAlerta } from './coordinador.util';
import { EstadoPantalla } from './ui/estado-pantalla';

const FILAS_POR_TIPO = 5;

const GRUPOS: Record<TipoAlerta, { titulo: string; filtro: string; resumen: string; kpi: string; descripcion: string }> = {
  reporte_no_enviado: { titulo: 'Reportes no enviados', filtro: 'Reportes no enviados', kpi: 'reportes no enviados', resumen: 'Reportes no enviados', descripcion: `La semana se cerró y el plazo de reporte (${CONFIGURACION_CARRERA.plazoReporteDias} días) venció.` },
  revision_pendiente: { titulo: 'Revisiones pendientes', filtro: 'Revisiones pendientes', kpi: 'revisiones pendientes', resumen: 'Revisiones pendientes', descripcion: `El tutor académico superó el plazo de revisión (${CONFIGURACION_CARRERA.plazoRevisionDias} días hábiles).` },
  rezago: { titulo: 'Horas rezagadas', filtro: 'Horas rezagadas', kpi: 'prácticas bajo el umbral', resumen: 'Horas rezagadas', descripcion: `Horas validadas y en revisión por debajo del umbral del ${CONFIGURACION_CARRERA.umbralRezago} % de las esperadas.` },
  incumplimiento: { titulo: 'Incumplimientos reportados', filtro: 'Incumplimientos', kpi: 'reportados por la entidad', resumen: 'Incumplimientos reportados', descripcion: 'Incumplimientos que registró el tutor de la entidad.' },
};

/** C2 · Alertas activas agrupadas por tipo, con filtro y estado vacío de demostración. */
@Component({
  selector: 'app-alertas',
  imports: [RouterLink, Tarjeta, Insignia, Kpi, KpiGrid, Vacio, EstadoPantalla],
  templateUrl: './alertas.html',
  styleUrl: './pantalla.css',
})
export class Alertas {
  private readonly api = inject(CoordinadorApi);
  protected readonly estado = toSignal(aEstado(this.api.alertas()), { initialValue: cargando<FilaAlerta[]>() });
  protected readonly filtro = signal<TipoAlerta | ''>('');
  protected readonly sinAlertas = signal(false);

  /** Grupos con sus filas (las más recientes primero) y el total real. */
  protected readonly grupos = computed(() => {
    const e = this.estado();
    if (e.tipo !== 'exito' || this.sinAlertas()) return [];
    return CLAVES_ALERTA.filter((t) => !this.filtro() || t === this.filtro())
      .map((tipo) => {
        const todas = e.datos.filter((f) => f.alerta.tipo === tipo).sort((a, b) => (a.alerta.fecha < b.alerta.fecha ? 1 : a.alerta.fecha > b.alerta.fecha ? -1 : b.alerta.practicaId - a.alerta.practicaId));
        return { tipo, total: todas.length, filas: todas.slice(0, FILAS_POR_TIPO) };
      })
      .filter((g) => g.total > 0);
  });
  protected readonly totales = computed(() => {
    const e = this.estado();
    return CLAVES_ALERTA.map((tipo) => ({ tipo, total: e.tipo === 'exito' ? e.datos.filter((f) => f.alerta.tipo === tipo).length : 0 }));
  });

  protected readonly claves = CLAVES_ALERTA;
  protected readonly info = GRUPOS;
  protected readonly textoAlerta = textoAlerta;
  protected readonly tipoAlerta = tipoAlerta;
  protected readonly textoTipo = (f: FilaAlerta): string => textoTipo({ tipo: f.tipoPractica });
  protected readonly nombrePropio = nombrePropio;
  protected readonly paramsPractica = paramsPractica;
  protected readonly formatoFecha = formatoFecha;

  protected elegir(evento: Event): void {
    this.filtro.set((evento.target as HTMLSelectElement).value as TipoAlerta | '');
  }
}
