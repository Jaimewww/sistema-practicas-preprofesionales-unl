import { Component } from '@angular/core';
import { Shell } from './layout/shell';

/** Raíz: delega todo el armazón (menú con RouterLink, banner y router-outlet) en el Shell. */
@Component({
  selector: 'app-root',
  imports: [Shell],
  template: `<app-shell />`,
})
export class App {}
