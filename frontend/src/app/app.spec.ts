import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { App } from './app';

describe('App', () => {
  it('muestra la navegación al inicio, al login y al tablero del estudiante', async () => {
    TestBed.configureTestingModule({ imports: [App], providers: [provideRouter([])] });
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const vista = fixture.nativeElement as HTMLElement;
    (vista.querySelector('.usuario__boton') as HTMLButtonElement).click();
    fixture.detectChanges();
    const rutas = new Set([...vista.querySelectorAll('a[href]')].map((a) => a.getAttribute('href')));
    expect(rutas).toContain('/');
    expect(rutas).toContain('/login');
    expect(rutas).toContain('/estudiante');
    expect(vista.querySelector('router-outlet')).not.toBeNull();
  });
});
