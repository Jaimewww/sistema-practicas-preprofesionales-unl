import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { cargando } from '../../core/estado-ui';
import { Aviso, Insignia, Kpi, KpiGrid, Tarjeta } from '../../shared/ui';
import { SecretariaApi } from './secretaria.api';
import type { ResumenSecretaria } from './secretaria.model';
import { aEstado, tipoAnexo } from './secretaria.util';
import { EstadoPantalla } from './ui/estado-pantalla';
import { ESTADO_ANEXO } from '../../core/demo';

/** S0 · Tablero de Secretaría: anexos por legalizar y los siguientes de la lista. */
@Component({
  selector: 'app-tablero-secretaria',
  imports: [RouterLink, Tarjeta, Aviso, Insignia, Kpi, KpiGrid, EstadoPantalla],
  templateUrl: './tablero-secretaria.html',
  styleUrl: './pantalla.css',
})
export class TableroSecretaria {
  private readonly api = inject(SecretariaApi);
  protected readonly estado = toSignal(aEstado(this.api.resumen()), { initialValue: cargando<ResumenSecretaria>() });
  protected readonly tipoAnexo = tipoAnexo;
  protected readonly textoAnexo = (a: { estado: 'pendiente' | 'legalizado' }) => ESTADO_ANEXO[a.estado];
}
