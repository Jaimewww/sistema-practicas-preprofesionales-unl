import { Component } from '@angular/core';

/**
 * Formulario de inicio de sesión (F-003).     RESPONSABLE: Jaime
 *
 * Pendiente: usuario y clave -> SesionService.iniciarSesion(); ante 429
 * mostrar el Retry-After; al terminar, Router.navigate(['/reportes/nuevo']).
 */
@Component({
  selector: 'app-login',
  template: `<h1>Iniciar sesión</h1><p>Inicio de sesión: pendiente (Jaime).</p>`,
})
export class Login {}
