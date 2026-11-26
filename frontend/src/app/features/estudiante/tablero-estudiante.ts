import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { cargando } from '../../core/estado-ui';
import { avanceDe, ESTUDIANTE, formatoFecha, PERIODO, TOTAL_SEMANAS } from '../../core/demo';
import type { Practica } from '../../core/demo';
import { BarraHoras, Insignia, Tarjeta, Vacio } from '../../shared/ui';
import { EstudianteApi } from './estudiante.api';
import { aEstado, carreraCorta, nombrePropio, paramPractica, paramsReporte, pendientes, rangoCorto, rangoEnLetras, requierenAccion, rezagada, textoPractica, textoReporte, textoTipo, tipoPractica, tipoReporte } from './estudiante.util';
import { EstadoPantalla } from './ui/estado-pantalla';

/** Tablero del estudiante (prototipo 01-home-estudiante): estado, horas, pendientes y últimos reportes. */
@Component({
  selector: 'app-tablero-estudiante',
  imports: [RouterLink, Tarjeta, Insignia, BarraHoras, Vacio, EstadoPantalla],
  templateUrl: './tablero-estudiante.html',
  styleUrls: ['./pantalla.css', './tablero-estudiante.css'],
})
export class TableroEstudiante {
  private readonly api = inject(EstudianteApi);
  protected readonly estado = toSignal(aEstado(this.api.misPracticas(), (lista) => lista.length === 0), { initialValue: cargando<Practica[]>() });

  protected readonly estudiante = ESTUDIANTE;
  protected readonly periodo = PERIODO;
  protected readonly semanas = TOTAL_SEMANAS;
  protected readonly avance = avanceDe;
  protected readonly pendientes = (p: Practica) => requierenAccion(pendientes(p));
  protected readonly ultimos = (p: Practica) => p.reportes.filter((r) => r.estado !== 'sin_reporte').slice(-4).reverse();
  protected readonly rezagada = rezagada;
  protected readonly textoPractica = textoPractica;
  protected readonly tipoPractica = tipoPractica;
  protected readonly textoTipo = textoTipo;
  protected readonly textoReporte = textoReporte;
  protected readonly tipoReporte = tipoReporte;
  protected readonly carreraCorta = carreraCorta;
  protected readonly nombrePropio = nombrePropio;
  protected readonly rangoCorto = rangoCorto;
  protected readonly rangoEnLetras = rangoEnLetras;
  protected readonly paramPractica = paramPractica;
  protected readonly paramsReporte = paramsReporte;
  protected readonly formatoFecha = formatoFecha;
}
