import { FormControl, Validators } from '@angular/forms';
import { ApiError } from './api/envelope';
import { accionDeError, estadoDeError, mensajeDeError } from './errores';
import { mensajesDeControl, validarHoras, validarSemana } from './validacion';

describe('mensajeDeError / accionDeError', () => {
  const filas: [string, ApiError, string, string][] = [
    ['400 validacion', new ApiError(400, 'validacion', 'x', { horas_reportadas: ['Muy alto.'] }), 'Muy alto.', 'marcar_campos'],
    ['401 no_autenticado', new ApiError(401, 'no_autenticado', 'x'), 'Tu sesión terminó.', 'ir_a_login'],
    ['403 permiso_denegado', new ApiError(403, 'permiso_denegado', 'x'), 'Solo un estudiante puede registrar horas.', 'ocultar_accion'],
    ['404 no_encontrado', new ApiError(404, 'no_encontrado', 'x'), 'No encontramos esa práctica.', 'volver_al_selector'],
    ['409 semana_duplicada', new ApiError(409, 'semana_duplicada', 'x'), 'Ya enviaste esa semana.', 'conservar_formulario'],
    ['409 practica_no_en_curso', new ApiError(409, 'practica_no_en_curso', 'x'), 'La práctica no está en curso.', 'deshabilitar_envio'],
    ['0 sin_conexion', new ApiError(0, 'sin_conexion', 'x'), 'No hay conexión con el servidor.', 'reintentar'],
    ['500', new ApiError(500, 'error_interno', 'Traceback secreto'), 'Ocurrió un problema en el servidor. Inténtalo de nuevo.', 'reintentar'],
  ];

  for (const [nombre, error, mensaje, accion] of filas) {
    it(nombre, () => {
      expect(mensajeDeError(error, 'registro_horas')).toBe(mensaje);
      expect(accionDeError(error)).toBe(accion);
    });
  }

  it('500 no expone detalles internos', () => {
    expect(mensajeDeError(new ApiError(500, 'x', 'Traceback secreto'), 'registro_horas')).not.toContain('Traceback');
  });

  it('fuera de E4 se conserva el detail del servidor, pero no el de un 500', () => {
    expect(mensajeDeError(new ApiError(404, 'no_encontrado', 'No encontrado.'))).toBe('No encontrado.');
    expect(mensajeDeError(new ApiError(500, 'x', 'Traceback secreto'))).not.toContain('Traceback');
  });

  it('estadoDeError arma el estado error', () => {
    const e = estadoDeError(new ApiError(404, 'no_encontrado', 'x'), 'registro_horas');
    expect(e).toEqual(expect.objectContaining({ tipo: 'error', mensaje: 'No encontramos esa práctica.' }));
  });
});

describe('validacion', () => {
  it('semana válida e inválidas', () => {
    expect(validarSemana()(new FormControl(1))).toBeNull();
    expect(validarSemana()(new FormControl(0))).toEqual({ semana: expect.any(Array) });
    expect(validarSemana()(new FormControl(1.5))).not.toBeNull();
    expect(validarSemana()(new FormControl(null))).not.toBeNull();
  });

  it('horas entre 1 y 168', () => {
    expect(validarHoras()(new FormControl(40))).toBeNull();
    expect(validarHoras()(new FormControl(0))).not.toBeNull();
    expect(validarHoras()(new FormControl(200))).not.toBeNull();
    expect(validarHoras()(new FormControl(2.5))).not.toBeNull();
  });

  it('ayudantía: máximo 10', () => {
    expect(validarHoras(() => 10)(new FormControl(10))).toBeNull();
    expect(validarHoras(() => 10)(new FormControl(11))).not.toBeNull();
  });

  it('mensajesDeControl usa la forma de error.campos', () => {
    const c = new FormControl(200, validarHoras());
    expect(mensajesDeControl(c)).toEqual(['Una semana tiene 168 horas: no se pueden reportar más.']);
  });

  it('mensajesDeControl ignora los errores nativos de Angular (max, min)', () => {
    const c = new FormControl(200, [validarHoras(), Validators.max(168)]);
    expect(mensajesDeControl(c)).toHaveLength(1);
  });
});
