import { computed, inject, Injectable, signal } from '@angular/core';
import { takeUntilDestroyed, toObservable, toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router } from '@angular/router';
import { combineLatest, distinctUntilChanged, map, switchMap } from 'rxjs';
import { cargando } from '../../core/estado-ui';
import { estadoDeError } from '../../core/errores';
import type { EstadoPractica } from '../../core/demo';
import { CoordinadorApi } from './coordinador.api';
import type { DetallePractica } from './coordinador.model';
import { aEstado, esEstado, estadoDemo, idPractica } from './coordinador.util';

/**
 * La práctica que muestran el marco, el resumen y el historial (C3). Se provee en el marco, así
 * las pestañas comparten una sola carga y una decisión (reanudar) refresca todo.
 */
@Injectable()
export class PracticaActual {
  private readonly api = inject(CoordinadorApi);
  private readonly ruta = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly recarga = signal(0);

  readonly id = toSignal(this.ruta.queryParamMap.pipe(map((q) => idPractica(q.get('p')))), { initialValue: idPractica(this.ruta.snapshot.queryParamMap.get('p')) });
  private readonly demo = toSignal(this.ruta.queryParamMap.pipe(map((q) => q.get('estado'))), { initialValue: this.ruta.snapshot.queryParamMap.get('estado') });
  readonly estado = toSignal(
    combineLatest([this.ruta.queryParamMap.pipe(map((q) => idPractica(q.get('p'))), distinctUntilChanged()), toObservable(this.recarga)]).pipe(switchMap(([id]) => aEstado(this.api.practica(id)))),
    { initialValue: cargando<DetallePractica>() },
  );
  /** `?estado=` de la URL cuando es un estado válido; los enlaces lo conservan. */
  readonly demoParam = computed(() => (esEstado(this.demo()) ? this.demo() : null));
  /** Aviso que deja una decisión tomada desde el resumen. */
  readonly aviso = signal('');
  readonly error = signal('');

  /** Estado que se muestra: el de la demostración (`?estado=`) o el real. */
  readonly estadoMostrado = computed<EstadoPractica | null>(() => {
    const e = this.estado();
    return e.tipo === 'exito' ? estadoDemo(this.demo(), e.datos.practica.estado) : null;
  });

  /** Cambia el estado de la demostración sin tocar los datos. */
  cambiarDemo(valor: string): void {
    this.aviso.set('');
    void this.router.navigate([], { relativeTo: this.ruta, queryParams: { estado: valor }, queryParamsHandling: 'merge', replaceUrl: true });
  }

  reanudar(): void {
    this.error.set('');
    this.api.reanudar(this.id()).pipe(takeUntilDestroyed()).subscribe({
      next: () => {
        this.aviso.set('reanudada');
        this.recarga.update((n) => n + 1);
        void this.router.navigate([], { relativeTo: this.ruta, queryParams: { estado: null }, queryParamsHandling: 'merge', replaceUrl: true });
      },
      error: (e: unknown) => {
        const r = estadoDeError<void>(e);
        this.error.set(r.tipo === 'error' ? r.mensaje : 'No se pudo reanudar la práctica.');
      },
    });
  }
}
