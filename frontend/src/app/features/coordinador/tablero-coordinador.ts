import { Component } from '@angular/core';
import { Tarjeta } from '../../shared/ui';

/** Marcador del tablero de «Coordinador»: el PR del rol lo reemplaza por la pantalla real. */
@Component({
  selector: 'app-tablero-coordinador',
  imports: [Tarjeta],
  template: `<app-tarjeta titulo="Pantalla en construcción" sub="El tablero de este rol llega en su propio PR." />`,
})
export class TableroCoordinador {}
