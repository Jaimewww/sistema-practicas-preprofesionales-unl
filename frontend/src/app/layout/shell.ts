import { Component, computed, DestroyRef, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRouteSnapshot, NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter, map, startWith } from 'rxjs';
import { environment } from '../../environments/environment';
import { PERIODO, SEMANA_ACTUAL, TOTAL_SEMANAS } from '../core/demo';
import { ROLES, rolDeUrl, rutaTablero } from './menu-roles';
import { Miga, PaginaBanner } from './pagina-banner';

/** Quita el sufijo « · Prácticas UNL» que el título de ruta usa para el <title> del documento. */
const SUFIJO_TITULO = / · Prácticas UNL$/;

interface DatosRuta {
  titulo: string;
  migas: Miga[] | null;
  foto: boolean;
}

/** Recorre la rama activa: `data.titulo`/`migas`/`foto` de la ruta más profunda que los defina; si no, su `title`. */
function datosDeLaRuta(raiz: ActivatedRouteSnapshot): DatosRuta {
  let ruta: ActivatedRouteSnapshot | null = raiz;
  let titulo: string | undefined;
  let migas: Miga[] | undefined;
  let foto = false;
  let tituloRuta: string | undefined;
  while (ruta) {
    const datos = ruta.routeConfig?.data;
    if (datos?.['titulo']) titulo = datos['titulo'] as string;
    if (datos?.['migas']) migas = datos['migas'] as Miga[];
    if (datos) foto = datos['foto'] === true;
    tituloRuta = ruta.title ?? tituloRuta;
    ruta = ruta.firstChild;
  }
  return { titulo: titulo ?? (tituloRuta ?? '').replace(SUFIJO_TITULO, ''), migas: migas ?? null, foto };
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

  /** Solo con datos simulados se ofrece «Cambiar de rol (demo)». */
  readonly demo = environment.useMock;
  readonly roles = ROLES;
  readonly rutaTablero = rutaTablero;

  /** Periodo que muestra la tarjeta lateral (valores de la propuesta de diseño). */
  readonly periodo = { nombre: PERIODO, semana: SEMANA_ACTUAL, semanas: TOTAL_SEMANAS };
  readonly avancePeriodo = Math.round((this.periodo.semana / this.periodo.semanas) * 100);

  private readonly navegacion = toSignal(
    this.router.events.pipe(
      filter((e) => e instanceof NavigationEnd),
      map(() => this.leerNavegacion()),
      startWith(this.leerNavegacion()),
    ),
    { initialValue: { url: '/', datos: { titulo: '', migas: null, foto: false } } },
  );

  private leerNavegacion() {
    return { url: this.router.url, datos: datosDeLaRuta(this.router.routerState.snapshot.root) };
  }

  /** Rol activo: el primer segmento de la URL (`/`, `/login` y `/reportes/nuevo` muestran el del estudiante). */
  readonly rol = computed(() => rolDeUrl(this.navegacion().url));
  /** Notificaciones sin leer; el contador solo se pinta si hay alguna. */
  readonly notificaciones = computed(() => this.rol().campana);
  readonly foto = computed(() => this.navegacion().datos.foto);
  readonly titulo = computed(() => this.navegacion().datos.titulo || 'Prácticas preprofesionales');
  readonly migas = computed<Miga[]>(() => this.navegacion().datos.migas ?? [{ texto: 'Inicio', enlace: '/' }, { texto: this.titulo() }]);
  /** Primer nombre de la persona de demostración, para el saludo del tablero. */
  readonly saludo = computed(() => `¡Hola, ${this.rol().persona.nombre.split(' ')[0]}!`);

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
