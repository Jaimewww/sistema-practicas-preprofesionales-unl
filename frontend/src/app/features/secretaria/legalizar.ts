import { Component, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { distinctUntilChanged, map, switchMap } from 'rxjs';
import { ApiError } from '../../core/api/envelope';
import { cargando, type EstadoUi } from '../../core/estado-ui';
import { mensajeDeError } from '../../core/errores';
import { ESTADO_ANEXO, formatoFecha } from '../../core/demo';
import { Aviso, Insignia, Tarjeta } from '../../shared/ui';
import { SecretariaApi } from './secretaria.api';
import type { FilaAnexo } from './secretaria.model';
import { aEstado, idAnexo, textoEstadoPractica, textoTipo, tipoAnexo } from './secretaria.util';
import { EstadoPantalla } from './ui/estado-pantalla';

/** Anexo que se muestra cuando la URL no trae `?a=` (como en el prototipo). */
export const ANEXO_POR_DEFECTO = 802;

/** S2 · Legalizar anexo: una sola vez, con autor y fecha; no cambia el estado de la práctica (RF-20). */
@Component({
  selector: 'app-legalizar',
  imports: [RouterLink, Tarjeta, Aviso, Insignia, EstadoPantalla],
  templateUrl: './legalizar.html',
  styleUrl: './pantalla.css',
})
export class Legalizar {
  private readonly api = inject(SecretariaApi);
  protected readonly estado = toSignal(
    inject(ActivatedRoute).queryParamMap.pipe(
      map((q) => idAnexo(q.get('a')) ?? ANEXO_POR_DEFECTO),
      distinctUntilChanged(),
      switchMap((id) => aEstado(this.api.anexo(id))),
    ),
    { initialValue: cargando<FilaAnexo>() as EstadoUi<FilaAnexo> },
  );

  /** Resultado de la legalización hecha en esta pantalla (sustituye al anexo cargado). */
  protected readonly legalizado = signal<FilaAnexo | null>(null);
  protected readonly recienLegalizado = signal(false);
  protected readonly errorLegalizar = signal('');
  protected readonly enCurso = signal(false);

  protected readonly tipoAnexo = tipoAnexo;
  protected readonly textoTipo = textoTipo;
  protected readonly textoEstadoPractica = textoEstadoPractica;
  protected readonly textoAnexo = (a: FilaAnexo['anexo']) => ESTADO_ANEXO[a.estado];
  protected readonly fecha = formatoFecha;
  protected readonly actual = (cargada: FilaAnexo): FilaAnexo => {
    const l = this.legalizado();
    return l && l.anexo.id === cargada.anexo.id ? l : cargada;
  };

  protected legalizar(id: number): void {
    this.enCurso.set(true);
    this.errorLegalizar.set('');
    this.api.legalizar(id).subscribe({
      next: (fila) => {
        this.legalizado.set(fila);
        this.recienLegalizado.set(true);
        this.enCurso.set(false);
      },
      error: (e: unknown) => {
        this.errorLegalizar.set(e instanceof ApiError ? mensajeDeError(e) : 'No se pudo legalizar el anexo.');
        this.enCurso.set(false);
      },
    });
  }
}
