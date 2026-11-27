import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Tarjeta } from '../../shared/ui';
import { TutorAcademicoApi } from './tutor-academico.api';
import { estadoPorParametro } from './tutor-academico.util';
import { EstadoPantalla } from './ui/estado-pantalla';
import { EstadosEjemplo, type EstadoEjemplo } from './ui/estados-ejemplo';
import { FormularioEvaluacion, MINIMO_APROBACION } from './ui/formulario-evaluacion';

/** Práctica que se evalúa cuando la URL no trae `?p=`: la lista para evaluar. */
const PRACTICA_POR_DEFECTO = 5;

/** T5 · Evaluación final: registrar el porcentaje de desempeño; muestra en vivo el resultado (aprobada desde 70 %). */
@Component({
  selector: 'app-evaluacion-final',
  imports: [RouterLink, Tarjeta, EstadoPantalla, EstadosEjemplo, FormularioEvaluacion],
  template: `
    @let e = estado();
    @if (e.tipo === 'exito') {
      @let d = e.datos;
      <div class="grilla">
        <div class="span-12"><app-estados-ejemplo parametro="p" [estados]="ejemplos" [activo]="'' + d.practica.id" /></div>
        <app-tarjeta titulo="Evaluación final" [span]="8">
          <app-formulario-evaluacion [datos]="d" />
        </app-tarjeta>
        <app-tarjeta titulo="Qué se necesita" [span]="4">
          <dl class="dl">
            <dt>Informe final</dt>
            <dd>Revisado y validado</dd>
            <dt>Informe externo</dt>
            <dd>Registrado por el tutor de la entidad</dd>
            <dt>Regla</dt>
            <dd>Aprobada desde {{ minimo }} % (RF-17, Art. 339)</dd>
          </dl>
          <div class="acciones-fila">
            <a class="boton-secundario boton-sm" routerLink="/tutor-academico/practica" [queryParams]="{ p: d.practica.id }">Volver a la práctica</a>
          </div>
        </app-tarjeta>
      </div>
    } @else {
      <app-estado-pantalla [estado]="e" />
    }
  `,
  styleUrl: './pantalla.css',
})
export class EvaluacionFinal {
  private readonly api = inject(TutorAcademicoApi);
  protected readonly estado = estadoPorParametro('p', (clave) => this.api.evaluacion(clave === '' ? PRACTICA_POR_DEFECTO : Number(clave)));
  protected readonly minimo = MINIMO_APROBACION;

  protected readonly ejemplos: EstadoEjemplo[] = [
    { clave: '5', texto: 'Mateo (listo para evaluar)' },
    { clave: '6', texto: 'Valeria (faltan informes)' },
  ];
}
