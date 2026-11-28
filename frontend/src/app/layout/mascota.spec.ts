import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Mascota } from './mascota';

function simularMovimientoReducido(reducido: boolean): void {
  vi.stubGlobal('matchMedia', (query: string) => ({ matches: reducido, media: query }));
}

describe('Mascota', () => {
  let fixture: ComponentFixture<Mascota>;
  let vista: HTMLElement;

  function montar(nombre?: string): void {
    fixture = TestBed.createComponent(Mascota);
    if (nombre !== undefined) fixture.componentRef.setInput('nombre', nombre);
    fixture.detectChanges();
    vista = fixture.nativeElement as HTMLElement;
  }

  const oso = () => vista.querySelector('.oso') as HTMLButtonElement;
  const globo = () => vista.querySelector('.oso__globo');
  const avanzar = (ms: number) => {
    vi.advanceTimersByTime(ms);
    fixture.detectChanges();
  };

  beforeEach(() => {
    vi.useFakeTimers();
    simularMovimientoReducido(false);
  });

  afterEach(() => {
    fixture?.destroy();
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('pinta las dos capas con su src, alt y aria-hidden', () => {
    montar();
    const cuerpo = vista.querySelector('.oso__cuerpo');
    const brazo = vista.querySelector('.oso__brazo');
    expect(cuerpo?.getAttribute('src')).toBe('/img/oso-cuerpo.png');
    expect(cuerpo?.getAttribute('alt')).toBe('Mascota UNL: oso con suéter rojo y libro');
    expect(brazo?.getAttribute('src')).toBe('/img/oso-brazo.png');
    expect(brazo?.getAttribute('alt')).toBe('');
    expect(brazo?.getAttribute('aria-hidden')).toBe('true');
    expect(oso().getAttribute('aria-label')).toBe('Saludar a la mascota UNL');
    expect(globo()).toBeNull();
  });

  it('el ciclo automático arranca a los 1,5 s y rota saludar, saltar, balancear', () => {
    montar();
    avanzar(1499);
    expect(oso().classList.contains('oso--ninguna')).toBe(true);
    avanzar(1);
    expect(oso().classList.contains('oso--saludar')).toBe(true);
    avanzar(1800);
    expect(oso().classList.contains('oso--ninguna')).toBe(true);
    avanzar(7000 - 1800);
    expect(oso().classList.contains('oso--saltar')).toBe(true);
    avanzar(700);
    expect(oso().classList.contains('oso--ninguna')).toBe(true);
    avanzar(7000 - 700);
    expect(oso().classList.contains('oso--balancear')).toBe(true);
    avanzar(1600);
    expect(oso().classList.contains('oso--ninguna')).toBe(true);
  });

  it('hover: salta y saluda justo después', () => {
    montar();
    oso().dispatchEvent(new Event('mouseenter'));
    fixture.detectChanges();
    expect(oso().classList.contains('oso--saltar')).toBe(true);
    avanzar(700);
    expect(oso().classList.contains('oso--saludar')).toBe(true);
    avanzar(1800);
    expect(oso().classList.contains('oso--ninguna')).toBe(true);
  });

  it('el clic muestra «¡Hola, Luciana!» 3,5 s y el siguiente clic, el siguiente mensaje', () => {
    montar('Luciana');
    oso().click();
    fixture.detectChanges();
    expect(globo()?.textContent?.trim()).toBe('¡Hola, Luciana!');
    expect(globo()?.getAttribute('role')).toBe('status');
    expect(oso().classList.contains('oso--saludar')).toBe(true);
    avanzar(3499);
    expect(globo()).not.toBeNull();
    avanzar(1);
    expect(globo()).toBeNull();

    oso().click();
    fixture.detectChanges();
    expect(globo()?.textContent?.trim()).toBe('¡Bienvenido al SIAAF!');
    avanzar(3000);
    oso().click();
    fixture.detectChanges();
    expect(globo()?.textContent?.trim()).toBe('¡Qué gusto verte!');
    avanzar(3000);
    expect(globo()).not.toBeNull(); // el temporizador se reinició
    avanzar(500);
    expect(globo()).toBeNull();
  });

  it('sin nombre el mensaje es «¡Hola!»', () => {
    montar();
    oso().click();
    fixture.detectChanges();
    expect(globo()?.textContent?.trim()).toBe('¡Hola!');
  });

  it('silencioso: el clic deja el saludo en movimiento sin globo de texto', () => {
    montar('| Cuenta');
    fixture.componentRef.setInput('callado', true);
    fixture.detectChanges();

    oso().click();
    fixture.detectChanges();
    expect(oso().classList.contains('oso--saludar')).toBe(true);
    expect(globo()).toBeNull();
  });

  it('con movimiento reducido no hay ciclo ni hover, pero el clic muestra el globo', () => {
    simularMovimientoReducido(true);
    montar('Luciana');
    vi.advanceTimersByTime(0); // vacía los temporizadores internos de Angular
    expect(vi.getTimerCount()).toBe(0);
    avanzar(20000);
    expect(oso().classList.contains('oso--ninguna')).toBe(true);
    oso().dispatchEvent(new Event('mouseenter'));
    fixture.detectChanges();
    expect(oso().classList.contains('oso--ninguna')).toBe(true);
    oso().click();
    fixture.detectChanges();
    expect(globo()?.textContent?.trim()).toBe('¡Hola, Luciana!');
    expect(oso().classList.contains('oso--ninguna')).toBe(true);
    avanzar(3500);
    expect(globo()).toBeNull();
  });

  it('no deja temporizadores pendientes al destruirse', () => {
    montar('Luciana');
    avanzar(1500);
    oso().click();
    fixture.detectChanges();
    expect(vi.getTimerCount()).toBeGreaterThan(0);
    fixture.destroy();
    vi.advanceTimersByTime(0);
    expect(vi.getTimerCount()).toBe(0);
  });
});
