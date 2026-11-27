import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { avanceDe, formatoFecha } from '../../core/demo';
import type { Practica } from '../../core/demo';
import { cargando } from '../../core/estado-ui';
import { Insignia, Kpi, KpiGrid, Tarjeta, Vacio } from '../../shared/ui';
import { TutorEntidadApi } from './tutor-entidad.api';
import type { ReporteConfirmable } from './tutor-entidad.model';
import { aEstado, nombreCorto, subtipoTitulo } from './tutor-entidad.util';
import { EstadoPantalla } from './ui/estado-pantalla';

interface DatosTablero {
  practicantes: Practica[];
  reportes: ReporteConfirmable[];
}

/** TE0 · Tablero del tutor de la entidad: reportes por confirmar, practicantes y accesos rápidos. */
@Component({
  selector: 'app-tablero-tutor-entidad',
  imports: [RouterLink, Tarjeta, Insignia, Kpi, KpiGrid, Vacio, EstadoPantalla],
  templateUrl: './tablero-tutor-entidad.html',
  styleUrls: ['./pantalla.css'],
})
export class TableroTutorEntidad {
  private readonly api = inject(TutorEntidadApi);
  protected readonly estado = toSignal(
    aEstado(forkJoin({ practicantes: this.api.practicantes(), reportes: this.api.reportesPorConfirmar() }), (d) => d.practicantes.length === 0),
    { initialValue: cargando<DatosTablero>() },
  );
  protected readonly avance = avanceDe;
  protected readonly nombreCorto = nombreCorto;
  protected readonly nombres = (lista: Practica[]): string => lista.map((p) => nombreCorto(p.estudiante)).join(', ');
  protected readonly subtipoTitulo = subtipoTitulo;
  protected readonly formatoFecha = formatoFecha;
}
