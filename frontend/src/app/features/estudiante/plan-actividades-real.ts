import { afterNextRender, Component, computed, inject, Injector, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { catchError, distinctUntilChanged, EMPTY, map, of, switchMap } from 'rxjs';
import { formatoFecha } from '../../core/demo';
import { cargando, exito, inicial, vacio, type EstadoUi } from '../../core/estado-ui';
import { estadoDeError } from '../../core/errores';
import { Aviso, Insignia, Pasos, Tarjeta, type PasoItem, type TipoInsignia } from '../../shared/ui';
import type { Practica } from '../practicas/practica.model';
import { PracticasApi } from '../practicas/practicas.api';
import type { EstadoPlan, PlanVersion } from './plan-informe.http';
import { PlanInformeHttp } from './plan-informe.http';
import { EstadoPantalla } from './ui/estado-pantalla';

const INSIGNIA: Record<EstadoPlan, { tipo: TipoInsignia; texto: string }> = {
  en_revision: { tipo: 'warn', texto: 'En revisión' },
  aprobado: { tipo: 'ok', texto: 'Aprobado' },
  devuelto: { tipo: 'bad', texto: 'Devuelto con observación' },
};

/** Título del historial: «Versión 2 · devuelta» como en el prototipo. */
const SUCEDE: Record<EstadoPlan, string> = {
  en_revision: 'en revisión',
  aprobado: 'aprobada',
  devuelto: 'devuelta',
};

/** Paso del historial que corresponde a cada estado: la versión anterior ya está decidida. */
const PASO: Record<EstadoPlan, PasoItem['estado']> = {
  en_revision: 'now',
  aprobado: 'done',
  devuelto: 'bad',
};

/** `?p=` como id positivo; `null` cuando falta: en modo real no se inventa la práctica 1 del demo. */
function idDeParam(valor: string | null): number | null {
  const id = Number(valor);
  return valor !== null && valor.trim() !== '' && Number.isInteger(id) && id > 0 ? id : null;
}

/** De la más nueva a la más antigua: el orden del API no es parte del contrato. */
const porVersion = (versiones: PlanVersion[]): PlanVersion[] =>
  [...versiones].sort((a, b) => b.version - a.version);

/**
 * E3 real · editor del plan de actividades (C-09) sobre `PlanInformeHttp`.
 *
 * Sin `?p=` no se adivina la práctica: se listan las visibles con `PracticasApi` y
 * la elección viaja en el mismo parámetro `?p=` que usa el resto del módulo. El plan
 * se escribe como un único `contenido` de texto (no hay actividades ni entregables
 * separados en el contrato) y solo se reenvía cuando la última versión fue devuelta;
 * un 409 del backend se muestra tal cual y conserva lo escrito.
 */
@Component({
  selector: 'app-plan-actividades-real',
  imports: [ReactiveFormsModule, Tarjeta, Pasos, Aviso, Insignia, EstadoPantalla],
  template: `
    @let e = estado();
    @if (e.tipo === 'inicial') {
      <app-tarjeta
        titulo="Plan de actividades"
        sub="Elija la práctica para la que va a presentar el plan."
      >
        <div class="cuerpo">
          <p class="ayuda">
            Elegí la práctica para la que querés presentar el plan de actividades.
          </p>
          @let lista = practicas();
          @switch (lista.tipo) {
            @case ('exito') {
              <div class="campo">
                <label for="selector-practica">Práctica</label>
                <select id="selector-practica" (change)="elegirPractica($event)">
                  <option value="" disabled selected>Elegí la práctica</option>
                  @for (p of lista.datos; track p.id) {
                    <option [value]="p.id">
                      #{{ p.id }} — {{ p.tipo }} / {{ p.subtipo }} ({{ p.estado }})
                    </option>
                  }
                </select>
              </div>
            }
            @case ('vacio') {
              <app-aviso tipo="info">No tiene prácticas visibles para presentar un plan.</app-aviso>
            }
            @case ('error') {
              <app-aviso tipo="bad">{{ lista.mensaje }}</app-aviso>
            }
            @default {
              <p class="cargando" role="status">Cargando prácticas…</p>
            }
          }
        </div>
      </app-tarjeta>
    } @else if (e.tipo === 'exito') {
      @let ultima = ultimaVersion();
      <div class="grilla">
        @if (enviado()) {
          <div class="span-12">
            <app-aviso tipo="ok"
              ><strong>Plan enviado.</strong> Quedó «en revisión» de su tutor académico.</app-aviso
            >
          </div>
        }
        @if (errorEnvio()) {
          <div class="span-12">
            <app-aviso tipo="bad">{{ errorEnvio() }}</app-aviso>
          </div>
        }
        <app-tarjeta
          [titulo]="
            ultima ? 'Plan de actividades · versión ' + ultima.version : 'Plan de actividades'
          "
          [sub]="subtitulo()"
          [span]="8"
        >
          @if (ultima) {
            <app-insignia
              acciones
              [tipo]="insignia(ultima).tipo"
              [texto]="insignia(ultima).texto"
            />
          }
          <div class="cuerpo">
            @if (editable()) {
              @if (faltaContenido()) {
                <div id="error-contenido" class="resumen-error" role="alert" tabindex="-1">
                  <p>Revise el formulario</p>
                  <ul>
                    <li>
                      <button type="button" class="enlace-boton" (click)="enfocarContenido()">
                        Escriba las actividades del plan.
                      </button>
                    </li>
                  </ul>
                </div>
              }
              <form (submit)="$event.preventDefault(); enviar()" novalidate>
                <div class="campo">
                  <label for="plan-contenido"
                    >Actividades del plan <span class="req" aria-hidden="true">*</span></label
                  >
                  <p id="ayuda-contenido" class="ayuda">
                    Describa las actividades que realizará en la práctica. El plan se envía como un
                    texto único y puede corregirlo cada vez que su tutor lo devuelva.
                  </p>
                  <textarea
                    id="plan-contenido"
                    [formControl]="contenido"
                    rows="10"
                    aria-describedby="ayuda-contenido"
                    [attr.aria-invalid]="faltaContenido() ? 'true' : null"
                  ></textarea>
                </div>
                <div class="acciones-fila acciones-form">
                  <button class="boton" type="submit" [disabled]="enviando()">
                    {{ enviando() ? 'Enviando…' : 'Enviar a revisión' }}
                  </button>
                </div>
              </form>
            } @else {
              <p class="plan-texto">{{ ultima?.contenido }}</p>
              @if (ultima?.estado === 'aprobado') {
                <p class="nota">
                  Con la aprobación del plan la práctica pasa a «en curso» y se habilita el reporte
                  semanal.
                </p>
              } @else {
                <p class="nota">
                  El plan está en revisión: cuando su tutor decida podrá corregirlo si lo devuelve.
                </p>
              }
            }
          </div>
        </app-tarjeta>
        <app-tarjeta titulo="Historial de versiones" [span]="4">
          @if (anteriores().length) {
            <app-pasos [pasos]="pasos(anteriores())" />
          } @else {
            <p class="demo">Todavía no hay versiones anteriores: esta es la primera.</p>
          }
        </app-tarjeta>
      </div>
    } @else {
      <app-estado-pantalla [estado]="e" />
    }
  `,
  styleUrls: ['./pantalla.css', './plan-actividades.css'],
  styles: `
    .plan-texto {
      margin: 0;
      white-space: pre-line;
    }
  `,
})
export class PlanActividadesReal {
  private readonly api = inject(PlanInformeHttp);
  private readonly practicasApi = inject(PracticasApi);
  private readonly ruta = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly injector = inject(Injector);

  protected readonly estado = signal<EstadoUi<PlanVersion[]>>(inicial());
  protected readonly practicas = signal<EstadoUi<Practica[]>>(inicial());
  /** Práctica elegida por `?p=`; `null` mientras no haya una. */
  protected readonly practicaId = signal<number | null>(
    idDeParam(this.ruta.snapshot.queryParamMap.get('p')),
  );
  protected readonly contenido = new FormControl('', { nonNullable: true });
  protected readonly faltaContenido = signal(false);
  protected readonly enviando = signal(false);
  protected readonly enviado = signal(false);
  protected readonly errorEnvio = signal('');

  protected readonly versiones = computed(() => {
    const e = this.estado();
    return e.tipo === 'exito' ? e.datos : [];
  });
  protected readonly ultimaVersion = computed(() => this.versiones()[0] ?? null);
  protected readonly anteriores = computed(() => this.versiones().slice(1));
  /** Solo se envía cuando no hay plan o el tutor devolvió la última versión. */
  protected readonly editable = computed(() => {
    const ultima = this.ultimaVersion();
    return ultima === null || ultima.estado === 'devuelto';
  });

  protected readonly insignia = (version: PlanVersion) => INSIGNIA[version.estado];

  constructor() {
    this.cargarPracticas();
    this.ruta.queryParamMap
      .pipe(
        map((q) => idDeParam(q.get('p'))),
        distinctUntilChanged(),
        switchMap((id) => {
          this.practicaId.set(id);
          this.enviado.set(false);
          this.faltaContenido.set(false);
          this.errorEnvio.set('');
          if (id === null) {
            this.contenido.setValue('');
            this.estado.set(inicial());
            return EMPTY;
          }
          this.estado.set(cargando());
          return this.api.versiones(id).pipe(
            map((versiones) => exito(porVersion(versiones))),
            catchError((error: unknown) => of(estadoDeError<PlanVersion[]>(error))),
          );
        }),
        takeUntilDestroyed(),
      )
      .subscribe((estado) => {
        this.estado.set(estado);
        this.contenido.setValue(this.ultimaVersion()?.contenido ?? '');
      });
  }

  protected elegirPractica(evento: Event): void {
    const id = Number((evento.target as HTMLSelectElement).value);
    if (!Number.isInteger(id) || id <= 0) return;
    void this.router.navigate([], {
      relativeTo: this.ruta,
      queryParams: { p: id },
      queryParamsHandling: 'merge',
    });
  }

  protected enviar(): void {
    const id = this.practicaId();
    const texto = this.contenido.value.trim();
    if (id === null) return;
    if (texto === '') {
      this.faltaContenido.set(true);
      this.enfocarError();
      return;
    }
    this.faltaContenido.set(false);
    this.errorEnvio.set('');
    this.enviando.set(true);
    this.api.enviarPlan(id, texto).subscribe({
      next: (version) => {
        this.enviando.set(false);
        this.estado.set(
          exito(porVersion([version, ...this.versiones().filter((v) => v.id !== version.id)])),
        );
        this.enviado.set(true);
      },
      error: (error: unknown) => {
        this.enviando.set(false);
        const resultado = estadoDeError<PlanVersion>(error);
        this.errorEnvio.set(
          resultado.tipo === 'error' ? resultado.mensaje : 'No se pudo enviar el plan.',
        );
      },
    });
  }

  protected enfocarContenido(): void {
    afterNextRender(() => document.getElementById('plan-contenido')?.focus(), {
      injector: this.injector,
    });
  }

  protected subtitulo(): string {
    const ultima = this.ultimaVersion();
    if (ultima === null) return 'Todavía no registró el plan de actividades de esta práctica.';
    const fecha = this.fechaDe(ultima.fecha_validacion);
    const sufijo = fecha === '' ? '' : ` el ${fecha}`;
    if (ultima.estado === 'aprobado') return `Aprobado${sufijo}.`;
    if (ultima.estado === 'devuelto') return `Devuelto${sufijo}: corrija el texto y reenvíelo.`;
    return 'Esperando la revisión de su tutor académico.';
  }

  protected pasos(versiones: PlanVersion[]): PasoItem[] {
    return versiones.map((version) => ({
      estado: PASO[version.estado],
      titulo: `Versión ${version.version} · ${SUCEDE[version.estado]}`,
      detalle: this.detalle(version),
    }));
  }

  private detalle(version: PlanVersion): string {
    const fecha = this.fechaDe(version.fecha_validacion);
    const decision =
      fecha === '' ? SUCEDE[version.estado] : `${SUCEDE[version.estado]} el ${fecha}`;
    return version.observacion === null ? decision : `${decision} · «${version.observacion}»`;
  }

  /** `2026-11-20T10:00:00Z` → `20/11/2026`; `null` → texto vacío. */
  private fechaDe(iso: string | null): string {
    return iso === null ? '' : formatoFecha(iso.slice(0, 10));
  }

  private enfocarError(): void {
    afterNextRender(() => document.getElementById('error-contenido')?.focus(), {
      injector: this.injector,
    });
  }

  private cargarPracticas(): void {
    this.practicasApi.listar().subscribe({
      next: (lista) => this.practicas.set(lista.length === 0 ? vacio<Practica[]>() : exito(lista)),
      error: (error: unknown) => this.practicas.set(estadoDeError<Practica[]>(error)),
    });
  }
}
