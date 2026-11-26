import { Component } from '@angular/core';
import { RouterLink, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink],
  template: `
    <nav>
      <a routerLink="/">Inicio</a> · <a routerLink="/login">Iniciar sesión</a> ·
      <a routerLink="/reportes/nuevo">Registrar horas</a>
    </nav>
    <main><router-outlet /></main>
  `,
})
export class App {}
