import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { cargando } from '../../core/estado-ui';
import { ESTADO_PRACTICA, periodosDe } from '../../core/demo';
import type { EstadoPractica, TipoAlerta, TipoPractica } from '../../core/demo';
import { Insignia, Tarjeta, Vacio } from '../../shared/ui';
import { CoordinadorApi } from './coordinador.api';
import type { FilaPractica } from './coordinador.model';
import { aEstado, CLAVES_ALERTA, nombrePropio, paramsPractica, textoAlerta, textoEstado, textoTipo, tipoAlerta, tipoEstado } from './coordinador.util';
import { EstadoPantalla } from './ui/estado-pantalla';

type FiltroAlerta = TipoAlerta | 'ninguna' | '';

/** C1 · Prácticas de la carrera: columnas de RF-06 y filtros por período, tipo, estado y alerta. */
@Component({
  selector: 'app-practicas-carrera',
  imports: [RouterLink, Tarjeta, Insignia, Vacio, EstadoPantalla],
  templateUrl: './practicas-carrera.html',
  styleUrls: ['./pantalla.css', './practicas-carrera.css'],
})
export class PracticasCarrera {
  private readonly api = inject(CoordinadorApi);
  protected readonly estado = toSignal(aEstado(this.api.practicas(), (l) => l.length === 0), { initialValue: cargando<FilaPractica[]>() });

  protected readonly periodo = signal('');
  protected readonly tipo = signal<TipoPractica | ''>('');
  protected readonly estadoFiltro = signal<EstadoPractica | ''>(this.inicial());
  protected readonly alerta = signal<FiltroAlerta>('');

  protected readonly periodos = computed(() => {
    const e = this.estado();
    return e.tipo === 'exito' ? periodosDe(e.datos.map((f) => f.practica)) : [];
  });
  protected readonly visibles = computed(() => {
    const e = this.estado();
    if (e.tipo !== 'exito') return [];
    const [per, tip, est, ale] = [this.periodo(), this.tipo(), this.estadoFiltro(), this.alerta()];
    return e.datos.filter(
      (f) =>
        (!per || f.practica.periodo === per) &&
        (!tip || f.practica.tipo === tip) &&
        (!est || f.practica.estado === est) &&
        (!ale || (ale === 'ninguna' ? f.alertas.length === 0 : f.alertas.some((a) => a.tipo === ale))),
    );
  });

  protected readonly estados = Object.entries(ESTADO_PRACTICA) as Array<[EstadoPractica, string]>;
  protected readonly clavesAlerta = CLAVES_ALERTA;
  protected readonly textoAlerta = textoAlerta;
  protected readonly tipoAlerta = tipoAlerta;
  protected readonly textoEstado = textoEstado;
  protected readonly tipoEstado = tipoEstado;
  protected readonly textoTipo = textoTipo;
  protected readonly nombrePropio = nombrePropio;
  protected readonly paramsPractica = paramsPractica;
  protected readonly rezagada = (f: FilaPractica): boolean => f.alertas.some((a) => a.tipo === 'rezago');
  protected readonly pct = (horas: number, requeridas: number): number => (requeridas ? Math.min(100, Math.round((horas / requeridas) * 1000) / 10) : 0);

  protected limpiar(): void {
    this.periodo.set('');
    this.tipo.set('');
    this.estadoFiltro.set('');
    this.alerta.set('');
  }

  protected valor(evento: Event): string {
    return (evento.target as HTMLSelectElement).value;
  }

  /** El tablero enlaza con `?estado=`; solo se acepta un estado conocido. */
  private inicial(): EstadoPractica | '' {
    const q = inject(ActivatedRoute).snapshot.queryParamMap.get('estado');
    return (Object.keys(ESTADO_PRACTICA) as EstadoPractica[]).find((e) => e === q) ?? '';
  }
}
