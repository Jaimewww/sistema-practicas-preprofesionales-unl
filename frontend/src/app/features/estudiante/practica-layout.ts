import { Component, computed, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Insignia, Pestanas, Tarjeta, type PestanaItem } from '../../shared/ui';
import { EstudianteApi } from './estudiante.api';
import { carreraCorta, estadoPorPractica, nombrePropio, paramPractica, practicaActual, rezagada, textoPractica, textoTipo, tipoPractica } from './estudiante.util';
import { EstadoPantalla } from './ui/estado-pantalla';

/**
 * Marco de «Mi práctica»: la tarjeta «Datos de la práctica» y las pestañas (resumen, plan,
 * reportes e informe final) compartidas por las rutas hijas, que se pintan en el `router-outlet`.
 */
@Component({
  selector: 'app-practica-layout',
  imports: [RouterOutlet, Tarjeta, Insignia, Pestanas, EstadoPantalla],
  template: `
    <div class="grilla">
      @let e = estado();
      @if (e.tipo === 'exito') {
        @let p = e.datos;
        <app-tarjeta titulo="Datos de la práctica" [span]="12">
          <div class="cuerpo cabecera-datos">
            <dl class="datos datos--tres">
              <div><dt>Tipo</dt><dd>{{ textoTipo(p) }}</dd></div>
              <div><dt>Entidad receptora</dt><dd>{{ p.entidad }}</dd></div>
              <div><dt>Periodo académico</dt><dd>{{ p.periodo }}</dd></div>
              <div><dt>Tutor académico</dt><dd>{{ nombrePropio(p.tutorAcademico) }}</dd></div>
              @if (p.tipo === 'laboral') {
                <div><dt>Tutora de la entidad</dt><dd>{{ nombrePropio(p.tutorEntidad) }}</dd></div>
              } @else {
                <div><dt>Tutor de la entidad</dt><dd>No aplica en servicio comunitario</dd></div>
              }
              <div><dt>Carrera</dt><dd>{{ carreraCorta(p.carrera) }}</dd></div>
            </dl>
            <div class="columna">
              <app-insignia [tipo]="tipoPractica(p)" [texto]="textoPractica(p)" />
              <app-insignia [tipo]="rezagada(p) ? 'bad' : 'ok'" [texto]="rezagada(p) ? 'Rezagada' : 'Al día'" />
            </div>
          </div>
        </app-tarjeta>
      } @else {
        <app-estado-pantalla class="span-12" [estado]="e" />
      }
      <div class="span-12">
        <app-pestanas etiqueta="Secciones de la práctica" [items]="pestanas()" />
      </div>
      <router-outlet />
    </div>
  `,
  styleUrl: './pantalla.css',
  // Las pestañas ya traen su propio margen inferior: se descuenta el de la rejilla para que no se sume.
  styles: `
    app-pestanas {
      margin-bottom: calc(var(--espacio-4) * -1);
    }
  `,
})
export class PracticaLayout {
  private readonly api = inject(EstudianteApi);
  private readonly id = practicaActual();
  protected readonly estado = estadoPorPractica((id) => this.api.practica(id));

  protected readonly rezagada = rezagada;
  protected readonly textoPractica = textoPractica;
  protected readonly tipoPractica = tipoPractica;
  protected readonly textoTipo = textoTipo;
  protected readonly nombrePropio = nombrePropio;
  protected readonly carreraCorta = carreraCorta;

  protected readonly pestanas = computed<PestanaItem[]>(() => {
    const parametros = paramPractica(this.id());
    return [
      { texto: 'Resumen', enlace: '/estudiante/practica', parametros },
      { texto: 'Plan', enlace: '/estudiante/practica/plan', parametros },
      { texto: 'Reportes semanales', enlace: '/estudiante/practica/reportes', parametros },
      { texto: 'Informe final', enlace: '/estudiante/informe-final', parametros },
    ];
  });
}
