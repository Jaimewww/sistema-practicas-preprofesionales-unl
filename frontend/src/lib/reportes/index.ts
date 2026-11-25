import { USE_MOCK } from '../api/config';
import { ReportesHttp } from './reportes.http';
import { ReportesMock } from './reportes.mock';
import type { ReportesApi } from './tipos';

/** Punto único de acceso: los componentes importan `reportesApi`, nunca la clase. */
export const reportesApi: ReportesApi = USE_MOCK ? new ReportesMock() : new ReportesHttp();

export type * from './tipos';
