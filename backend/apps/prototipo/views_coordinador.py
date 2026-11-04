import csv

from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from . import coordinador as demo
from . import facade
from . import sample_data as data
from .forms import CierreForm, ConfiguracionCarreraForm, EstadoPracticaForm
from .views import TABS, _con_query, contexto_demo, solo_en_debug


def _practica(request, practica_id):
    try:
        return facade.practica_para_pantalla(practica_id, "coordinador", **contexto_demo(request))
    except facade.PracticeQueryError as error:
        if error.status == 404:
            raise Http404 from error
        return None


@solo_en_debug
@demo.migrar_cookie
@require_http_methods(["GET"])
def practicas_carrera(request):
    practicas = facade.practicas_para_pantalla("coordinador", **contexto_demo(request))
    filtros = {key: request.GET.get(param, "") for key, param in
               (("periodo", "periodo"), ("tipo", "tipo"), ("estado", "estado"),
                ("alerta", "alerta"), ("busqueda", "q"))}
    return render(request, "practicas/practicas_carrera.html", {
        "usuario_nombre": data.COORDINADOR, "carrera": data.CARRERA_COORDINADOR,
        "practicas": data.filtrar_practicas(practicas, **filtros),
        "total_carrera": len(practicas), "filtros": filtros,
        "periodos": data.periodos_de(practicas),
        "opciones_tipo": [("", "Todos los tipos"), ("laboral", "Laboral"), ("comunitaria", "Comunitaria")],
        "opciones_estado": [("", "Todos los estados"), *data.ESTADO_PRACTICA.items()],
        "opciones_alerta": [("", "Todas las alertas"), *data.TIPOS_ALERTA.items()],
    })


@solo_en_debug
@demo.migrar_cookie
@require_http_methods(["GET"])
def alertas(request):
    tipo = request.GET.get("tipo", "")
    payload = facade.alertas_de("coordinador", tipo, **contexto_demo(request))
    return render(request, "practicas/alertas.html", {
        "usuario_nombre": data.COORDINADOR, "alertas": payload["alertas"], "tipo": tipo,
        "opciones_alerta": [("", "Todas las alertas"), *data.TIPOS_ALERTA.items()],
    })


@solo_en_debug
@demo.migrar_cookie
@require_http_methods(["GET"])
def practica_coordinador(request, practica_id):
    practica = _practica(request, practica_id)
    if practica is None:
        return HttpResponseForbidden()
    base = reverse("prototipo:practica_coordinador", args=[practica_id])
    tabs = (*TABS, ("historial", "Historial"))
    tab = request.GET.get("tab", "resumen")
    if tab not in dict(tabs):
        tab = "resumen"
    acciones = []
    for accion, (origenes, _, etiqueta) in demo.TRANSICIONES.items():
        if practica["estado"] in origenes:
            url = (reverse("prototipo:cerrar_practica", args=[practica_id]) if accion == "cerrar"
                   else reverse("prototipo:estado_practica", args=[practica_id, accion]))
            acciones.append({"url": url, "etiqueta": etiqueta})
    return render(request, "practicas/practica_detalle.html", {
        "usuario_nombre": data.COORDINADOR, "es_coordinador": True,
        "practica": practica, "acciones": acciones, "tab": tab,
        "tabs": [{"clave": key, "etiqueta": label, "url": _con_query(base, tab=key), "activa": tab == key}
                 for key, label in tabs],
    })


@solo_en_debug
@demo.migrar_cookie
@require_http_methods(["GET", "POST"])
def cerrar_practica(request, practica_id):
    return _decision(request, practica_id, "cerrar")


@solo_en_debug
@demo.migrar_cookie
@require_http_methods(["GET", "POST"])
def estado_practica(request, practica_id, accion):
    return _decision(request, practica_id, accion)


