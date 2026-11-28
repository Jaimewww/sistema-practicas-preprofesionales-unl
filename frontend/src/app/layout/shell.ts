import { Component, computed, DestroyRef, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import {
  ActivatedRouteSnapshot,
  NavigationEnd,
  Router,
  RouterLink,
  RouterLinkActive,
  RouterOutlet,
} from '@angular/router';
import { filter, map, startWith } from 'rxjs';
import { DEMO_MODE } from '../core/auth/dashboard.guard';
import { SesionService } from '../core/auth/sesion.service';
import { PERIODO, SEMANA_ACTUAL, TOTAL_SEMANAS } from '../core/demo';
import { accountMenu, ROLES, rolDeUrl, rutaTablero } from './menu-roles';
import { Mascota } from './mascota';
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
  return {
    titulo: titulo ?? (tituloRuta ?? '').replace(SUFIJO_TITULO, ''),
    migas: migas ?? null,
    foto,
  };
}

/**
 * Armazón de la app (docs/diseno/): barra lateral marino, barra superior flotante,
 * banner con el título de la ruta y pie. Por debajo de 1100 px la barra lateral es un
 * panel superpuesto que se abre con el botón de menú.
 *
 * En modo demo el rol sale de la URL y la persona es la del prototipo; en modo real
 * el rol y el nombre salen del perfil de `/me/` (solo las cuentas del backend).
 */
@Component({
  selector: 'app-shell',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, PaginaBanner, Mascota],
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
  readonly demo = inject(DEMO_MODE);
  /** Fuera del demo el armazón muestra la cuenta que entró; sin sesión no se inyecta. */
  private readonly session = this.demo ? null : inject(SesionService);
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

  /** Rol activo: el perfil de la cuenta en modo real; en demo, el primer segmento de la URL. */
  readonly rol = computed(
    () => accountMenu(this.session?.perfil()?.rol ?? '') ?? rolDeUrl(this.navegacion().url),
  );
  /** Nombre y siglas de la persona: la de demostración o la de la cuenta autenticada. */
  readonly persona = computed(() => {
    if (this.demo) return this.rol().persona;
    const nombre = this.session?.perfil()?.nombre.trim() || 'Usuario';
    const siglas = nombre
      .split(/\s+/)
      .slice(0, 2)
      .map((part) => part.charAt(0))
      .join('')
      .toUpperCase();
    return { nombre, siglas };
  });
  /** Notificaciones sin leer; el contador solo se pinta si hay alguna. */
  readonly notificaciones = computed(() => (this.demo ? this.rol().campana : 0));
  readonly foto = computed(() => this.navegacion().datos.foto);
  readonly titulo = computed(() => this.navegacion().datos.titulo || 'Prácticas preprofesionales');
  readonly migas = computed<Miga[]>(
    () =>
      this.navegacion().datos.migas ?? [{ texto: 'Inicio', enlace: '/' }, { texto: this.titulo() }],
  );
  /** Primer nombre de la persona, para el saludo del tablero y la mascota. */
  readonly primerNombre = computed(() => this.persona().nombre.split(' ')[0]);
  readonly saludo = computed(() => `¡Hola, ${this.primerNombre()}!`);

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
