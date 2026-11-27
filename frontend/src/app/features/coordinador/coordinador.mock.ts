import { Injectable } from '@angular/core';
import { map, Observable, timer } from 'rxjs';
import { ApiError } from '../../core/api/envelope';
import { alertasDe, avanceDe, CONFIGURACION_CARRERA, fechaCierre, HOY, PERIODO, PRACTICAS_CARRERA, COORDINADOR } from '../../core/demo';
import type { ConfiguracionCarrera, EntradaHistorial, EstadoPractica, Practica } from '../../core/demo';
import { CoordinadorApi } from './coordinador.api';
import type { DetallePractica, FilaAlerta, FilaConsolidado, FilaPractica, ResumenCarrera } from './coordinador.model';
import { CLAVES_ALERTA, validarConfiguracion } from './coordinador.util';

const ESTADOS: readonly EstadoPractica[] = ['en_curso', 'asignada', 'en_revision_final', 'suspendida', 'cancelada', 'cerrada'];

/** Mock en memoria sobre `core/demo`: las 150 prácticas de la carrera del coordinador. */
@Injectable()
export class CoordinadorMock extends CoordinadorApi {
  /** Espera simulada por defecto; los tests la ponen en 0 para no esperar. */
  static demoraPorDefecto = 400;
  demoraMs = CoordinadorMock.demoraPorDefecto;
  private config: ConfiguracionCarrera = { ...CONFIGURACION_CARRERA };
  /** Decisiones tomadas en esta sesión: la práctica con su nuevo estado e historial. */
  private readonly cambios = new Map<number, Practica>();

  private todas(): Practica[] {
    return PRACTICAS_CARRERA.map((p) => this.cambios.get(p.id) ?? p);
  }

  private filas(): FilaPractica[] {
    return this.todas().map((practica) => ({ practica, avance: avanceDe(practica, this.config.umbralRezago), alertas: alertasDe(practica, this.config) }));
  }

  resumen(): Observable<ResumenCarrera> {
    return this.responder(() => {
      const filas = this.filas();
      const cuenta = (tipo: string) => filas.reduce((n, f) => n + f.alertas.filter((a) => a.tipo === tipo).length, 0);
      const porAlerta = CLAVES_ALERTA.map((tipo) => ({ tipo, cantidad: cuenta(tipo) }));
      return {
        periodo: PERIODO,
        total: filas.length,
        enCurso: filas.filter((f) => f.practica.estado === 'en_curso').length,
        rezagadas: cuenta('rezago'),
        alertasActivas: porAlerta.reduce((n, a) => n + a.cantidad, 0),
        porEstado: ESTADOS.map((estado) => ({ estado, cantidad: filas.filter((f) => f.practica.estado === estado).length })),
        porAlerta,
        decisiones: filas.map((f) => f.practica).filter((p) => p.estado === 'en_revision_final' || p.estado === 'suspendida'),
      };
    });
  }

  practicas(): Observable<FilaPractica[]> {
    return this.responder(() => this.filas());
  }

  alertas(): Observable<FilaAlerta[]> {
    return this.responder(() =>
      this.filas().flatMap((f) => f.alertas.map((alerta) => ({ alerta, estudiante: f.practica.estudiante, tipoPractica: f.practica.tipo, tutorAcademico: f.practica.tutorAcademico }))),
    );
  }

  practica(id: number): Observable<DetallePractica> {
    return this.responder(() => this.detalle(this.buscar(id)));
  }

  suspender(id: number, motivo: string): Observable<DetallePractica> {
    return this.cambiar(id, 'en_curso', 'suspendida', motivo, 'Solo se suspende una práctica en curso.');
  }

  cancelar(id: number, motivo: string): Observable<DetallePractica> {
    return this.cambiar(id, 'suspendida', 'cancelada', motivo, 'Solo se cancela una práctica suspendida.');
  }

  reanudar(id: number): Observable<DetallePractica> {
    return this.cambiar(id, 'suspendida', 'en_curso', 'Práctica reanudada.', 'Solo se reanuda una práctica suspendida.', false);
  }

  cerrar(id: number, evaluacion: number): Observable<DetallePractica> {
    return this.responder(() => {
      const p = this.buscar(id);
      if (p.estado === 'cerrada' || p.estado === 'cancelada') throw new ApiError(409, 'transicion_invalida', 'La práctica ya no admite cambios.');
      const resultado = evaluacion >= 70 ? 'aprobada' : 'no_aprobada';
      return this.detalle(this.aplicar(p, 'cerrada', 'Práctica cerrada con el resultado de la evaluación final.', resultado));
    });
  }

  consolidado(): Observable<FilaConsolidado[]> {
    return this.responder(() =>
      this.todas()
        .filter((p) => p.estado === 'cerrada')
        .map((p) => ({
          estudiante: p.estudiante,
          periodo: p.periodo,
          componente: p.tipo,
          horasValidadas: avanceDe(p).validadas,
          horasRequeridas: p.horasRequeridas,
          resultado: p.resultado,
          cierre: fechaCierre(p) ?? '',
        }))
        .sort((a, b) => a.estudiante.localeCompare(b.estudiante, 'es') || a.componente.localeCompare(b.componente)),
    );
  }

  configuracion(): Observable<ConfiguracionCarrera> {
    return this.responder(() => ({ ...this.config }));
  }

  guardarConfiguracion(config: ConfiguracionCarrera): Observable<ConfiguracionCarrera> {
    return this.responder(() => {
      const errores = validarConfiguracion(config);
      const campos = Object.keys(errores);
      if (campos.length) throw new ApiError(400, 'validacion', 'Datos inválidos.', Object.fromEntries(campos.map((c) => [c, [errores[c as keyof typeof errores] as string]])));
      this.config = { ...config };
      return { ...this.config };
    });
  }

  private cambiar(id: number, desde: EstadoPractica, hacia: EstadoPractica, motivo: string, aviso: string, exigirMotivo = true): Observable<DetallePractica> {
    return this.responder(() => {
      const p = this.buscar(id);
      if (exigirMotivo && !motivo.trim()) throw new ApiError(400, 'validacion', 'Datos inválidos.', { motivo: ['Escriba el motivo de la decisión.'] });
      if (p.estado !== desde) throw new ApiError(409, 'transicion_invalida', aviso);
      return this.detalle(this.aplicar(p, hacia, motivo.trim()));
    });
  }

  private aplicar(p: Practica, hacia: EstadoPractica, motivo: string, resultado: Practica['resultado'] = p.resultado): Practica {
    const entrada: EntradaHistorial = { estadoAnterior: p.estado, estadoNuevo: hacia, autor: COORDINADOR, fecha: HOY, motivo };
    const nueva: Practica = { ...p, estado: hacia, resultado, historial: [...p.historial, entrada] };
    this.cambios.set(p.id, nueva);
    return nueva;
  }

  private detalle(practica: Practica): DetallePractica {
    return { practica, alertas: alertasDe(practica, this.config), historial: practica.historial };
  }

  private buscar(id: number): Practica {
    const p = this.todas().find((x) => x.id === id);
    if (!p) throw new ApiError(404, 'no_encontrado', 'No encontrado.');
    return p;
  }

  private responder<T>(obtener: () => T): Observable<T> {
    return timer(this.demoraMs).pipe(map(obtener));
  }
}