def _decision(request, practica_id, accion):
    estado = demo.leer_estado(request)
    practica = _practica(request, practica_id)
    if practica is None:
        return HttpResponseForbidden()
    if accion not in demo.TRANSICIONES:
        return HttpResponseBadRequest("Acción desconocida.")
    origenes, destino, titulo = demo.TRANSICIONES[accion]
    if practica["estado"] not in origenes:
        return HttpResponseBadRequest("La acción no está permitida en el estado actual.")
    requisitos = data.requisitos_cierre(practica) if accion == "cerrar" else []
    faltantes = [r["requisito"] for r in requisitos if not r["cumplido"]]
    form = (CierreForm(request.POST if request.method == "POST" else None) if accion == "cerrar"
            else EstadoPracticaForm(request.POST if request.method == "POST" else None, accion=accion))
    detalle_url = reverse("prototipo:practica_coordinador", args=[practica_id])
    if request.method == "POST":
        valido = form.is_valid()
        if faltantes:
            form.add_error(None, "No se puede cerrar: falta " + "; ".join(faltantes) + ".")
        elif valido:
            try:
                if accion == "cerrar":
                    _, estado = facade.cerrar_practica(practica_id, "coordinador", **contexto_demo(request))
                else:
                    demo.registrar_cambio(estado, practica, destino, form.cleaned_data["motivo"])
                return demo.guardar_estado(request, redirect(detalle_url + "?tab=historial"), estado)
            except facade.PracticeQueryError as error:
                form.add_error(None, str(error))
    return render(request, "practicas/decision_coordinador.html", {
        "usuario_nombre": data.COORDINADOR, "practica": practica,
        "form": form, "titulo": titulo, "requisitos": requisitos,
        "bloqueado": bool(faltantes), "detalle_url": detalle_url, "es_cierre": accion == "cerrar",
    })


@solo_en_debug
@demo.migrar_cookie
@require_http_methods(["GET", "POST"])
def configuracion_carrera(request):
    estado = demo.leer_estado(request)
    config = demo.configuracion(estado)
    form = ConfiguracionCarreraForm(request.POST if request.method == "POST" else None, initial=config)
    guardado = request.method == "POST" and form.is_valid()
    if guardado:
        estado["configuracion"] = form.cleaned_data
        try:
            demo.firmar_estado(estado)
        except facade.PracticeQueryError as error:
            form.add_error(None, str(error))
            guardado = False
    response = render(request, "practicas/configuracion_carrera.html", {
        "usuario_nombre": data.COORDINADOR, "carrera": data.CARRERA_COORDINADOR,
        "form": form, "guardado": guardado,
    })
    return demo.guardar_estado(request, response, estado) if guardado else response


@solo_en_debug
@demo.migrar_cookie
@require_http_methods(["GET"])
def consolidado_carrera(request):
    return _consolidado(request, general=False)


@solo_en_debug
@demo.migrar_cookie
@require_http_methods(["GET"])
def consolidado_general(request):
    return _consolidado(request, general=True)


def _consolidado(request, general):
    practicas = facade.practicas_para_pantalla("coordinador", **contexto_demo(request))
    if general:
        practicas += data.practicas_de_otras_carreras()
    periodo, componente = request.GET.get("periodo", ""), request.GET.get("componente", "")
    filas = data._filtrar_consolidado(
        [data._fila_consolidado(p) for p in practicas if p["estado"] == "cerrada"], periodo, componente)
    if request.GET.get("formato") == "csv":
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="consolidado-' + ("general" if general else "carrera") + '.csv"'
        writer = csv.writer(response)
        writer.writerow(["Estudiante", "Carrera", "Período", "Componente", "Horas validadas", "Horas requeridas", "Resultado", "Fecha de cierre"])
        for f in filas:
            writer.writerow([f["estudiante"], f["carrera"], f["periodo"], f["componente"],
                             f["horas_validadas"], f["horas_requeridas"], f["resultado_display"],
                             f["fecha_cierre"].isoformat()])
        return response
    return render(request, "practicas/consolidado.html", {
        "usuario_nombre": data.ANALISTA_DVS if general else data.COORDINADOR,
        "general": general, "titulo": "Consolidado general" if general else "Consolidado de la carrera",
        "filas": filas, "periodos": data.periodos_de(practicas), "periodo": periodo, "componente": componente,
        "csv_url": _con_query(request.path, periodo=periodo, componente=componente, formato="csv"),
    })


@solo_en_debug
@require_http_methods(["POST"])
def restablecer(request):
    response = redirect("prototipo:practicas_carrera")
    response.delete_cookie(demo.COOKIE, path="/")
    response.delete_cookie(demo.COOKIE_ANTERIOR, path="/prototipo/")
    return response
