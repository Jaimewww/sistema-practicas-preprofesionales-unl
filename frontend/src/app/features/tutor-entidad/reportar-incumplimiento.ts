import { Component, computed, inject, linkedSignal, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { map } from 'rxjs';
import { formatoFecha } from '../../core/demo';
import type { Incumplimiento, Practica } from '../../core/demo';
import { estadoDeError } from '../../core/errores';
import { cargando } from '../../core/estado-ui';
import { Aviso, Tarjeta } from '../../shared/ui';
import { TutorEntidadApi } from './tutor-entidad.api';
import type { RegistroIncumplimiento } from './tutor-entidad.model';
import { aEstado, idDeParametro, nombreCorto, subtipoTexto } from './tutor-entidad.util';
import { EstadoPantalla } from './ui/estado-pantalla';

const FALTA_DESCRIPCION = 'Describa el incumplimiento.';

/** R5 · Reportar incumplimiento: descripción obligatoria; avisa al tutor académico y lista lo ya reportado. */
@Component({
  selector: 'app-reportar-incumplimiento',
  imports: [FormsModule, RouterLink, Tarjeta, Aviso, EstadoPantalla],
  templateUrl: './reportar-incumplimiento.html',
  styleUrls: ['./pantalla.css'],
})
export class ReportarIncumplimiento {
  private readonly api = inject(TutorEntidadApi);
  protected readonly estado = toSignal(aEstado(this.api.practicantes(), (l) => l.length === 0), { initialValue: cargando<Practica[]>() });
  private readonly pedido = toSignal(inject(ActivatedRoute).queryParamMap.pipe(map((q) => idDeParametro(q.get('p')))), { initialValue: null });
  private readonly lista = computed(() => {
    const e = this.estado();
    return e.tipo === 'exito' ? e.datos : [];
  });

  /** Practicante elegido: el de `?p=` si existe en la lista; si no, el primero. */
  protected readonly seleccionado = linkedSignal<Practica[], number | null>({
    source: this.lista,
    computation: (lista) => lista.find((x) => x.id === this.pedido())?.id ?? lista[0]?.id ?? null,
  });
  protected readonly practica = computed(() => this.lista().find((p) => p.id === this.seleccionado()) ?? null);
  /** Incumplimientos reportados en esta pantalla, por practicante (se suman a los que ya trae la práctica). */
  private readonly nuevos = signal<Record<number, Incumplimiento[]>>({});
  protected readonly reportados = computed(() => {
    const p = this.practica();
    return p ? [...p.incumplimientos, ...(this.nuevos()[p.id] ?? [])] : [];
  });

  protected descripcion = '';
  protected readonly error = signal(false);
  protected readonly errorServidor = signal('');
  protected readonly enviando = signal(false);
  protected readonly registro = signal<RegistroIncumplimiento | null>(null);
  protected readonly faltaDescripcion = FALTA_DESCRIPCION;
  protected readonly formatoFecha = formatoFecha;
  protected readonly nombreCorto = nombreCorto;
  protected readonly subtipoTexto = subtipoTexto;

  protected alEscribir(): void {
    if (this.descripcion.trim()) this.error.set(false);
  }

  protected enviar(): void {
    const practica = this.practica();
    if (!practica) return;
    if (!this.descripcion.trim()) {
      this.error.set(true);
      document.getElementById('descripcion')?.focus();
      return;
    }
    this.error.set(false);
    this.errorServidor.set('');
    this.enviando.set(true);
    this.api.reportarIncumplimiento(practica.id, this.descripcion).subscribe({
      next: (r) => {
        this.enviando.set(false);
        this.registro.set(r);
        const nuevo: Incumplimiento = { descripcion: this.descripcion.trim(), reportadoPor: r.reportadoPor, reportadoEl: r.reportadoEl };
        this.nuevos.update((n) => ({ ...n, [practica.id]: [...(n[practica.id] ?? []), nuevo] }));
      },
      error: (err: unknown) => {
        this.enviando.set(false);
        const r = estadoDeError<void>(err);
        this.errorServidor.set(r.tipo === 'error' ? r.mensaje : 'No se pudo enviar el reporte.');
      },
    });
  }
}
