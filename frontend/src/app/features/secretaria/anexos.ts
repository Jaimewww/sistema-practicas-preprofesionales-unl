import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { cargando } from '../../core/estado-ui';
import { ESTADO_ANEXO, formatoFecha } from '../../core/demo';
import type { EstadoAnexo, TipoPractica } from '../../core/demo';
import { Insignia, Tarjeta, Vacio } from '../../shared/ui';
import { SecretariaApi } from './secretaria.api';
import type { FilaAnexo } from './secretaria.model';
import { aEstado, textoEstadoPractica, textoTipo, tipoAnexo } from './secretaria.util';
import { EstadoPantalla } from './ui/estado-pantalla';

/** S1 · Anexos por legalizar: lista con filtros por estado y tipo de práctica. */
@Component({
  selector: 'app-anexos',
  imports: [RouterLink, Tarjeta, Insignia, Vacio, EstadoPantalla],
  templateUrl: './anexos.html',
  styleUrl: './pantalla.css',
})
export class Anexos {
  private readonly api = inject(SecretariaApi);
  protected readonly estado = toSignal(aEstado(this.api.anexos(), (l) => l.length === 0), { initialValue: cargando<FilaAnexo[]>() });

  protected readonly estadoFiltro = signal<EstadoAnexo | ''>('pendiente');
  protected readonly tipo = signal<TipoPractica | ''>('');
  /** «Simular bandeja vacía»: muestra la variante sin filas, como el prototipo. */
  protected readonly simularVacio = signal(false);

  protected readonly visibles = computed(() => {
    const e = this.estado();
    if (e.tipo !== 'exito' || this.simularVacio()) return [];
    return e.datos.filter((f) => (!this.estadoFiltro() || f.anexo.estado === this.estadoFiltro()) && (!this.tipo() || f.practica.tipo === this.tipo()));
  });

  protected readonly tituloVacio = computed(() => (this.estadoFiltro() === 'pendiente' ? 'No hay anexos pendientes de legalización' : 'No hay anexos con estos filtros'));
  protected readonly textoVacio = computed(() =>
    this.estadoFiltro() === 'pendiente'
      ? 'Cuando legalice los anexos de la lista, aquí no quedará nada pendiente. Los legalizados se consultan con el filtro «Legalizados».'
      : 'Pruebe con otro estado o tipo de práctica, o use «Limpiar».',
  );

  protected readonly tipoAnexo = tipoAnexo;
  protected readonly textoTipo = textoTipo;
  protected readonly textoEstadoPractica = textoEstadoPractica;
  protected readonly textoAnexo = (estado: EstadoAnexo) => ESTADO_ANEXO[estado];
  protected readonly fecha = formatoFecha;
  protected readonly valor = (ev: Event): string => (ev.target as HTMLSelectElement).value;
  protected readonly parametros = (id: number) => ({ a: id });

  protected limpiar(): void {
    this.estadoFiltro.set('pendiente');
    this.tipo.set('');
    this.simularVacio.set(false);
  }
}
