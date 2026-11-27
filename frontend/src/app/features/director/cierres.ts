import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { cargando } from '../../core/estado-ui';
import { CARRERA, filtrarPracticas, PERIODO, PERIODO_ANTERIOR, avanceDe } from '../../core/demo';
import type { Practica, ResultadoPractica, TipoPractica } from '../../core/demo';
import { Insignia, Tarjeta, Vacio } from '../../shared/ui';
import { DirectorApi } from './director.api';
import { aEstado, detalleEntidad, textoResultado, textoTipo, tipoResultado } from './director.util';
import { EstadoPantalla } from './ui/estado-pantalla';

/** D1 · Cierres de mi carrera: lista de solo lectura con filtros por período, tipo, resultado y estudiante. */
@Component({
  selector: 'app-cierres',
  imports: [RouterLink, Tarjeta, Insignia, Vacio, EstadoPantalla],
  template: `
    @let e = estado();
    @if (e.tipo === 'exito') {
      @let filas = filtradas();
      <div class="grilla">
        <app-tarjeta titulo="Prácticas cerradas" sub="Solo lectura: aprobada o no aprobada según la evaluación final." [span]="12">
          <div class="filtros" role="search" aria-label="Filtros de los cierres">
            <label for="f-periodo">
              Período
              <select id="f-periodo" [value]="periodo()" (change)="periodo.set($any($event.target).value)">
                <option value="">Todos los períodos</option>
                @for (p of periodos; track p) {
                  <option [value]="p">{{ p }}</option>
                }
              </select>
            </label>
            <label for="f-tipo">
              Tipo
              <select id="f-tipo" [value]="tipo()" (change)="tipo.set($any($event.target).value)">
                <option value="">Todos los tipos</option>
                <option value="laboral">Laboral</option>
                <option value="comunitaria">Comunitaria</option>
              </select>
            </label>
            <label for="f-res">
              Resultado
              <select id="f-res" [value]="resultado()" (change)="resultado.set($any($event.target).value)">
                <option value="">Todos los resultados</option>
                <option value="aprobada">Aprobada</option>
                <option value="no_aprobada">No aprobada</option>
              </select>
            </label>
            <label for="f-q">
              Estudiante
              <input id="f-q" type="text" placeholder="Nombre o apellido" [value]="busqueda()" (input)="busqueda.set($any($event.target).value)" />
            </label>
            <button type="button" class="boton-secundario" (click)="limpiar()">Limpiar</button>
          </div>
          <p class="texto" aria-live="polite">{{ carrera }} · <strong>{{ filas.length }}</strong> prácticas</p>
          @if (filas.length > 0) {
            <div class="tabla-marco">
              <table class="tbl">
                <caption class="sr-only">Prácticas cerradas de la carrera con su resultado</caption>
                <thead>
                  <tr>
                    <th scope="col">Estudiante</th>
                    <th scope="col">Tipo</th>
                    <th scope="col">Resultado</th>
                    <th scope="col">Horas validadas</th>
                    <th scope="col">Requeridas</th>
                    <th scope="col">Tutor académico</th>
                    <th scope="col">Acción</th>
                  </tr>
                </thead>
                <tbody>
                  @for (p of filas; track p.id) {
                    <tr>
                      <td><strong>{{ p.estudiante }}</strong><small>{{ p.periodo }}</small></td>
                      <td>{{ textoTipo(p) }}<small>{{ detalleEntidad(p) }}</small></td>
                      <td><app-insignia [tipo]="tipoResultado(p.resultado)" [texto]="textoResultado(p.resultado)" /></td>
                      <td><strong>{{ validadas(p) }} h</strong></td>
                      <td>{{ p.horasRequeridas }} h</td>
                      <td>{{ p.tutorAcademico }}</td>
                      <td><a class="boton-secundario" routerLink="/director/cierre" [queryParams]="{ p: p.id }" [attr.aria-label]="'Ver cierre de ' + p.estudiante">Ver cierre</a></td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
          } @else {
            <app-vacio titulo="No hay cierres con estos filtros" texto="No hay prácticas cerradas para el período, tipo o resultado elegidos." />
          }
        </app-tarjeta>
      </div>
    } @else {
      <app-estado-pantalla [estado]="e" vacioTitulo="Aún no hay cierres" vacioTexto="Cuando el coordinador cierre una práctica de su carrera la verá aquí." />
    }
  `,
  styleUrl: './pantalla.css',
})
export class Cierres {
  private readonly api = inject(DirectorApi);
  protected readonly estado = toSignal(aEstado(this.api.cierres(), (lista) => lista.length === 0), { initialValue: cargando<Practica[]>() });

  protected readonly carrera = CARRERA;
  protected readonly periodos = [PERIODO, PERIODO_ANTERIOR];
  protected readonly periodo = signal('');
  protected readonly tipo = signal('');
  protected readonly resultado = signal('');
  protected readonly busqueda = signal('');

  protected readonly textoTipo = textoTipo;
  protected readonly textoResultado = textoResultado;
  protected readonly tipoResultado = tipoResultado;
  protected readonly detalleEntidad = detalleEntidad;
  protected readonly validadas = (p: Practica): number => avanceDe(p).validadas;

  protected readonly filtradas = computed<Practica[]>(() => {
    const e = this.estado();
    if (e.tipo !== 'exito') return [];
    const resultado = this.resultado() as ResultadoPractica | '';
    return filtrarPracticas(e.datos, { periodo: this.periodo(), tipo: (this.tipo() as TipoPractica) || undefined, busqueda: this.busqueda() }).filter((p) => !resultado || p.resultado === resultado);
  });

  protected limpiar(): void {
    this.periodo.set('');
    this.tipo.set('');
    this.resultado.set('');
    this.busqueda.set('');
  }
}
