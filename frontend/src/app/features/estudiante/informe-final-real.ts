import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { catchError, distinctUntilChanged, map, of, startWith, switchMap } from 'rxjs';
import type { Observable } from 'rxjs';
import { aApiError } from '../../core/api/api-error.interceptor';
import { formatoFecha } from '../../core/demo';
import { estadoDeError, mensajeDeError } from '../../core/errores';
import { Aviso, Insignia, Pasos, Tarjeta, type PasoItem, type TipoInsignia } from '../../shared/ui';
import type {
  EstadoInformeEstudiante,
  InformeFinalEstudiante,
  InformeFinalEstudianteDetalle,
} from './plan-informe.http';
import { PlanInformeHttp } from './plan-informe.http';

/** Límite del contrato y del backend (ADR 0005): PDF de hasta 5 MB. */
const TAMANO_MAXIMO = 5 * 1024 * 1024;

const INSIGNIA: Record<EstadoInformeEstudiante, { tipo: TipoInsignia; texto: string }> = {
  en_revision: { tipo: 'warn', texto: 'En revisión' },
  validado: { tipo: 'ok', texto: 'Validado' },
  devuelto: { tipo: 'bad', texto: 'Devuelto con observación' },
};

/**
 * Estado de la lectura del informe. `ausente` (404) no es un error: significa que la
 * práctica todavía no tiene informe, y se distingue de `error` (permisos, red, 5xx).
 */
type EstadoInformeReal =
  | { tipo: 'cargando' }
  | { tipo: 'sin_practica' }
  | { tipo: 'ausente' }
  | { tipo: 'exito'; detalle: InformeFinalEstudianteDetalle }
  | { tipo: 'error'; mensaje: string };

/** `?p=` como id positivo; `null` cuando falta: en modo real no se inventa la práctica 1 del demo. */
function idDeParam(valor: string | null): number | null {
  const id = Number(valor);
  return valor !== null && valor.trim() !== '' && Number.isInteger(id) && id > 0 ? id : null;
}

/**
 * E6 real · informe final del estudiante (C-10) sobre `PlanInformeHttp`.
 *
 * La lectura es la última versión con su devolución; un 404 se pinta como «todavía no
 * hay informe» y cualquier otro error conserva su mensaje. El envío es multipart con
 * un único `archivo` PDF de hasta 5 MB, sin resumen ni campos que el contrato no
 * acepte, y una devolución habilita el reenvío del PDF corregido.
 */
