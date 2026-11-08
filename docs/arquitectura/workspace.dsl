workspace "Sistema de seguimiento de prácticas preprofesionales UNL" "Modelo C4 (C1 contexto, C2 contenedores, C3 componentes del backend). Los elementos con la etiqueta Planificado aún no están implementados: dependen de los issues #76 a #80, #85 y #86." {

    !identifiers hierarchical

    model {
        estudiante = person "Estudiante" "Desarrolla la práctica, reporta actividades, horas y evidencias PDF, y consulta su avance (HU-01, HU-02, HU-04)." "Actor"
        tutorAcademico = person "Tutor académico" "Docente que valida o devuelve planes, reportes e informes con observación (HU-03, Art. 336)." "Actor"
        tutorEntidad = person "Tutor de la entidad receptora" "Persona externa a la UNL en prácticas laborales; confirma reportes y registra su informe de sus practicantes (HU-07, Art. 337)." "Actor"
        coordinador = person "Coordinador de prácticas" "Docente responsable de prácticas de la carrera; consulta el estado, recibe alertas y cierra prácticas (HU-05, Art. 335)." "Actor"
        director = person "Director de carrera" "Actor secundario: consulta cierres e historial inalterable de su carrera (HU-09, Art. 340)." "Actor"
        secretaria = person "Secretaría" "Legaliza los anexos de cierre de la carrera (RF-04, HU-09)." "Actor"

        siaaf = softwareSystem "SIAAF" "Sistema académico institucional de la UNL. El sistema se concibe como un módulo suyo; la integración técnica está fuera del alcance (spec, RNF-11)." "Externo,FueraDeAlcance"

        sps = softwareSystem "Sistema de seguimiento de prácticas" "Da seguimiento y trazabilidad a una práctica ya asignada, desde el plan de actividades hasta el cierre, con horas validadas, alertas e historial inalterable." {

            web = container "Prototipo web (plantillas)" "Pantallas server-rendered del prototipo (/prototipo/), solo con DEBUG=True. Consumen la misma fachada que la API." "Plantillas Django" "Existente,Navegador"

            api = container "API backend" "Expone /api/v1/ y /health/. Hoy: vistas Django con JsonResponse y datos sintéticos (apps/prototipo, apps/health). Objetivo: Django REST Framework sobre modelos persistentes." "Python, Django 5.2" "Existente" {

                seguridadDjango = component "Seguridad de Django" "SecurityMiddleware, SessionMiddleware y CsrfViewMiddleware de backend/config/settings.py; protege las vistas de escritura salvo el PATCH marcado csrf_exempt." "Middleware de Django" "Existente"
                health = component "Health check" "Función health de apps/health/views.py: responde 200 con el JSON status ok. El chequeo de base y el 503 llegan con #86." "Vista Django" "Existente"
                apiDemo = component "API demo (api.py, api_urls.py)" "Decorador _demo (un método, X-Rol, 401/403/405) y las vistas lista_practicas, detalle_practica, lista_alertas, historial_practica, legalizar_anexo, cierre_practica, reportes_practica y decidir_pendiente. Errores con json_error." "Vistas Django" "Existente"
                pantallas = component "Vistas de pantallas (views*.py)" "Vistas de plantilla de estudiante, tutores, coordinador, director, secretaría y entidad; solo_en_debug devuelve 404 sin DEBUG." "Vistas Django" "Existente"
                fachada = component "Fachada de casos de uso (facade.py)" "practicas_de, practica_de_id, alertas_de, cerrar_practica, historial_de, legalizar_anexo y registrar_reporte; PracticeQueryError. Filtra por rol y carrera (RF-11)." "Módulo Python" "Existente"
                dto = component "DTO (dto.py)" "to_practica_dto, to_reporte_dto, to_alerta_dto, to_historial_dto y to_anexo_dto: forma exacta del contrato." "Módulo Python" "Existente"
                reglas = component "Reglas y validaciones" "validaciones.py (decidir, aplicar, límite de 500 caracteres), forms.py (ReporteSemanalForm, PDF de hasta 5 MB, ayudantía de hasta 10 h) y TRANSICIONES de coordinador.py." "Módulo Python" "Existente"
                estadoDemo = component "Estado de demo" "Sesión de Django (SESSION_KEY) y cookies firmadas con django.core.signing: prototipo_validaciones, prototipo_coordinador_v2 y prototipo_secretaria_v2." "Sesión y cookies firmadas" "Existente"
                sampleData = component "Datos sintéticos (sample_data.py)" "Catálogo de 150 prácticas propias y 40 externas en memoria. Transitorio: lo reemplaza la persistencia de #76." "Módulo Python" "Existente"

                drfVistas = component "Vistas DRF (APIView / ViewSet)" "[PLANIFICADO] Capa api/ de #76 y #78: endpoints de /api/v1/ que delegan en los casos de uso." "Django REST Framework" "Planificado"
                serializers = component "Serializers" "[PLANIFICADO] Validación de entrada y forma de salida (ReporteSerializer, PracticaSerializer) en lugar de los DTO manuales." "Django REST Framework" "Planificado"
                renderer = component "Renderer y exception handler del envelope" "[PLANIFICADO] Envuelve éxitos y errores en {success, message, data, errors, meta}; el 204 va sin cuerpo y el 500 sin trazas (#77)." "Django REST Framework" "Planificado"
                permisos = component "Autenticación y permisos" "[PLANIFICADO] Autenticación real (método por decidir en el ADR 0011) y permisos por rol y por objeto; reemplaza X-Rol (#79)." "Django REST Framework" "Planificado"
                openapi = component "Esquema OpenAPI" "[PLANIFICADO] Genera /api/v1/schema/ con requests, responses y errores (#77)." "drf-spectacular" "Planificado"
                casosDeUso = component "Casos de uso (application/)" "[PLANIFICADO] Evolución de la fachada: orquesta dominio y repositorios (#76)." "Módulo Python" "Planificado"
                dominio = component "Dominio (domain/)" "[PLANIFICADO] Reglas de negocio: Art. 341, regla del 70 % y tabla de transiciones de estado (#76)." "Módulo Python" "Planificado"
                repositorios = component "Modelos y repositorios (infrastructure/)" "[PLANIFICADO] Modelos Practica, Reporte y relacionados, migraciones y consultas filtradas por rol (#76)." "Django ORM" "Planificado"
                observabilidad = component "Middleware de observabilidad" "[PLANIFICADO] Asigna X-Request-ID a cada respuesta y lo escribe en los logs estructurados (#86)." "Middleware de Django" "Planificado"
            }

            swagger = container "Documentación OpenAPI (Swagger UI)" "[PLANIFICADO] Esquema OpenAPI en /api/v1/schema/ e interfaz Swagger en /api/v1/docs/ (#77)." "drf-spectacular" "Planificado"

            db = container "Base de datos PostgreSQL" "[PLANIFICADO] Prácticas, reportes, validaciones, usuarios e historial de estados. Hoy el código usa SQLite (backend/config/settings.py); PostgreSQL llega con #76 y ya existe en docker-compose.yml." "PostgreSQL 17" "Planificado,BaseDeDatos"

            evidencias = container "Almacén de evidencias" "[PLANIFICADO] Archivos PDF de hasta 5 MB, versionados por devolución (research Tema 5, RNF-05). Hoy no se almacenan: solo se registra el nombre." "FileField sobre sistema de archivos" "Planificado,BaseDeDatos"

            portal = container "Portal de documentación" "[PLANIFICADO] Sitio estático con la especificación, la matriz de trazabilidad, los diagramas C4 y los ADR (#85)." "Quarto, GitHub Pages" "Planificado,Navegador"
        }

        # Personas -> contenedores (los de C1 se derivan como relaciones implícitas)
        estudiante -> sps.web "Registra reportes y consulta horas y estado" "HTTPS"
        tutorAcademico -> sps.web "Valida o devuelve documentos de sus tutorados" "HTTPS"
        tutorEntidad -> sps.web "Confirma reportes y registra su informe" "HTTPS"
        coordinador -> sps.web "Consulta prácticas, recibe alertas y cierra" "HTTPS"
        director -> sps.web "Consulta cierres e historial" "HTTPS"
        secretaria -> sps.web "Legaliza anexos de cierre" "HTTPS"

        # Contenedores
        sps.web -> sps.api.pantallas "Renderiza pantallas" "Mismo proceso Django"
        sps.swagger -> sps.api.openapi "Sirve el esquema y la interfaz" "HTTP" "Planificado"
        sps.portal -> sps.api "Documenta contrato, arquitectura y trazabilidad" "" "Planificado"
        sps.api -> siaaf "Futura integración con identificadores institucionales (cédula, código de carrera)" "Fuera de alcance" "FueraDeAlcance"

        # Componentes existentes
        sps.api.seguridadDjango -> sps.api.apiDemo "Protege con CSRF y sesión"
        sps.api.seguridadDjango -> sps.api.pantallas "Protege con CSRF y sesión"
        sps.api.apiDemo -> sps.api.fachada "Delega los casos de uso"
        sps.api.apiDemo -> sps.api.reglas "Decide pendientes (validaciones.decidir)"
        sps.api.pantallas -> sps.api.fachada "Delega los casos de uso"
        sps.api.pantallas -> sps.api.reglas "Valida formularios"
        sps.api.fachada -> sps.api.dto "Arma los payloads"
        sps.api.fachada -> sps.api.reglas "Valida el reporte (ReporteSemanalForm)"
        sps.api.fachada -> sps.api.sampleData "Lee el catálogo en memoria"
        sps.api.fachada -> sps.api.estadoDemo "Aplica envíos, decisiones y cambios del cliente"
        sps.api.reglas -> sps.api.estadoDemo "Lee y firma las cookies"

        # Componentes planificados
        sps.api.drfVistas -> sps.api.serializers "Valida y serializa" "" "Planificado"
        sps.api.drfVistas -> sps.api.permisos "Autoriza cada petición" "" "Planificado"
        sps.api.drfVistas -> sps.api.casosDeUso "Delega los casos de uso" "" "Planificado"
        sps.api.drfVistas -> sps.api.renderer "Responde con el envelope" "" "Planificado"
        sps.api.casosDeUso -> sps.api.dominio "Aplica las reglas de negocio" "" "Planificado"
        sps.api.casosDeUso -> sps.api.repositorios "Lee y escribe el estado" "" "Planificado"
        sps.api.permisos -> sps.api.repositorios "Comprueba la pertenencia del objeto" "" "Planificado"
        sps.api.openapi -> sps.api.drfVistas "Describe los endpoints" "" "Planificado"
        sps.api.observabilidad -> sps.api.drfVistas "Etiqueta cada petición con X-Request-ID" "" "Planificado"
        sps.api.observabilidad -> sps.api.health "Etiqueta cada petición con X-Request-ID" "" "Planificado"
        sps.api.repositorios -> sps.db "Consultas y migraciones" "SQL / psycopg" "Planificado"
        sps.api.repositorios -> sps.evidencias "Guarda y lee PDF" "" "Planificado"
        sps.api.health -> sps.db "Comprueba la conexión (503 si falla)" "SQL" "Planificado"

        deploymentEnvironment "Docker Compose" {
            deploymentNode "Equipo de desarrollo o CI" "" "Docker Engine" {
                deploymentNode "Servicio api" "Imagen construida por el Dockerfile; el entrypoint aplica migrate y seed." "python:3.13-slim" {
                    apiInstancia = containerInstance sps.api
                    webInstancia = containerInstance sps.web
                }
                deploymentNode "Servicio db" "Volumen pgdata." "postgres:17-alpine" {
                    dbInstancia = containerInstance sps.db
                }
            }
        }
    }

    views {
        systemContext sps "C1-Contexto" "C1: actores y sistemas externos del sistema de seguimiento." {
            include *
            autolayout tb
        }

        container sps "C2-Contenedores" "C2: contenedores del sistema. Los trazos discontinuos son planificados." {
            include *
            autolayout lr
        }

        component sps.api "C3-Componentes-API" "C3: componentes del backend por capas. Los trazos discontinuos son planificados (#76 a #80 y #86)." {
            include *
            autolayout lr
        }

        deployment sps "Docker Compose" "D1-Despliegue" "Despliegue local y de CI con docker compose (#81)." {
            include *
            autolayout lr
        }

        styles {
            element "Element" {
                color #ffffff
            }
            element "Person" {
                shape person
                background #08427b
            }
            element "Software System" {
                background #1168bd
            }
            element "Container" {
                background #438dd5
            }
            element "Component" {
                background #2e6da4
            }
            element "Externo" {
                background #999999
            }
            element "Navegador" {
                shape webbrowser
            }
            element "BaseDeDatos" {
                shape cylinder
            }
            element "Planificado" {
                background #6b6b6b
                border dashed
                opacity 70
            }
            element "FueraDeAlcance" {
                border dotted
            }
            relationship "Relationship" {
                color #555555
                thickness 2
            }
            relationship "Planificado" {
                dashed true
            }
            relationship "FueraDeAlcance" {
                dashed true
            }
        }
    }
}
