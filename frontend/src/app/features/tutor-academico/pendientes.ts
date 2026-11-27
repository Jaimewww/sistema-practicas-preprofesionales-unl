import { Component, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { formatoFecha, PLAZO_REVISION_DIAS, TIPO_REVISION } from '../../core/demo';
import type { TipoRevision } from '../../core/demo';
import { cargando } from '../../core/estado-ui';
import { Aviso, Insignia, Tarjeta, Vacio } from '../../shared/ui';
import { TutorAcademicoApi } from './tutor-academico.api';
import type { Pendiente } from './tutor-academico.model';
import { aEstado, nombreCorto, practicaEnEntidad, rutaRevision } from './tutor-academico.util';
import { EstadoPantalla } from './ui/estado-pantalla';

/** T1 · Pendientes de revisión: la bandeja de planes, reportes e informes, del más antiguo al más nuevo. */
@Component({
  selector: 'app-pendientes',
  imports: [RouterLink, Tarjeta, Insignia, Aviso, Vacio, EstadoPantalla],
  templateUrl: './pendientes.html',
  styleUrl: './pantalla.css',
})
export class Pendientes {
  private readonly api = inject(TutorAcademicoApi);
  protected readonly estado = toSignal(aEstado(this.api.pendientes(), (l) => l.length === 0), { initialValue: cargando<Pendiente[]>() });

  protected readonly plazo = PLAZO_REVISION_DIAS;
  protected readonly tipoTexto = TIPO_REVISION;
  protected readonly nombreCorto = nombreCorto;
  protected readonly practicaEnEntidad = practicaEnEntidad;
  protected readonly rutaRevision = rutaRevision;
  protected readonly formatoFecha = formatoFecha;

  protected readonly tipo = signal('');
  protected readonly plazoFiltro = signal('');
  protected readonly estudiante = signal('');
  /** Variante «sin pendientes» del prototipo (`?vacio=1` o el botón). */
  protected readonly sinPendientes = signal(inject(ActivatedRoute).snapshot.queryParamMap.get('vacio') === '1');

  protected filtrar(lista: Pendiente[]): Pendiente[] {
    const tipo = this.tipo();
    const plazo = this.plazoFiltro();
    const est = this.estudiante();
    return lista.filter((p) => (!tipo || p.tipo === tipo) && (!plazo || (plazo === 'fuera') === p.fueraDePlazo) && (!est || String(p.practica.id) === est));
  }

  protected estudiantes(lista: Pendiente[]): Array<{ id: number; nombre: string }> {
    const vistos = new Map<number, string>();
    for (const p of lista) vistos.set(p.practica.id, nombreCorto(p.practica.estudiante));
    return [...vistos].map(([id, nombre]) => ({ id, nombre })).sort((a, b) => a.id - b.id);
  }

  /** «1 pendiente fuera de plazo: el reporte de la semana 7 de Diego Jiménez lleva 9 días hábiles esperando (plazo: 5).» */
  protected avisoFuera(lista: Pendiente[]): { titulo: string; texto: string } | null {
    const fuera = lista.filter((p) => p.fueraDePlazo);
    if (!fuera.length) return null;
    const p = fuera[0];
    const de = nombreCorto(p.practica.estudiante);
    const cosa: Record<TipoRevision, string> = {
      reporte: `el reporte de la semana ${p.semana} de ${de}`,
      plan: `el plan de actividades de ${de}`,
      informe: `el informe final de ${de}`,
    };
    const titulo = fuera.length === 1 ? '1 pendiente fuera de plazo:' : `${fuera.length} pendientes fuera de plazo:`;
    const quien = fuera.length === 1 ? cosa[p.tipo] : `el más antiguo es ${cosa[p.tipo]}`;
    return { titulo, texto: `${quien} lleva ${p.dias} días hábiles esperando (plazo: ${this.plazo}).` };
  }

  protected valor(evento: Event): string {
    return (evento.target as HTMLSelectElement).value;
  }
}
