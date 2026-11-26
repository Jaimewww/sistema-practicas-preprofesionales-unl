import { Component, computed, DestroyRef, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRouteSnapshot, NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter, map, startWith } from 'rxjs';
import { Miga, PaginaBanner } from './pagina-banner';

/** Quita el sufijo « · Prácticas UNL» que el título de ruta usa para el <title> del documento. */
const SUFIJO_TITULO = / · Prácticas UNL$/;

function tituloDeLaRuta(raiz: ActivatedRouteSnapshot): string {
  let ruta = raiz;
  let titulo = ruta.title;
  while (ruta.firstChild) {
    ruta = ruta.firstChild;
    titulo = ruta.title ?? titulo;
  }
  return (titulo ?? '').replace(SUFIJO_TITULO, '');
}

/**
 * Armazón de la app (docs/diseno/): barra lateral marino, barra superior flotante,
 * banner con el título de la ruta y pie. Por debajo de 1100 px la barra lateral es un
 * panel superpuesto que se abre con el botón de menú.
 */
@Component({
  selector: 'app-shell',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, PaginaBanner],
  templateUrl: './shell.html',
  styleUrl: './shell.css',
  host: { '(document:keydown.escape)': 'cerrarMenu()' },
})
export class Shell {
  private readonly router = inject(Router);

  /** Barra lateral abierta (solo se nota por debajo de 1100 px). */
  readonly menuAbierto = signal(false);
  readonly practicasAbierto = signal(true);
  readonly usuarioAbierto = signal(false);
  /** Notificaciones sin leer; el contador solo se pinta si hay alguna. */
  readonly notificaciones = signal(0);

  /** Periodo que muestra la tarjeta lateral (valores de la propuesta de diseño). */
  readonly periodo = { nombre: 'MAR.26-AGO.26 GRADO', semana: 9, semanas: 16 };
  readonly avancePeriodo = Math.round((this.periodo.semana / this.periodo.semanas) * 100);

  private readonly navegacion = toSignal(
    this.router.events.pipe(
      filter((e) => e instanceof NavigationEnd),
      map(() => tituloDeLaRuta(this.router.routerState.snapshot.root)),
      startWith(tituloDeLaRuta(this.router.routerState.snapshot.root)),
    ),
    { initialValue: '' },
  );

  readonly titulo = computed(() => this.navegacion() || 'Prácticas preprofesionales');
  readonly migas = computed<Miga[]>(() => [{ texto: 'Inicio', enlace: '/' }, { texto: this.titulo() }]);

  constructor() {
    const sub = this.router.events.pipe(filter((e) => e instanceof NavigationEnd)).subscribe(() => {
      this.menuAbierto.set(false);
      this.usuarioAbierto.set(false);
    });
    inject(DestroyRef).onDestroy(() => sub.unsubscribe());
  }

  alternarMenu(): void {
    this.menuAbierto.update((v) => !v);
  }

  arriba(): void {
    window.scrollTo({ top: 0 });
  }

  cerrarMenu(): void {
    this.menuAbierto.set(false);
    this.usuarioAbierto.set(false);
  }
}
