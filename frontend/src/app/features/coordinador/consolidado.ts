import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { cargando } from '../../core/estado-ui';
import { formatoFecha, HOY, PERIODO, PERIODO_ANTERIOR } from '../../core/demo';
import type { TipoPractica } from '../../core/demo';
import { Aviso, Insignia, Tarjeta, Vacio } from '../../shared/ui';
import { CoordinadorApi } from './coordinador.api';
import type { FilaConsolidado } from './coordinador.model';
import { construirCsv, descargarCsv, textoComponente, textoResultado } from './csv.util';
import { aEstado, nombrePropio } from './coordinador.util';
import { EstadoPantalla } from './ui/estado-pantalla';

/** C6 · Consolidado de la carrera por estudiante y componente, con exportación real a CSV (RNF-10). */
@Component({
  selector: 'app-consolidado',
  imports: [Aviso, Insignia, Tarjeta, Vacio, EstadoPantalla],
  templateUrl: './consolidado.html',
  styleUrl: './pantalla.css',
})
export class Consolidado {
  private readonly api = inject(CoordinadorApi);
  protected readonly estado = toSignal(aEstado(this.api.consolidado()), { initialValue: cargando<FilaConsolidado[]>() });
  protected readonly periodo = signal<string>(PERIODO);
  protected readonly componente = signal<TipoPractica | ''>('');
  protected readonly generado = signal('');

  /** Solo las filas visibles: lo mismo que se exporta. */
  protected readonly visibles = computed(() => {
    const e = this.estado();
    if (e.tipo !== 'exito') return [];
    return e.datos.filter((f) => (!this.periodo() || f.periodo === this.periodo()) && (!this.componente() || f.componente === this.componente()));
  });

  protected readonly periodos = [PERIODO, PERIODO_ANTERIOR];
  protected readonly nombrePropio = nombrePropio;
  protected readonly textoComponente = textoComponente;
  protected readonly textoResultado = textoResultado;
  protected readonly formatoFecha = formatoFecha;

  protected valor(evento: Event): string {
    return (evento.target as HTMLSelectElement).value;
  }

  protected limpiar(): void {
    this.periodo.set(PERIODO);
    this.componente.set('');
  }

  protected exportar(): void {
    const nombre = `consolidado-computacion-${HOY}.csv`;
    descargarCsv(nombre, construirCsv(this.visibles()));
    this.generado.set(nombre);
  }
}
