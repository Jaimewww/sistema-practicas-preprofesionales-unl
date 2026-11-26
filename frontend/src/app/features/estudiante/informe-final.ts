import { Component, inject, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { avanceDe, ESTADO_PRACTICA, formatoFecha } from '../../core/demo';
import type { Practica } from '../../core/demo';
import { estadoDeError } from '../../core/errores';
import { Aviso, Insignia, Pasos, Tarjeta, type PasoItem, type TipoInsignia } from '../../shared/ui';
import { EstudianteApi } from './estudiante.api';
import { estadoPorPractica, nombrePropio, paramPractica, practicaActual } from './estudiante.util';
import { EstadoPantalla } from './ui/estado-pantalla';

const TAMANO_MAXIMO = 5 * 1024 * 1024;
const INSIGNIA: Record<'validado' | 'en_revision' | 'devuelto', { tipo: TipoInsignia; texto: string }> = {
  validado: { tipo: 'ok', texto: 'Revisado' },
  en_revision: { tipo: 'warn', texto: 'En revisión' },
  devuelto: { tipo: 'bad', texto: 'Devuelto con observación' },
};

/** E6 · Informe final: bloqueado hasta que la práctica esté en «revisión final»; muestra el camino al cierre. */
@Component({
  selector: 'app-informe-final',
  imports: [ReactiveFormsModule, Tarjeta, Pasos, Aviso, Insignia, EstadoPantalla],
  templateUrl: './informe-final.html',
  styleUrls: ['./pantalla.css', './informe-final.css'],
})
export class InformeFinal {
  private readonly api = inject(EstudianteApi);
  protected readonly id = practicaActual();
  protected readonly estado = estadoPorPractica((id) => this.api.practica(id));

  protected readonly form = new FormGroup({ resumen: new FormControl('', { nonNullable: true }) });
  protected readonly archivo = signal<File | null>(null);
  protected readonly errores = signal<string[]>([]);
  protected readonly enviando = signal(false);
  protected readonly presentado = signal(false);
  protected readonly paramPractica = paramPractica;
  protected readonly nombrePropio = nombrePropio;
  protected readonly formatoFecha = formatoFecha;
  protected readonly insignia = INSIGNIA;

  /** El informe solo se habilita en revisión final (o cerrada, para consultarlo). */
  protected bloqueado(p: Practica): boolean {
    return p.estado !== 'en_revision_final';
  }

  protected motivo(p: Practica): string {
    const av = avanceDe(p);
    return `Se habilita cuando su práctica pase a «revisión final». Hoy está «${ESTADO_PRACTICA[p.estado].toLowerCase()}» con ${av.validadas} de ${av.requeridas} h validadas.`;
  }

  protected elegir(archivos: FileList | null): void {
    this.archivo.set(archivos?.item(0) ?? null);
  }

  protected soltar(evento: DragEvent): void {
    evento.preventDefault();
    this.archivo.set(evento.dataTransfer?.files.item(0) ?? null);
  }

  protected presentar(): void {
    const errores: string[] = [];
    const resumen = this.form.controls.resumen.value.trim();
    const archivo = this.archivo();
    if (!resumen) errores.push('Escriba el resumen de su experiencia.');
    if (!archivo) errores.push('Adjunte su informe final en PDF.');
    else if (archivo.type !== 'application/pdf' && !archivo.name.toLowerCase().endsWith('.pdf')) errores.push('El informe debe estar en PDF.');
    else if (archivo.size > TAMANO_MAXIMO) errores.push('El informe no puede pesar más de 5 MB.');
    this.errores.set(errores);
    if (errores.length || !archivo) return;
    this.enviando.set(true);
    this.api.presentarInforme(this.id(), resumen, archivo.name).subscribe({
      next: () => {
        this.enviando.set(false);
        this.presentado.set(true);
      },
      error: (e: unknown) => {
        this.enviando.set(false);
        const resultado = estadoDeError<void>(e);
        this.errores.set([resultado.tipo === 'error' ? resultado.mensaje : 'No se pudo presentar el informe.']);
      },
    });
  }

  /** Camino al cierre: el primer paso sin cumplir es «donde está» la estudiante. */
  protected camino(p: Practica): PasoItem[] {
    const av = avanceDe(p);
    const informe = p.informeFinal;
    const hechos = [
      av.validadas >= av.requeridas,
      p.estado === 'en_revision_final' || p.estado === 'cerrada',
      !!informe,
      informe?.estado === 'validado',
      p.estado === 'cerrada',
    ];
    const pasos: Array<[string, string]> = [
      [`Completar las ${av.requeridas} h`, `${av.validadas} h validadas hasta hoy`],
      ['Revisión final', 'Se habilita el informe'],
      ['Presentar el informe', 'Queda «en revisión»'],
      ['Revisión del tutor académico', 'Aprueba o devuelve con observaciones'],
      ['Evaluación y cierre', 'Resultado «aprobada» desde 70 %'],
    ];
    const primero = hechos.indexOf(false);
    return pasos.map(([titulo, detalle], i) => ({
      estado: hechos[i] ? 'done' : i === primero ? 'now' : informe?.estado === 'devuelto' && i === 3 ? 'bad' : 'pendiente',
      titulo,
      detalle,
    }));
  }
}
