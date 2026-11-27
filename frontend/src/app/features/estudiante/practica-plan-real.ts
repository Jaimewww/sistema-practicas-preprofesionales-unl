import { Component, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { catchError, distinctUntilChanged, EMPTY, map, of, switchMap } from 'rxjs';
import { formatoFecha } from '../../core/demo';
import { cargando, exito, inicial, type EstadoUi } from '../../core/estado-ui';
import { estadoDeError } from '../../core/errores';
import { Insignia, Pasos, Tarjeta, type PasoItem, type TipoInsignia } from '../../shared/ui';
import type { EstadoPlan, PlanVersion } from './plan-informe.http';
import { PlanInformeHttp } from './plan-informe.http';
import { EstadoPantalla } from './ui/estado-pantalla';

const INSIGNIA: Record<EstadoPlan, { tipo: TipoInsignia; texto: string }> = {
  en_revision: { tipo: 'warn', texto: 'En revisión' },
  aprobado: { tipo: 'ok', texto: 'Aprobado' },
  devuelto: { tipo: 'bad', texto: 'Devuelto con observación' },
};

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
 * E2 real · pestaña «Plan» (C-09): el plan vigente de solo lectura, su decisión y el
 * historial de versiones, todo desde `GET /practicas/{id}/plan/`.
 *
 * Muestra el `contenido` heredado como texto plano (sin actividades ni entregables
 * inventados) y solo ofrece corregir cuando la última versión fue devuelta, con el
 * enlace al editor real en el mismo `?p=`.
 */
@Component({
  selector: 'app-practica-plan-real',
  imports: [RouterLink, Tarjeta, Insignia, Pasos, EstadoPantalla],
  host: { class: 'span-12' },
  template: `
    @let e = estado();
    @if (e.tipo === 'exito') {
      @let ultima = ultimaVersion();
      @let id = practicaId();
      <div class="grilla">
        @if (ultima === null) {
          <app-tarjeta titulo="Plan de actividades" [span]="12">
            <div class="cuerpo">
              <p class="texto">Aún no hay plan de actividades</p>
              <p class="demo">
                El plan lo registra la estudiante y queda en revisión de su tutor académico.
              </p>
              @if (id !== null) {
                <p>
                  <a class="boton" [routerLink]="'/estudiante/plan'" [queryParams]="{ p: id }"
                    >Registrar el plan de actividades</a
                  >
                </p>
              }
            </div>
          </app-tarjeta>
        } @else {
          <app-tarjeta
            [titulo]="'Plan de actividades · versión ' + ultima.version"
            [sub]="subtitulo(ultima)"
            [span]="8"
          >
            <app-insignia
              acciones
              [tipo]="insignia(ultima).tipo"
              [texto]="insignia(ultima).texto"
            />
            <div class="cuerpo">
              <p class="plan-texto">{{ ultima.contenido }}</p>
              @if (ultima.estado === 'devuelto') {
                @if (ultima.observacion) {
                  <div class="cita">
                    <strong>Observación de su tutor académico</strong>
                    <p>{{ ultima.observacion }}</p>
                  </div>
                }
                @if (id !== null) {
                  <p>
                    <a class="boton" [routerLink]="'/estudiante/plan'" [queryParams]="{ p: id }"
                      >Corregir y reenviar el plan</a
                    >
                  </p>
                }
              } @else if (ultima.estado === 'aprobado') {
                <p class="nota">
                  Plan aprobado: la práctica pasó a «en curso» y se habilitó el reporte semanal.
                </p>
              } @else {
                <p class="nota">
                  Plan en revisión: su tutor académico lo aprobará o lo devolverá con observaciones.
                </p>
              }
            </div>
          </app-tarjeta>
          <app-tarjeta titulo="Historial de versiones" [span]="4">
            <app-pasos [pasos]="pasos(anteriores())" />
            <p class="demo">
              Las versiones anteriores se conservan; el plan aprobado es de solo lectura.
            </p>
          </app-tarjeta>
        }
      </div>
    } @else if (e.tipo === 'inicial') {
      <app-tarjeta titulo="Plan de actividades">
        <div class="cuerpo">
          <p class="texto">Elegí una práctica para ver su plan de actividades.</p>
          <a class="boton" routerLink="/estudiante/plan">Elegir la práctica</a>
        </div>
      </app-tarjeta>
    } @else {
      <app-estado-pantalla [estado]="e" />
    }
  `,
  styleUrl: './pantalla.css',
  styles: `
    .plan-texto {
      margin: 0;
      white-space: pre-line;
    }
  `,
})
export class PracticaPlanReal {
  private readonly api = inject(PlanInformeHttp);
  private readonly ruta = inject(ActivatedRoute);

  protected readonly estado = signal<EstadoUi<PlanVersion[]>>(inicial());
  /** Práctica elegida por `?p=`; `null` mientras no haya una. */
  protected readonly practicaId = signal<number | null>(
    idDeParam(this.ruta.snapshot.queryParamMap.get('p')),
  );

  protected readonly versiones = computed(() => {
    const e = this.estado();
    return e.tipo === 'exito' ? e.datos : [];
  });
  protected readonly ultimaVersion = computed(() => this.versiones()[0] ?? null);
  protected readonly anteriores = computed(() => this.versiones().slice(1));

  protected readonly insignia = (version: PlanVersion) => INSIGNIA[version.estado];

  constructor() {
    this.ruta.queryParamMap
      .pipe(
        map((q) => idDeParam(q.get('p'))),
        distinctUntilChanged(),
        switchMap((id) => {
          this.practicaId.set(id);
          if (id === null) {
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
      .subscribe((estado) => this.estado.set(estado));
  }

  protected subtitulo(version: PlanVersion): string {
    const fecha = this.fechaDe(version.fecha_validacion);
    const sufijo = fecha === '' ? '' : ` el ${fecha}`;
    if (version.estado === 'aprobado') return `Aprobado${sufijo}.`;
    if (version.estado === 'devuelto') return `Devuelto${sufijo}.`;
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
}
