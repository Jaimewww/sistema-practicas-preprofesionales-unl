import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

/**
 * Raíz: solo el `router-outlet`. `/login` se pinta fuera del tablero; el armazón
 * (menú, banner y contenido) es la ruta hija `''` con `Shell` en `app.routes.ts`.
 */
@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  template: `<router-outlet />`,
})
export class App {}
