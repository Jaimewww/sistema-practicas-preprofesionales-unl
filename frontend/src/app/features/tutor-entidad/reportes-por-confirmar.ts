import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { formatoFecha } from '../../core/demo';
import { cargando } from '../../core/estado-ui';
import { Insignia, Tarjeta, Vacio } from '../../shared/ui';
import { TutorEntidadApi } from './tutor-entidad.api';
import type { ReporteConfirmable } from './tutor-entidad.model';
import { aEstado, nombreCorto, rango, textoRevision, tipoRevision } from './tutor-entidad.util';
import { EstadoPantalla } from './ui/estado-pantalla';

/** R2 · Reportes por confirmar: los reportes de sus practicantes que la entidad aún no confirma, con filtros. */
@Component({
  selector: 'app-reportes-por-confirmar',
  imports: [RouterLink, Tarjeta, Insignia, Vacio, EstadoPantalla],
  templateUrl: './reportes-por-confirmar.html',
  styleUrls: ['./pantalla.css'],
})
export class ReportesPorConfirmar {
  private readonly api = inject(TutorEntidadApi);
  protected readonly estado = toSignal(aEstado(this.api.reportesPorConfirmar()), { initialValue: cargando<ReporteConfirmable[]>() });

  /** Id del practicante elegido (`''` = todos) y revisión académica elegida (`''` = todas). */
  protected readonly practicante = signal('');
  protected readonly revision = signal('');
  /** Variante «sin reportes por confirmar» (`?vacio=1` o el botón de demostración). */
  protected readonly sinReportes = signal(inject(ActivatedRoute).snapshot.queryParamMap.get('vacio') === '1');

  /** Por semana y, dentro de cada semana, por practicante. */
  protected readonly reportes = computed(() => {
    const e = this.estado();
    const lista = e.tipo === 'exito' ? e.datos : [];
    return [...lista].sort((a, b) => a.reporte.semana - b.reporte.semana || a.practica.id - b.practica.id);
  });
  protected readonly practicantes = computed(() => {
    const vistos = new Map<number, string>();
    for (const r of this.reportes()) vistos.set(r.practica.id, r.practica.estudiante);
    return [...vistos].map(([id, nombre]) => ({ id: String(id), nombre: nombreCorto(nombre) }));
  });
  protected readonly visibles = computed(() =>
    this.reportes().filter((r) => (!this.practicante() || String(r.practica.id) === this.practicante()) && (!this.revision() || r.reporte.estado === this.revision())),
  );

  protected readonly formatoFecha = formatoFecha;
  protected readonly rango = rango;
  protected readonly textoRevision = textoRevision;
  protected readonly tipoRevision = tipoRevision;
}
