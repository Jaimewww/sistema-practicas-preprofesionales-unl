import { Component } from '@angular/core';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-inicio',
  template: `
    <h1>Sistema de Prácticas Preprofesionales</h1>
    <p>Frontend de la APE-006: consumo de <code>POST /api/v1/practicas/&#123;id&#125;/reportes/</code>.</p>
    <p>Modo de datos: <strong>{{ useMock ? 'simulado (mock)' : 'API real' }}</strong>.</p>
  `,
})
export class Inicio {
  readonly useMock = environment.useMock;
}
