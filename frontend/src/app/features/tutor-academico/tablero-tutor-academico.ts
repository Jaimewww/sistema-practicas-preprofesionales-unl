import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { avanceDe, formatoFecha, PERIODO, PLAZO_REVISION_DIAS, TIPO_REVISION } from '../../core/demo';
import type { Practica } from '../../core/demo';
import { cargando } from '../../core/estado-ui';
import { Insignia, Kpi, KpiGrid, Tarjeta, Vacio } from '../../shared/ui';
import { TutorAcademicoApi } from './tutor-academico.api';
import type { Pendiente } from './tutor-academico.model';
import { aEstado, listoParaEvaluar, nombreCorto, primerNombre, rezagada, rutaRevision } from './tutor-academico.util';
import { EstadoPantalla } from './ui/estado-pantalla';

interface Datos {
  pendientes: Pendiente[];
  tutorados: Practica[];
}

/** Cuántos pendientes se destacan en «Para revisar primero». */
const DESTACADOS = 4;

/** TA0 · Tablero del tutor académico: pendientes por revisar, tutorados que necesitan atención y accesos rápidos. */
@Component({
  selector: 'app-tablero-tutor-academico',
  imports: [RouterLink, Tarjeta, Kpi, KpiGrid, Insignia, Vacio, EstadoPantalla],
  templateUrl: './tablero-tutor-academico.html',
  styleUrl: './pantalla.css',
})
export class TableroTutorAcademico {
  private readonly api = inject(TutorAcademicoApi);
  protected readonly estado = toSignal(
    aEstado<Datos>(forkJoin({ pendientes: this.api.pendientes(), tutorados: this.api.tutorados() }), (d) => d.tutorados.length === 0 && d.pendientes.length === 0),
    { initialValue: cargando<Datos>() },
  );

  protected readonly periodo = PERIODO;
  protected readonly plazo = PLAZO_REVISION_DIAS;
  protected readonly tipoTexto = TIPO_REVISION;
  protected readonly nombreCorto = nombreCorto;
  protected readonly rutaRevision = rutaRevision;
  protected readonly avance = avanceDe;
  protected readonly formatoFecha = formatoFecha;

  protected destacados(d: Datos): Pendiente[] {
    return d.pendientes.slice(0, DESTACADOS);
  }

  protected fueraDePlazo(d: Datos): number {
    return d.pendientes.filter((p) => p.fueraDePlazo).length;
  }

  protected rezagadas(d: Datos): Practica[] {
    return d.tutorados.filter(rezagada);
  }

  /** «Luciana y Diego»: los primeros nombres de las prácticas rezagadas. */
  protected nombresRezagadas(d: Datos): string {
    const nombres = this.rezagadas(d).map((p) => primerNombre(p.estudiante));
    return nombres.length > 1 ? `${nombres.slice(0, -1).join(', ')} y ${nombres[nombres.length - 1]}` : nombres.join('');
  }

  /** Tutorados que piden atención: los rezagados y los listos para la evaluación final. */
  protected atencion(d: Datos): Practica[] {
    return d.tutorados.filter((p) => rezagada(p) || listoParaEvaluar(p));
  }

  protected listo = listoParaEvaluar;

  protected paraEvaluar(d: Datos): Practica | undefined {
    return d.tutorados.find(listoParaEvaluar);
  }

  /** «Lo más antiguo primero: el reporte de Diego (semana 7) ya venció.» */
  protected subAcciones(d: Datos): string {
    const primero = d.pendientes[0];
    if (!primero) return 'No tiene pendientes de revisión.';
    if (!primero.fueraDePlazo) return 'Lo más antiguo primero.';
    const cosa = { reporte: 'el reporte', plan: 'el plan de actividades', informe: 'el informe final' }[primero.tipo];
    const semana = primero.semana === null ? '' : ` (semana ${primero.semana})`;
    return `Lo más antiguo primero: ${cosa} de ${primerNombre(primero.practica.estudiante)}${semana} ya venció.`;
  }
}
