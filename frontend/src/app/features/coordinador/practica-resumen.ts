import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Aviso, BarraHoras, Insignia, Tarjeta } from '../../shared/ui';
import { avanceDe, TOTAL_SEMANAS } from '../../core/demo';
import type { EstadoPractica, Practica } from '../../core/demo';
import { componente, nombrePropio, paramsPractica, textoAlerta } from './coordinador.util';
import { PracticaActual } from './practica-actual';

const SOLO_LECTURA: Partial<Record<EstadoPractica, string>> = {
  suspendida: 'Práctica suspendida: solo lectura. Para seguir, reanúdela o cancélela.',
  cancelada: 'Práctica cancelada: solo lectura. No admite cambios.',
  cerrada: 'Práctica cerrada: solo lectura. Conserva el resultado de la evaluación final.',
};
const SIN_DECISIONES: Partial<Record<EstadoPractica, string>> = { asignada: 'Asignada', cancelada: 'Cancelada', cerrada: 'Cerrada' };

/** C3 · Resumen de la práctica con las acciones del coordinador según el estado. */
@Component({
  selector: 'app-practica-resumen',
  imports: [RouterLink, Aviso, BarraHoras, Insignia, Tarjeta],
  templateUrl: './practica-resumen.html',
  styleUrls: ['./pantalla.css', './practica-resumen.css'],
})
export class PracticaResumen {
  protected readonly ctx = inject(PracticaActual);
  protected readonly avance = (p: Practica) => avanceDe(p);
  protected readonly semanas = TOTAL_SEMANAS;
  protected readonly soloLectura = SOLO_LECTURA;
  protected readonly sinDecisiones = SIN_DECISIONES;
  protected readonly componente = componente;
  protected readonly nombrePropio = nombrePropio;
  protected readonly textoAlerta = textoAlerta;
  protected readonly paramsPractica = paramsPractica;

  /** `?estado=` solo viaja si el estado mostrado es el de la demostración. */
  protected params(id: number, extra: Record<string, string> = {}) {
    const demo = this.ctx.demoParam();
    return paramsPractica(id, { ...extra, ...(demo ? { estado: demo } : {}) });
  }

  protected evaluacion(p: Practica): string {
    const ev = p.evaluacion;
    return ev ? `${ev.porcentaje} % — ${ev.porcentaje >= 70 ? 'Aprobada' : 'No aprobada'}` : 'Sin evaluación final registrada';
  }
}
