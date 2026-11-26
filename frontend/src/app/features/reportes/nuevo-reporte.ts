import { Component, signal } from '@angular/core';
import { SelectorPractica } from '../practicas/selector-practica/selector-practica';
import { RegistrarReporte } from './registrar-reporte/registrar-reporte';

/**
 * Ruta /reportes/nuevo: une el selector (Doménica) con el formulario E4 (Melissa).
 * RESPONSABLE: Melissa. El título lo pone el banner del Shell (título de la ruta). El padre guarda la práctica elegida y se la pasa a E4.
 */
@Component({
  selector: 'app-nuevo-reporte',
  imports: [SelectorPractica, RegistrarReporte],
  template: `
    <div class="pagina">
      <app-selector-practica (seleccion)="practicaId.set($event)" />
      <app-registrar-reporte [practicaId]="practicaId()" />
    </div>
  `,
  styles: `
    .pagina {
      display: grid;
      gap: var(--espacio-5);
    }
  `,
})
export class NuevoReporte {
  readonly practicaId = signal(1);
}
