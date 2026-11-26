import { Component, output } from '@angular/core';

/**
 * Selector de práctica (F-001).     RESPONSABLE: Doménica
 *
 * Pendiente: inject(PracticasApi).listar() con EstadoUi (cargando / vacío / error)
 * y emitir la práctica elegida con `seleccion` para que E4 sepa el practica_id.
 */
@Component({
  selector: 'app-selector-practica',
  template: `<p>Selector de práctica: pendiente (Doménica).</p>`,
})
export class SelectorPractica {
  readonly seleccion = output<number>();
}
