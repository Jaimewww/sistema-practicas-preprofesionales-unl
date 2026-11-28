import { Routes } from '@angular/router';
import { Anexos } from './anexos';
import { Legalizar } from './legalizar';
import { SecretariaApi } from './secretaria.api';
import { SecretariaMock } from './secretaria.mock';
import { TableroSecretaria } from './tablero-secretaria';

const INICIO = { texto: 'Inicio', enlace: '/secretaria' };
const ANEXOS = { texto: 'Anexos por legalizar', enlace: '/secretaria/anexos' };

/**
 * Rutas de «Secretaría de carrera» (prefijo `/secretaria`). Las pantallas del rol van en `children` con su
 * `data: { titulo, migas }`; los servicios del rol (`*Api` → `*Mock`) van en `providers` del padre.
 */
export const RUTAS_SECRETARIA: Routes = [
  {
    path: '',
    providers: [{ provide: SecretariaApi, useClass: SecretariaMock }],
    children: [
      {
        path: '',
        component: TableroSecretaria,
        title: 'Tablero · Prácticas UNL',
        data: { titulo: 'Tablero', migas: [{ texto: 'Inicio' }], foto: true },
      },
      {
        path: 'anexos',
        component: Anexos,
        title: 'Anexos por legalizar · Prácticas UNL',
        data: { titulo: 'Anexos por legalizar', migas: [INICIO, { texto: 'Prácticas' }, { texto: 'Anexos por legalizar' }] },
      },
      {
        path: 'legalizar',
        component: Legalizar,
        title: 'Legalizar anexo · Prácticas UNL',
        data: { titulo: 'Legalizar anexo', migas: [INICIO, ANEXOS, { texto: 'Legalizar' }] },
      },
    ],
  },
];
