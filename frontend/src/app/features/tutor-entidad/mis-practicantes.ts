import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { avanceDe } from '../../core/demo';
import type { Practica } from '../../core/demo';
import { cargando } from '../../core/estado-ui';
import { Aviso, Insignia, Tarjeta, Vacio } from '../../shared/ui';
import { TutorEntidadApi } from './tutor-entidad.api';
import { aEstado, subtipoTitulo, textoEstadoPractica, tipoEstadoPractica } from './tutor-entidad.util';
import { EstadoPantalla } from './ui/estado-pantalla';

type FiltroAvance = '' | 'rezagada' | 'aldia';

/** R1 · Mis practicantes: práctica laboral con estado y horas, filtros y accesos al informe externo y al incumplimiento. */
@Component({
  selector: 'app-mis-practicantes',
  imports: [RouterLink, Tarjeta, Insignia, Aviso, Vacio, EstadoPantalla],
  templateUrl: './mis-practicantes.html',
  styleUrls: ['./pantalla.css'],
})
export class MisPracticantes {
  private readonly api = inject(TutorEntidadApi);
  protected readonly estado = toSignal(aEstado(this.api.practicantes()), { initialValue: cargando<Practica[]>() });

  protected readonly busqueda = signal('');
  protected readonly avanceFiltro = signal<FiltroAvance>('');
  /** Variante «sin practicantes» (`?vacio=1` o el botón de demostración). */
  protected readonly sinPracticantes = signal(inject(ActivatedRoute).snapshot.queryParamMap.get('vacio') === '1');

  protected readonly practicantes = computed(() => {
    const e = this.estado();
    return e.tipo === 'exito' ? e.datos : [];
  });
  protected readonly visibles = computed(() => {
    const texto = this.busqueda().trim().toLowerCase();
    const filtro = this.avanceFiltro();
    return this.practicantes().filter((p) => {
      if (texto && !p.estudiante.toLowerCase().includes(texto)) return false;
      if (filtro && (filtro === 'rezagada') !== avanceDe(p).rezagada) return false;
      return true;
    });
  });

  protected readonly avance = avanceDe;
  protected readonly subtipoTitulo = subtipoTitulo;
  protected readonly textoEstado = textoEstadoPractica;
  protected readonly tipoEstado = tipoEstadoPractica;
  protected pct = (horas: number, requeridas: number): number => Math.round((horas / requeridas) * 1000) / 10;
}