@Component({
  selector: 'app-informe-final-real',
  imports: [RouterLink, Tarjeta, Insignia, Pasos, Aviso],
  template: `
    @let e = estado();
    @if (e.tipo === 'error') {
      <div class="grilla">
        <div class="span-12">
          <app-aviso tipo="bad">{{ e.mensaje }}</app-aviso>
        </div>
      </div>
    } @else if (e.tipo === 'sin_practica') {
      <app-tarjeta titulo="Informe final de actividades">
        <div class="cuerpo">
          <p class="texto">Elegí una práctica para consultar o presentar su informe final.</p>
          <a class="boton" routerLink="/estudiante/plan">Elegir la práctica</a>
        </div>
      </app-tarjeta>
    } @else if (e.tipo === 'cargando') {
      <p class="cargando" role="status">Cargando…</p>
    } @else {
      @let d = detalle();
      <div class="grilla">
        <app-tarjeta
          titulo="Informe final de actividades"
          sub="Presente su informe en PDF; su tutor académico lo revisa antes del cierre."
          [span]="8"
        >
          <div class="cuerpo">
            @if (d === null) {
              <app-aviso tipo="info">
                <strong>Aún no presentó su informe final.</strong> Adjunte el PDF de su informe para
                enviarlo a revisión.
              </app-aviso>
            } @else {
              <app-aviso
                [tipo]="d.estado === 'devuelto' ? 'bad' : d.estado === 'validado' ? 'ok' : 'info'"
              >
                <p class="titulo-aviso">
                  <app-insignia
                    [tipo]="insignia(d.estado).tipo"
                    [texto]="insignia(d.estado).texto"
                  />
                </p>
                <p class="titulo-aviso">Presentado el {{ fecha(d.fecha) }}</p>
                @if (d.devolucion) {
                  <p class="titulo-aviso">
                    <strong>Observación:</strong> {{ d.devolucion.observacion }}
                  </p>
                  <p class="demo">Devuelto el {{ fecha(d.devolucion.fecha) }}</p>
                }
              </app-aviso>
            }
            @if (enviado(); as informe) {
              <app-aviso tipo="ok">
                <p class="titulo-aviso">
                  <strong>Informe presentado.</strong> Quedó «en revisión» de su tutor académico.
                </p>
                <p class="titulo-aviso">
                  Versión {{ informe.version }} · presentado el {{ fecha(informe.fecha) }} ·
                  <app-insignia
                    [tipo]="insignia(informe.estado).tipo"
                    [texto]="insignia(informe.estado).texto"
                  />
                </p>
              </app-aviso>
            }
            @if (errorEnvio()) {
              <app-aviso tipo="bad">{{ errorEnvio() }}</app-aviso>
            }
            @if (errores().length > 0) {
              <div class="resumen-error" role="alert">
                <p>Revise el formulario</p>
                <ul>
                  @for (mensaje of errores(); track mensaje) {
                    <li>{{ mensaje }}</li>
                  }
                </ul>
              </div>
            }
            @if (puedePresentar()) {
              <form (submit)="$event.preventDefault(); presentar()" novalidate>
                <div class="campo">
                  <span class="etiqueta" id="et-informe"
                    >Informe final en PDF <span class="req" aria-hidden="true">*</span></span
                  >
                  <label
                    class="zona"
                    for="archivo"
                    (dragover)="$event.preventDefault()"
                    (drop)="soltar($event)"
                  >
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      aria-hidden="true"
                    >
                      <path d="M12 16V4M7 9l5-5 5 5" />
                      <path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" />
                    </svg>
                    <strong>{{ archivo()?.name ?? 'Arrastre su informe en PDF' }}</strong>
                    <span class="ayuda">Solo PDF, hasta 5 MB.</span>
                  </label>
                  <input
                    id="archivo"
                    class="sr-only"
                    type="file"
                    accept="application/pdf,.pdf"
                    aria-labelledby="et-informe"
                    (change)="elegir($any($event.target).files)"
                  />
                </div>
                <div class="acciones-fila">
                  <button class="boton" type="submit" [disabled]="enviando()">
                    {{ enviando() ? 'Enviando…' : 'Presentar a revisión' }}
                  </button>
                </div>
              </form>
            }
          </div>
        </app-tarjeta>
        <app-tarjeta titulo="Camino al cierre" [span]="4">
          <app-pasos [pasos]="camino()" />
          <p class="nota">
            Si el tutor lo devuelve, verá sus observaciones aquí y podrá corregirlo con un PDF
            nuevo.
          </p>
        </app-tarjeta>
      </div>
    }
  `,
  styleUrls: ['./pantalla.css', './informe-final.css'],
})
export class InformeFinalReal {
  private readonly api = inject(PlanInformeHttp);
  private readonly ruta = inject(ActivatedRoute);

  protected readonly estado = toSignal(
    this.ruta.queryParamMap.pipe(
      map((q) => idDeParam(q.get('p'))),
      distinctUntilChanged(),
      switchMap((id): Observable<EstadoInformeReal> => {
        if (id === null) return of<EstadoInformeReal>({ tipo: 'sin_practica' });
        return this.api.informeFinal(id).pipe(
          map((detalle): EstadoInformeReal => ({ tipo: 'exito', detalle })),
          catchError((error: unknown) => {
            const apiError = aApiError(error);
            return of<EstadoInformeReal>(
              apiError.status === 404
                ? { tipo: 'ausente' }
                : { tipo: 'error', mensaje: mensajeDeError(apiError) },
            );
          }),
          startWith<EstadoInformeReal>({ tipo: 'cargando' }),
        );
      }),
    ),
    { initialValue: { tipo: 'cargando' } as EstadoInformeReal },
  );

