import { USE_MOCK } from '../api/config';
import { PracticasHttp } from './practicas.http';
import { PracticasMock } from './practicas.mock';
import type { PracticasApi } from './tipos';

export const practicasApi: PracticasApi = USE_MOCK ? new PracticasMock() : new PracticasHttp();

export type * from './tipos';
