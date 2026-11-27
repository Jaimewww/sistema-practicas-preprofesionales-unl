import { Component, inject, linkedSignal, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { distinctUntilChanged, map, switchMap } from 'rxjs';
import { formatoFecha, TUTOR_ENTIDAD } from '../../core/demo';
import { estadoDeError } from '../../core/errores';
import { cargando } from '../../core/estado-ui';
import { Aviso, Insignia, Tarjeta } from '../../shared/ui';
import { TutorEntidadApi } from './tutor-entidad.api';
import type { Confirmacion, ReporteConfirmable } from './tutor-entidad.model';
import { aEstado, nombreCorto, rango, textoPracticaLarga, textoRevision, tipoRevision } from './tutor-entidad.util';
import { EstadoPantalla } from './ui/estado-pantalla';

/** Reporte que se muestra cuando la URL no trae `?r=`: la semana 8 de Luciana. */
export const REPORTE_POR_DEFECTO = 'l8';

/** R3 · Confirmar reporte: el reporte semanal del practicante (por confirmar, ya confirmado o devuelto) y «Confirmar». */
@Component({
  selector: 'app-confirmar-reporte',
  imports: [RouterLink, Tarjeta, Insignia, Aviso, EstadoPantalla],
  templateUrl: './confirmar-reporte.html',
  styleUrls: ['./pantalla.css'],
})
export class ConfirmarReporte {
  private readonly api = inject(TutorEntidadApi);
  private readonly codigo$ = inject(ActivatedRoute).queryParamMap.pipe(
    map((q) => q.get('r') || REPORTE_POR_DEFECTO),
    distinctUntilChanged(),
  );
  protected readonly codigo = toSignal(this.codigo$, { initialValue: REPORTE_POR_DEFECTO });
  protected readonly estado = toSignal(
    this.codigo$.pipe(switchMap((c) => aEstado(this.api.reporte(c)))),
    { initialValue: cargando<ReporteConfirmable>() },
  );

  /** Confirmación hecha en esta pantalla (se olvida al cambiar de reporte). */
  protected readonly confirmado = linkedSignal<unknown, Confirmacion | null>({ source: this.codigo, computation: () => null });
  protected readonly error = linkedSignal<unknown, string>({ source: this.codigo, computation: () => '' });
  protected readonly enviando = signal(false);

  protected readonly ejemplos = [
    { r: 'l8', texto: 'Luciana · semana 8' },
    { r: 'l7', texto: 'Luciana · semana 7' },
    { r: 'd7', texto: 'Diego · semana 7' },
    { r: 'd8', texto: 'Ya confirmado (Diego · semana 8)' },
    { r: 'l5', texto: 'Devuelto (Luciana · semana 5)' },
  ];

  protected readonly formatoFecha = formatoFecha;
  protected readonly rango = rango;
  protected readonly nombreCorto = nombreCorto;
  protected readonly textoPracticaLarga = textoPracticaLarga;
  protected readonly textoRevision = textoRevision;
  protected readonly tipoRevision = tipoRevision;
  protected readonly tutora = TUTOR_ENTIDAD;

  /** Quién confirmó y cuándo: lo ya registrado o lo recién confirmado. */
  protected confirmacionDe(r: ReporteConfirmable): Confirmacion | null {
    return this.confirmado() ?? r.confirmacion;
  }

  protected confirmar(): void {
    this.error.set('');
    this.enviando.set(true);
    this.api.confirmarReporte(this.codigo()).subscribe({
      next: (c) => {
        this.enviando.set(false);
        this.confirmado.set(c);
      },
      error: (e: unknown) => {
        this.enviando.set(false);
        const r = estadoDeError<void>(e);
        this.error.set(r.tipo === 'error' ? r.mensaje : 'No se pudo confirmar el reporte.');
      },
    });
  }
}
