import { Component, computed, inject, linkedSignal, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { map } from 'rxjs';
import { formatoFecha } from '../../core/demo';
import type { Practica } from '../../core/demo';
import { estadoDeError } from '../../core/errores';
import { cargando } from '../../core/estado-ui';
import { Aviso, Tarjeta } from '../../shared/ui';
import { TutorEntidadApi } from './tutor-entidad.api';
import type { RegistroInformeExterno } from './tutor-entidad.model';
import { aEstado, errorDeArchivo, idDeParametro, MAXIMO_MB, subtipoTexto } from './tutor-entidad.util';
import { EstadoPantalla } from './ui/estado-pantalla';

interface ArchivoElegido {
  nombre: string;
  bytes: number;
}

/** R4 · Informe externo: valoración y PDF firmado (hasta 5 MB) del tutor de la entidad sobre su practicante. */
@Component({
  selector: 'app-informe-externo',
  imports: [FormsModule, RouterLink, Tarjeta, Aviso, EstadoPantalla],
  templateUrl: './informe-externo.html',
  styleUrls: ['./pantalla.css'],
})
export class InformeExterno {
  private readonly api = inject(TutorEntidadApi);
  protected readonly estado = toSignal(aEstado(this.api.practicantes(), (l) => l.length === 0), { initialValue: cargando<Practica[]>() });
  private readonly pedido = toSignal(inject(ActivatedRoute).queryParamMap.pipe(map((q) => idDeParametro(q.get('p')))), { initialValue: null });

  /** Practicante elegido: el de `?p=` si existe en la lista; si no, el primero. */
  private readonly lista = computed(() => {
    const e = this.estado();
    return e.tipo === 'exito' ? e.datos : [];
  });
  protected readonly seleccionado = linkedSignal<Practica[], number | null>({
    source: this.lista,
    computation: (lista) => {
      const p = this.pedido();
      return lista.find((x) => x.id === p)?.id ?? lista[0]?.id ?? null;
    },
  });
  protected readonly practica = computed(() => this.lista().find((p) => p.id === this.seleccionado()) ?? null);

  protected valoracion = '';
  protected readonly archivo = signal<ArchivoElegido | null>(null);
  protected readonly errorValoracion = signal('');
  protected readonly errorArchivo = signal('');
  protected readonly errores = signal<string[]>([]);
  protected readonly enviando = signal(false);
  protected readonly registro = signal<(RegistroInformeExterno) | null>(null);
  protected readonly maximo = MAXIMO_MB;
  protected readonly formatoFecha = formatoFecha;
  protected readonly subtipoTexto = subtipoTexto;

  /** Archivos de prueba de la demostración («Probar archivo»). */
  protected readonly pruebas: ReadonlyArray<ArchivoElegido & { texto: string }> = [
    { nombre: 'informe-entidad.pdf', bytes: Math.round(1.2 * 1048576), texto: 'informe-entidad.pdf (1,2 MB)' },
    { nombre: 'informe-entidad.docx', bytes: Math.round(0.4 * 1048576), texto: 'informe-entidad.docx' },
    { nombre: 'informe-entidad.pdf', bytes: Math.round(7.2 * 1048576), texto: 'informe de 7,2 MB' },
  ];

  protected elegirReal(archivos: FileList | null): void {
    const f = archivos ? Array.from(archivos)[0] : undefined;
    this.archivo.set(f ? { nombre: f.name, bytes: f.size } : null);
  }

  protected probar(evento: Event, a: ArchivoElegido, entrada: HTMLInputElement): void {
    evento.preventDefault();
    entrada.value = '';
    this.archivo.set({ nombre: a.nombre, bytes: a.bytes });
  }

  protected guardar(): void {
    const practica = this.practica();
    if (!practica) return;
    const errores: string[] = [];
    const sinValoracion = !this.valoracion.trim();
    this.errorValoracion.set(sinValoracion ? 'Describa la valoración del desempeño.' : '');
    if (sinValoracion) errores.push('Describa la valoración del desempeño.');
    const e = errorDeArchivo(this.archivo());
    this.errorArchivo.set(e ?? '');
    if (e) errores.push(e);
    this.errores.set(errores);
    if (errores.length) return;
    this.enviando.set(true);
    this.api.registrarInformeExterno(practica.id, this.valoracion, this.archivo()!).subscribe({
      next: (r) => {
        this.enviando.set(false);
        this.registro.set(r);
      },
      error: (err: unknown) => {
        this.enviando.set(false);
        const r = estadoDeError<void>(err);
        this.errores.set([r.tipo === 'error' ? r.mensaje : 'No se pudo registrar el informe.']);
      },
    });
  }
}
