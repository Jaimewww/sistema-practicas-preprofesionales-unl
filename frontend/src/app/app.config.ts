import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { environment } from '../environments/environment';
import { apiErrorInterceptor } from './core/api/api-error.interceptor';
import { authInterceptor } from './core/auth/auth.interceptor';
import { PracticasApi } from './features/practicas/practicas.api';
import { PracticasHttp } from './features/practicas/practicas.http';
import { PracticasMock } from './features/practicas/practicas.mock';
import { ReportesApi } from './features/reportes/reportes.api';
import { ReportesHttp } from './features/reportes/reportes.http';
import { ReportesMock } from './features/reportes/reportes.mock';
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(withInterceptors([authInterceptor, apiErrorInterceptor])),
    // Único lugar donde se elige mock o API real: los componentes inyectan el contrato.
    { provide: ReportesApi, useClass: environment.useMock ? ReportesMock : ReportesHttp },
    { provide: PracticasApi, useClass: environment.useMock ? PracticasMock : PracticasHttp },
  ],
};