  protected readonly detalle = computed(() => {
    const e = this.estado();
    return e.tipo === 'exito' ? e.detalle : null;
  });
  protected readonly archivo = signal<File | null>(null);
  protected readonly errores = signal<string[]>([]);
  protected readonly enviando = signal(false);
  /** Versión creada por el último POST: la pantalla no vuelve a pedir el informe. */
  protected readonly enviado = signal<InformeFinalEstudiante | null>(null);
  protected readonly errorEnvio = signal('');

  /** Solo se puede presentar si no hay informe o si el tutor devolvió el último. */
  protected readonly puedePresentar = computed(() => {
    if (this.enviado() !== null) return false;
    const estado = this.estado();
    if (estado.tipo === 'ausente') return true;
    return estado.tipo === 'exito' && estado.detalle.estado === 'devuelto';
  });

  protected readonly camino = computed<PasoItem[]>(() => {
    const estado = this.enviado()?.estado ?? this.detalle()?.estado ?? null;
    const devuelto = estado === 'devuelto';
    const presentado = estado !== null && !devuelto;
    const validado = estado === 'validado';
    return [
      {
        estado: devuelto ? 'now' : presentado ? 'done' : 'now',
        titulo: devuelto ? 'Presentar el PDF corregido' : 'Presentar el informe',
        detalle: 'Un PDF de hasta 5 MB',
      },
      {
        estado: validado ? 'done' : devuelto ? 'bad' : presentado ? 'now' : 'pendiente',
        titulo: 'Revisión del tutor académico',
        detalle: 'Aprueba o devuelve con observaciones',
      },
      {
        estado: validado ? 'now' : 'pendiente',
        titulo: 'Evaluación y cierre de la práctica',
        detalle: 'Lo registra la coordinación',
      },
    ];
  });

  protected readonly insignia = (estado: EstadoInformeEstudiante) => INSIGNIA[estado];

  protected elegir(archivos: FileList | null): void {
    this.archivo.set(archivos?.item(0) ?? null);
  }

  protected soltar(evento: DragEvent): void {
    evento.preventDefault();
    this.archivo.set(evento.dataTransfer?.files.item(0) ?? null);
  }

  protected presentar(): void {
    const id = idDeParam(this.ruta.snapshot.queryParamMap.get('p'));
    const archivo = this.archivo();
    const errores: string[] = [];
    if (id === null) errores.push('Elegí una práctica antes de presentar el informe.');
    if (archivo === null) errores.push('Adjunte su informe final en PDF.');
    else if (archivo.type !== 'application/pdf' && !archivo.name.toLowerCase().endsWith('.pdf')) {
      errores.push('El informe debe estar en PDF.');
    } else if (archivo.size > TAMANO_MAXIMO) errores.push('El informe no puede pesar más de 5 MB.');
    this.errores.set(errores);
    if (errores.length > 0 || archivo === null || id === null) return;
    this.errorEnvio.set('');
    this.enviando.set(true);
    this.api.presentarInformeFinal(id, archivo).subscribe({
      next: (informe) => {
        this.enviando.set(false);
        this.archivo.set(null);
        this.enviado.set(informe);
      },
      error: (error: unknown) => {
        this.enviando.set(false);
        const resultado = estadoDeError<InformeFinalEstudiante>(error);
        this.errorEnvio.set(
          resultado.tipo === 'error' ? resultado.mensaje : 'No se pudo presentar el informe.',
        );
      },
    });
  }

  /** `2026-11-22T10:00:00Z` → `22/11/2026`. */
  protected fecha(iso: string): string {
    return formatoFecha(iso.slice(0, 10));
  }
}
