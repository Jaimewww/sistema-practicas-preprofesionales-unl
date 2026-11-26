import { Component, inject } from '@angular/core';
import { RouterLink, Router } from '@angular/router';
import { formatoFecha } from '../../core/demo';
import { Aviso, Insignia, Pasos, Tarjeta, type PasoItem, type TipoInsignia } from '../../shared/ui';
import { EstudianteApi } from './estudiante.api';
import type { PlanDetalle, VersionPlan } from './estudiante.model';
import { estadoPorPractica, nombrePropio, paramPractica } from './estudiante.util';
import { EstadoPantalla } from './ui/estado-pantalla';

const INSIGNIA: Record<PlanDetalle['estado'], { tipo: TipoInsignia; texto: string }> = {
  validado: { tipo: 'ok', texto: 'Aprobado' },
  en_revision: { tipo: 'warn', texto: 'En revisión' },
  devuelto: { tipo: 'bad', texto: 'Devuelto con observación' },
};

/** E2 · pestaña «Plan»: el plan vigente (solo lectura) y el historial de sus versiones. */
@Component({
  selector: 'app-practica-plan',
  imports: [RouterLink, Tarjeta, Insignia, Pasos, Aviso, EstadoPantalla],
  host: { class: 'span-12' },
  template: `
    @let e = estado();
    @if (e.tipo === 'exito') {
      @let plan = e.datos;
      <div class="grilla">
        @if (planEnviado) {
          <app-aviso class="span-12" tipo="ok"><strong>Plan enviado a revisión.</strong> Su tutor académico lo aprobará o lo devolverá con observaciones.</app-aviso>
        }
        <app-tarjeta
          [titulo]="'Plan de actividades · versión ' + plan.version"
          [sub]="subtitulo(plan)"
          [span]="8"
        >
          <app-insignia acciones [tipo]="insignia(plan).tipo" [texto]="insignia(plan).texto" />
          <div class="cuerpo">
            <ol class="actividades">
              @for (a of plan.actividades; track $index) {
                <li>
                  <span class="numero" aria-hidden="true">{{ $index + 1 }}</span>
                  <div>
                    <strong>{{ a.descripcion }}</strong>
                    @if (a.herramientas) {
                      <p><small>Herramientas</small><br />{{ a.herramientas }}</p>
                    }
                    @if (a.entregable) {
                      <p><small>Entregable</small><br />{{ a.entregable }}</p>
                    }
                  </div>
                </li>
              }
            </ol>
            @if (plan.estado === 'validado') {
              <p class="nota">Con la aprobación del plan, la práctica pasó de «asignada» a «en curso» y se habilitó el reporte semanal.</p>
            }
            @if (plan.estado === 'devuelto') {
              <a class="boton" routerLink="/estudiante/plan" [queryParams]="paramPractica(plan.practica.id)">Corregir y reenviar el plan</a>
            }
          </div>
        </app-tarjeta>
        <app-tarjeta titulo="Historial de versiones" [span]="4">
          <app-pasos [pasos]="pasos(plan.versiones)" />
          <p class="demo">El plan aprobado es de solo lectura. Si el tutor lo devuelve, aparece la versión siguiente para corregir.</p>
        </app-tarjeta>
      </div>
    } @else {
      <app-estado-pantalla [estado]="e" />
    }
  `,
  styleUrl: './pantalla.css',
})
export class PracticaPlan {
  private readonly api = inject(EstudianteApi);
  protected readonly estado = estadoPorPractica((id) => this.api.plan(id));
  /** Viene de «Enviar a revisión» en E3: el aviso solo se ve en esa navegación. */
  protected readonly planEnviado = this.vieneDeEnviar(inject(Router));

  protected readonly paramPractica = paramPractica;
  protected readonly insignia = (plan: PlanDetalle) => INSIGNIA[plan.estado];

  /** La pestaña se crea al terminar la navegación (dentro del marco), así que se mira la última exitosa. */
  private vieneDeEnviar(router: Router): boolean {
    const navegacion = router.currentNavigation() ?? router.lastSuccessfulNavigation();
    return navegacion?.extras.state?.['planEnviado'] === true;
  }

  protected subtitulo(plan: PlanDetalle): string {
    if (plan.estado === 'validado' && plan.decididoEl) return `Aprobado por ${nombrePropio(plan.decididoPor)} el ${formatoFecha(plan.decididoEl)}`;
    if (plan.estado === 'en_revision') return 'Esperando la revisión de su tutor académico.';
    return `Devuelto por ${nombrePropio(plan.decididoPor)}.`;
  }

  protected pasos(versiones: VersionPlan[]): PasoItem[] {
    return versiones.map((v) => {
      const enviada = `Enviada el ${formatoFecha(v.enviadaEl)}`;
      switch (v.estado) {
        case 'devuelta':
          return { estado: 'bad', titulo: `Versión ${v.numero} · devuelta`, detalle: `${enviada} · devuelta el ${formatoFecha(v.decididaEl ?? v.enviadaEl)}. «${v.observacion}»` };
        case 'aprobada':
          return { estado: 'done', titulo: `Versión ${v.numero} · aprobada`, detalle: `${enviada} · aprobada el ${formatoFecha(v.decididaEl ?? v.enviadaEl)}` };
        default:
          return { estado: 'now', titulo: `Versión ${v.numero} · en revisión`, detalle: enviada };
      }
    });
  }
}
