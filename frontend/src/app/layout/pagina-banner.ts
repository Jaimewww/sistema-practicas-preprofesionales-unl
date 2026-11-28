import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';

export interface Miga {
  texto: string;
  /** Sin enlace = página actual. */
  enlace?: string;
}

/**
 * Banner de página (docs/diseno/): degradado marino, círculos decorativos, ruta y título.
 * Con `foto` (tableros) muestra el campus, sin migas y con el saludo proyectado en `[saludo]`.
 */
@Component({
  selector: 'app-pagina-banner',
  imports: [RouterLink],
  template: `
    <section class="banner" [class.banner--foto]="foto()" [attr.aria-label]="foto() ? 'Bienvenida' : 'Encabezado de la página'">
      @if (foto()) {
        <img class="escena" src="/img/campus-unl.jpg" alt="" />
        <div class="sombra"></div>
      }
      <div class="texto">
        @if (!foto()) {
        <nav aria-label="Ruta">
          <ol class="migas">
            @for (miga of migas(); track miga.texto; let primera = $first) {
              <li>
                @if (miga.enlace) {
                  <a [routerLink]="miga.enlace">
                    @if (primera) {
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 11l9-8 9 8" /><path d="M5 10v10h5v-6h4v6h5V10" /></svg>
                    }{{ miga.texto }}
                  </a>
                } @else {
                  <span aria-current="page">{{ miga.texto }}</span>
                }
              </li>
            }
          </ol>
        </nav>
        }
        <h2 class="titulo">{{ titulo() }}</h2>
        @if (foto()) {
          <p class="saludo"><ng-content select="[saludo]" /><i></i></p>
        }
      </div>
    </section>
  `,
  styleUrl: './pagina-banner.css',
})
export class PaginaBanner {
  readonly titulo = input.required<string>();
  readonly migas = input<Miga[]>([]);
  /** Variante de los tableros: foto del campus y saludo. */
  readonly foto = input(false);
}
