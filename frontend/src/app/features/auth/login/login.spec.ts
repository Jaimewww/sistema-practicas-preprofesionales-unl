import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { ApiError } from '../../../core/api/envelope';
import { SesionService } from '../../../core/auth/sesion.service';
import { Login } from './login';

/** Sesión falsa: el formulario se prueba sin red ni backend. */
function sesionFalsa(error?: ApiError) {
  return {
    iniciarSesion: vi.fn(() => (error ? throwError(() => error) : of(undefined))),
    cargarPerfil: vi.fn(() => of({ nombre: 'Cuenta de prueba', rol: 'tutor_academico' })),
    limpiarSesion: vi.fn(),
    refrescar: vi.fn(() => of(undefined)),
    cerrarSesion: vi.fn(() => of(undefined)),
  };
}

describe('Login (F-003)', () => {
  async function crear(error?: ApiError) {
    TestBed.configureTestingModule({
      imports: [Login],
      providers: [provideRouter([]), { provide: SesionService, useValue: sesionFalsa(error) }],
    });
    const fixture = TestBed.createComponent(Login);
    fixture.detectChanges();
    await fixture.whenStable();
    return fixture;
  }

  function completar(
    fixture: Awaited<ReturnType<typeof crear>>,
    usuario = 'jaime.torres',
    clave = 'demo-ape006',
  ) {
    fixture.componentInstance.form.setValue({ usuario, clave });
    fixture.detectChanges();
  }

  function vista(fixture: Awaited<ReturnType<typeof crear>>) {
    return fixture.nativeElement as HTMLElement;
  }

  function boton(fixture: Awaited<ReturnType<typeof crear>>) {
    return vista(fixture).querySelector('button[type=submit]') as HTMLButtonElement;
  }

  afterEach(() => vi.useRealTimers());

  it('429: muestra los segundos del Retry-After y deshabilita el envío hasta cero', async () => {
    vi.useFakeTimers();
    const fixture = await crear(
      new ApiError(
        429,
        'demasiadas_solicitudes',
        'Demasiados intentos. Intente de nuevo en 45 segundos.',
      ),
    );
    completar(fixture);

    fixture.componentInstance.enviar();
    fixture.detectChanges();

    // 429 es advertencia: la pinta el `.aviso` base del contrato, no el error.
    const aviso = vista(fixture).querySelector('.aviso');
    expect(aviso?.textContent).toContain('45 s');
    expect(aviso?.classList.contains('aviso-error')).toBe(false);
    expect(boton(fixture).disabled).toBe(true);

    vi.advanceTimersByTime(45_000);
    fixture.detectChanges();

    expect(boton(fixture).disabled).toBe(false);
    expect(vista(fixture).querySelector('.aviso')).toBeNull();
  });

  it('401: muestra el mensaje del servidor en el formulario', async () => {
    const fixture = await crear(
      new ApiError(401, 'no_autenticado', 'Usuario o contraseña incorrectos.'),
    );
    completar(fixture);

    fixture.componentInstance.enviar();
    fixture.detectChanges();

    expect(vista(fixture).querySelector('.aviso-error')?.textContent).toContain(
      'Usuario o contraseña incorrectos.',
    );
    expect(boton(fixture).disabled).toBe(false);
  });

  it('400: muestra el mensaje del campo que rechazó el servidor', async () => {
    const fixture = await crear(
      new ApiError(400, 'validacion', 'Datos inválidos.', {
        usuario: ['Este campo es obligatorio.'],
      }),
    );
    completar(fixture);

    fixture.componentInstance.enviar();
    fixture.detectChanges();

    expect(vista(fixture).querySelector('.campo--error')?.textContent).toContain(
      'Este campo es obligatorio.',
    );
  });

  it('status 0: explica que puede ser la conexión o CORS, sin culpar a la contraseña', async () => {
    const fixture = await crear(
      new ApiError(0, 'sin_conexion', 'No se pudo conectar con el servidor.'),
    );
    completar(fixture);

    fixture.componentInstance.enviar();
    fixture.detectChanges();

    const aviso = vista(fixture).querySelector('.aviso-error')?.textContent ?? '';
    expect(aviso).toContain('CORS');
    expect(aviso).toContain('http://localhost:4200');
  });

  it('200: navega al tablero según el rol', async () => {
    const fixture = await crear();
    const router = TestBed.inject(Router);
    const navegar = vi.spyOn(router, 'navigate').mockResolvedValue(true);
    completar(fixture);

    fixture.componentInstance.enviar();
    fixture.detectChanges();

    expect(navegar).toHaveBeenCalledWith(['/tutor-academico']);
  });

  it('el logo UNL usa la ruta única de assets públicos', async () => {
    const fixture = await crear();
    const logo = vista(fixture).querySelector('img') as HTMLImageElement;

    expect(logo.getAttribute('src')).toBe('/img/logo-unl.png');
    expect(logo.getAttribute('src')).not.toContain('data:');
    expect(vista(fixture).querySelectorAll('.hito')).toHaveLength(3);
  });
});
