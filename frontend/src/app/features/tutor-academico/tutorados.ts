import { Component, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { avanceDe, PERIODO, UMBRAL_REZAGO } from '../../core/demo';
import type { Practica } from '../../core/demo';
import { cargando } from '../../core/estado-ui';
import { Insignia, Kpi, KpiGrid, Tarjeta, Vacio } from '../../shared/ui';
import { TutorAcademicoApi } from './tutor-academico.api';
import { aEstado, avanceTexto, claveAvance, descripcionPractica, textoPractica, tipoPractica } from './tutor-academico.util';
import { EstadoPantalla } from './ui/estado-pantalla';

/** T3 · Mis tutorados: las prácticas que tutoriza, con estado, horas y si van al día o rezagadas. */
@Component({
  selector: 'app-tutorados',
  imports: [RouterLink, Tarjeta, Insignia, Kpi, KpiGrid, Vacio, EstadoPantalla],
  templateUrl: './tutorados.html',
  styleUrl: './pantalla.css',
  styles: `
    .mini {
      position: relative;
      min-width: 110px;
      height: 10px;
      margin-top: 6px;
      background: var(--horas-pista);
      border-radius: 999px;
    }
    .mini .v,
    .mini .r {
      position: absolute;
      top: 0;
      bottom: 0;
    }
    .mini .v {
      left: 0;
      background: var(--horas-validadas);
      border-radius: 999px 0 0 999px;
    }
    .mini .r {
      background: var(--horas-revision);
    }
  `,
})
export class Tutorados {
  private readonly api = inject(TutorAcademicoApi);
  protected readonly estado = toSignal(aEstado(this.api.tutorados(), (l) => l.length === 0), { initialValue: cargando<Practica[]>() });

  protected readonly periodo = PERIODO;
  protected readonly umbral = UMBRAL_REZAGO;
  protected readonly avance = avanceDe;
  protected readonly avanceTexto = avanceTexto;
  protected readonly descripcion = descripcionPractica;
  protected readonly tipoPractica = tipoPractica;
  protected readonly textoPractica = textoPractica;

  protected readonly busqueda = signal('');
  protected readonly estadoFiltro = signal('');
  protected readonly avanceFiltro = signal('');
  /** Variante «sin tutorados» del prototipo (`?vacio=1` o el botón). */
  protected readonly sinTutorados = signal(inject(ActivatedRoute).snapshot.queryParamMap.get('vacio') === '1');

  protected filtrar(lista: Practica[]): Practica[] {
    const q = this.busqueda().trim().toLowerCase();
    const estado = this.estadoFiltro();
    const av = this.avanceFiltro();
    return lista.filter(
      (p) => (!q || `${p.estudiante} ${this.descripcion(p)} ${p.entidad}`.toLowerCase().includes(q)) && (!estado || p.estado === estado) && (!av || claveAvance(p) === av),
    );
  }

  protected cuantas(lista: Practica[], estado: string): number {
    return lista.filter((p) => p.estado === estado).length;
  }

  protected rezagadas(lista: Practica[]): number {
    return lista.filter((p) => claveAvance(p) === 'rezagada').length;
  }

  protected valor(evento: Event): string {
    return (evento.target as HTMLInputElement | HTMLSelectElement).value;
  }

  /** Porcentaje de las horas requeridas (para la barra de cada fila). */
  protected pct(horas: number, requeridas: number): number {
    return requeridas > 0 ? Math.min(100, Math.round((horas / requeridas) * 1000) / 10) : 0;
  }
}
