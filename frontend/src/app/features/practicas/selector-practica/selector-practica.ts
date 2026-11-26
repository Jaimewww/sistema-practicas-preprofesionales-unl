import { Component, inject, OnInit, output, signal } from '@angular/core';
import { estadoDeError } from '../../../core/errores';
import { cargando, exito, inicial, vacio, type EstadoUi } from '../../../core/estado-ui';
import type { Practica } from '../practica.model';
import { PracticasApi } from '../practicas.api';

/** Selector de práctica (F-001). RESPONSABLE: Doménica. */
@Component({
  selector: 'app-selector-practica',
  template: `
    <section class="tarjeta" aria-labelledby="titulo-selector-practica">
      <h2 id="titulo-selector-practica">Práctica</h2>
      @let e = estado();

      @if (e.tipo === 'inicial' || e.tipo === 'cargando') {
        <p class="aviso aviso-info" role="status">Cargando prácticas…</p>
      }

      @if (e.tipo === 'vacio') {
        <p class="aviso aviso-info" role="status">No tenés prácticas activas</p>
      }

      @if (e.tipo === 'error') {
        <p class="aviso aviso-error" role="alert">{{ e.mensaje }}</p>
      }

      @if (e.tipo === 'exito') {
        <p class="ayuda">Elegí la práctica para la que querés registrar horas semanales.</p>
        <div class="campo">
          <label for="selector-practica">Práctica</label>
          <select id="selector-practica" (change)="elegir($event)">
            <option value="" disabled>Seleccioná una práctica</option>
            @for (practica of e.datos; track practica.id) {
              <option [value]="practica.id" [attr.data-practica-id]="practica.id">
                #{{ practica.id }} — {{ practica.tipo }} / {{ practica.subtipo }} ({{
                  practica.estado
                }})
              </option>
            }
          </select>
        </div>
      }
    </section>
  `,
  styles: `
    h2 {
      margin: 0 0 var(--espacio-4);
      color: var(--color-primario);
      font-size: 20px;
    }

    .ayuda {
      margin: 0 0 var(--espacio-4);
      color: var(--color-texto-suave);
      font-size: 13px;
    }
  `,
})
export class SelectorPractica implements OnInit {
  private readonly practicasApi = inject(PracticasApi);

  readonly estado = signal<EstadoUi<Practica[]>>(inicial());
  readonly seleccion = output<number>();

  ngOnInit(): void {
    this.estado.set(cargando());
    this.practicasApi.listar().subscribe({
      next: (practicas) =>
        this.estado.set(practicas.length === 0 ? vacio<Practica[]>() : exito(practicas)),
      error: (error: unknown) => this.estado.set(estadoDeError<Practica[]>(error)),
    });
  }

  elegir(event: Event): void {
    const id = Number((event.target as HTMLSelectElement).value);
    if (Number.isInteger(id)) {
      this.seleccion.emit(id);
    }
  }
}
