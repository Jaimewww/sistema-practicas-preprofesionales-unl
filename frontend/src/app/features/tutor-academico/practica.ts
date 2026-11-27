import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { avanceDe, ESTADO_PRACTICA, formatoFecha, RESULTADO_PRACTICA } from '../../core/demo';
import type { EntradaHistorial, Practica as PracticaDemo } from '../../core/demo';
import { Aviso, BarraHoras, Insignia, Pasos, Tarjeta, Vacio, type PasoItem } from '../../shared/ui';
import { TutorAcademicoApi } from './tutor-academico.api';
import type { DetallePractica } from './tutor-academico.model';
import { avisoSoloLectura, confirmacion, descripcionPractica, estadoPorParametro, rangoLargo, textoPractica, textoReporte, textoRevision, tipoPractica, tipoReporte, tipoRevision } from './tutor-academico.util';
import { EstadoPantalla } from './ui/estado-pantalla';
import { EstadosEjemplo, type EstadoEjemplo } from './ui/estados-ejemplo';
import { FranjaSemanas } from './ui/franja-semanas';

/** T4 · Práctica del tutorado: datos, horas, reportes, plan, informes, incumplimientos e historial. */
@Component({
  selector: 'app-practica-tutorado',
  imports: [RouterLink, Tarjeta, Insignia, Aviso, BarraHoras, Pasos, Vacio, EstadoPantalla, EstadosEjemplo, FranjaSemanas],
  templateUrl: './practica.html',
  styleUrl: './pantalla.css',
})
export class PracticaTutorado {
  private readonly api = inject(TutorAcademicoApi);
  protected readonly estado = estadoPorParametro('p', (clave) => this.api.practica(clave));

  protected readonly ejemplos: EstadoEjemplo[] = [
    { clave: '1', texto: 'Luciana (en curso, rezagada)' },
    { clave: '3', texto: 'Diego (en curso, rezagada)' },
    { clave: '4', texto: 'Andrea (asignada)' },
    { clave: '5', texto: 'Mateo (revisión final)' },
    { clave: '6', texto: 'Valeria (revisión final)' },
    { clave: 'ro', texto: 'Suspendida (solo lectura)' },
  ];

  protected readonly avance = avanceDe;
  protected readonly descripcion = descripcionPractica;
  protected readonly tipoPractica = tipoPractica;
  protected readonly textoPractica = textoPractica;
  protected readonly tipoReporte = tipoReporte;
  protected readonly textoReporte = textoReporte;
  protected readonly tipoRevision = tipoRevision;
  protected readonly textoRevision = textoRevision;
  protected readonly confirmacion = confirmacion;
  protected readonly avisoSoloLectura = avisoSoloLectura;
  protected readonly rangoLargo = rangoLargo;
  protected readonly formatoFecha = formatoFecha;
  protected readonly resultado = RESULTADO_PRACTICA;

  protected activo(d: DetallePractica): string {
    return d.soloLectura ? 'ro' : String(d.practica.id);
  }

  /** Estado de horas en palabras: se compara lo validado y en revisión con el mínimo del umbral. */
  protected enCurso(p: PracticaDemo): { rezagada: boolean; suma: number; minimas: number; esperadas: number } {
    const av = avanceDe(p);
    return { rezagada: av.rezagada, suma: av.validadas + av.enRevision, minimas: av.minimas, esperadas: av.esperadas };
  }

  protected historial(p: PracticaDemo): PasoItem[] {
    return p.historial.map((h: EntradaHistorial, i) => ({
      estado: h.estadoNuevo === 'suspendida' || h.estadoNuevo === 'cancelada' ? 'bad' : i === p.historial.length - 1 && h.estadoNuevo === 'en_revision_final' ? 'now' : 'done',
      titulo: ESTADO_PRACTICA[h.estadoNuevo],
      detalle: `${formatoFecha(h.fecha)} · ${h.autor}${h.motivo ? ' · ' + h.motivo : ''}`,
    }));
  }

  protected conEsperadas(p: PracticaDemo): boolean {
    return p.estado === 'en_curso' || p.estado === 'suspendida';
  }
}
