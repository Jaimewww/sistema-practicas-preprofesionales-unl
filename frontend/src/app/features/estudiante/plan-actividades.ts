import { afterNextRender, Component, effect, inject, Injector, signal, untracked } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { estadoDeError } from '../../core/errores';
import { formatoFecha } from '../../core/demo';
import { Aviso, Pasos, Tarjeta, type PasoItem } from '../../shared/ui';
import { EstudianteApi } from './estudiante.api';
import type { ActividadPlan, PlanEditable } from './estudiante.model';
import { estadoPorPractica, nombrePropio, paramPractica, practicaActual } from './estudiante.util';
import { EstadoPantalla } from './ui/estado-pantalla';

type GrupoActividad = FormGroup<{ descripcion: FormControl<string>; herramientas: FormControl<string>; entregable: FormControl<string> }>;

interface Fila {
  /** Identificador estable para `id`/`for`: no cambia al quitar otras filas. */
  uid: number;
  grupo: GrupoActividad;
}

let siguienteUid = 0;

const nuevaFila = (a?: ActividadPlan): Fila => ({
  uid: ++siguienteUid,
  grupo: new FormGroup({
    descripcion: new FormControl(a?.descripcion ?? '', { nonNullable: true }),
    herramientas: new FormControl(a?.herramientas ?? '', { nonNullable: true }),
    entregable: new FormControl(a?.entregable ?? '', { nonNullable: true }),
  }),
});

/** E3 · Plan de actividades: agregar y quitar actividades, mínimo una, y enviar a revisión. */
@Component({
  selector: 'app-plan-actividades',
  imports: [ReactiveFormsModule, RouterLink, Tarjeta, Pasos, Aviso, EstadoPantalla],
  templateUrl: './plan-actividades.html',
  styleUrls: ['./pantalla.css', './plan-actividades.css'],
})
export class PlanActividades {
  private readonly api = inject(EstudianteApi);
  private readonly router = inject(Router);
  private readonly injector = inject(Injector);
  protected readonly id = practicaActual();
  protected readonly estado = estadoPorPractica((id) => this.api.planEditable(id));

  protected readonly filas = signal<Fila[]>([]);
  /** «Registre al menos una actividad»: se muestra tras intentar enviar sin ninguna. */
  protected readonly sinActividades = signal(false);
  protected readonly enviando = signal(false);
  protected readonly errorEnvio = signal('');
  protected readonly paramPractica = paramPractica;
  protected readonly nombrePropio = nombrePropio;
  protected readonly formatoFecha = formatoFecha;

  constructor() {
    // Cuando llega el plan, las filas arrancan con sus actividades (o con una fila vacía).
    effect(() => {
      const e = this.estado();
      if (e.tipo === 'exito') {
        untracked(() => this.filas.set(e.datos.actividades.length ? e.datos.actividades.map(nuevaFila) : [nuevaFila()]));
      }
    });
  }

  protected agregar(): void {
    const fila = nuevaFila();
    this.filas.update((lista) => [...lista, fila]);
    afterNextRender(() => document.getElementById(`actividad-${fila.uid}`)?.focus(), { injector: this.injector });
  }

  protected enfocarPrimera(): void {
    document.getElementById(`actividad-${this.filas()[0]?.uid}`)?.focus();
  }

  protected quitar(uid: number): void {
    if (this.filas().length > 1) this.filas.update((lista) => lista.filter((f) => f.uid !== uid));
  }

  protected enviar(): void {
    const actividades = this.filas()
      .map((f) => f.grupo.getRawValue())
      .map((a) => ({ descripcion: a.descripcion.trim(), herramientas: a.herramientas.trim(), entregable: a.entregable.trim() }))
      .filter((a) => a.descripcion);
    if (!actividades.length) {
      this.sinActividades.set(true);
      afterNextRender(() => document.getElementById('error-plan')?.focus(), { injector: this.injector });
      return;
    }
    this.sinActividades.set(false);
    this.errorEnvio.set('');
    this.enviando.set(true);
    this.api.enviarPlan(this.id(), actividades).subscribe({
      next: () => {
        this.enviando.set(false);
        void this.router.navigate(['/estudiante/practica/plan'], { queryParams: paramPractica(this.id()), state: { planEnviado: true } });
      },
      error: (e: unknown) => {
        this.enviando.set(false);
        const resultado = estadoDeError<void>(e);
        this.errorEnvio.set(resultado.tipo === 'error' ? resultado.mensaje : 'No se pudo enviar el plan.');
      },
    });
  }

  /** Recorrido del plan: lo ya enviado, dónde está la estudiante y lo que sigue. */
  protected recorrido(plan: PlanEditable): PasoItem[] {
    const pasos: PasoItem[] = [];
    for (const v of plan.versiones) {
      pasos.push({ estado: 'done', titulo: `Versión ${v.numero} enviada`, detalle: formatoFecha(v.enviadaEl) });
      if (v.estado === 'devuelta') {
        pasos.push({ estado: 'bad', titulo: 'Devuelta con observación', detalle: `${formatoFecha(v.decididaEl ?? v.enviadaEl)} · requiere corrección` });
      }
    }
    pasos.push({
      estado: 'now',
      titulo: plan.versiones.length ? `Versión ${plan.version}: usted corrige` : `Versión ${plan.version}: usted lo registra`,
      detalle: 'Está aquí',
    });
    pasos.push({ estado: 'pendiente', titulo: 'Revisión del tutor académico', detalle: 'Aprueba o devuelve' });
    pasos.push({ estado: 'pendiente', titulo: 'Práctica en curso', detalle: 'Se habilitan los reportes' });
    return pasos;
  }
}
