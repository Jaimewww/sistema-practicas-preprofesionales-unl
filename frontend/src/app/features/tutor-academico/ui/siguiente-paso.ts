import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Tarjeta } from '../../../shared/ui';

/** Tarjeta «Siguiente paso» de T2 cuando el documento ya está decidido: volver a la bandeja. */
@Component({
  selector: 'app-siguiente-paso',
  imports: [RouterLink, Tarjeta],
  host: { style: 'display: contents' }, // la tarjeta interior es la que ocupa columnas en .grilla
  template: `
    <app-tarjeta titulo="Siguiente paso" [span]="12">
      <div class="acciones-fila">
        <a class="boton-secundario" routerLink="/tutor-academico/pendientes">Volver a pendientes de revisión</a>
      </div>
    </app-tarjeta>
  `,
  styleUrl: '../pantalla.css',
})
export class SiguientePaso {}
