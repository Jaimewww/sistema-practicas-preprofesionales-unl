"""Director (D1-D2) and Secretary (S1-S2) prototype views.

Both roles belong to the same career as the coordinator (RF-11). The director
reads the closed practices and the history of his career; the secretary legalizes
annexes with the signed demo state shared by the screens and the API (#62).
"""
from copy import deepcopy

from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from . import facade
from . import sample_data as data
from . import secretaria as demo
from .views import TABS, _con_query, contexto_demo, solo_en_debug


@solo_en_debug
@require_http_methods(["GET"])
def cierres_director(request):
    cerradas = facade.practicas_para_director(**contexto_demo(request))
    practicas = cerradas
    filtros = {
        "periodo": request.GET.get("periodo", ""),
        "tipo": request.GET.get("tipo", ""),
        "resultado": request.GET.get("resultado", ""),
        "busqueda": request.GET.get("q", ""),
    }
    if filtros["periodo"]:
        practicas = [p for p in practicas if p["periodo"] == filtros["periodo"]]
    if filtros["tipo"]:
        practicas = [p for p in practicas if p["tipo"] == filtros["tipo"]]
    if filtros["resultado"]:
        practicas = [p for p in practicas if p.get("resultado") == filtros["resultado"]]
    if filtros["busqueda"]:
        texto = filtros["busqueda"].strip().upper()
        practicas = [p for p in practicas if texto in p["estudiante"].upper()]
    return render(request, "practicas/director_cierres.html", {
        "usuario_nombre": data.DIRECTOR,
        "carrera": data.CARRERA_COORDINADOR,
        "practicas": practicas,
        "total": len(practicas),
        "filtros": filtros,
        "periodos": sorted({p["periodo"] for p in cerradas}, reverse=True),
    })


@solo_en_debug
@require_http_methods(["GET"])
def practica_director(request, practica_id):
    estado = contexto_demo(request)
    try:
        practica = facade.practica_para_director(practica_id, **estado)
        historial = facade.historial_de(practica_id, "director", **estado)
    except facade.PracticeQueryError:
        return HttpResponseNotFound()
    base = reverse("prototipo:practica_director", args=[practica_id])
    tabs = (*TABS, ("anexos", "Anexos"), ("historial", "Historial"), ("resultado", "Resultado"))
    tab = request.GET.get("tab", "resumen")
    if tab not in dict(tabs):
        tab = "resumen"
    return render(request, "practicas/director_practica.html", {
        "usuario_nombre": data.DIRECTOR,
        "practica": practica,
        "historial": historial,
        "tab": tab,
        "tabs": [
            {"clave": key, "etiqueta": label, "url": _con_query(base, tab=key if key != "resumen" else None), "activa": tab == key}
            for key, label in tabs
        ],
    })


def _practicas_con_legalizaciones(request):
    estado = demo.leer_estado(request)
    return demo.aplicar_legalizaciones(deepcopy(data.practicas_de_la_carrera()), estado)


@solo_en_debug
@demo.migrar_cookie
@require_http_methods(["GET"])
def anexos_secretaria(request):
    practicas = _practicas_con_legalizaciones(request)
    tipo = request.GET.get("tipo", "")
    items = [
        {"anexo": a, "practica": p}
        for p in practicas
        for a in p.get("anexos", [])
        if a["estado"] == "pendiente" and (not tipo or p["tipo"] == tipo)
    ]
    return render(request, "practicas/secretaria_anexos.html", {
        "usuario_nombre": data.SECRETARIA,
        "carrera": data.CARRERA_COORDINADOR,
        "items": items,
        "tipo": tipo,
    })


@solo_en_debug
@demo.migrar_cookie
@require_http_methods(["GET", "POST"])
def legalizar_anexo(request, anexo_id):
    if request.method == "POST":
        return _legalizar(request, anexo_id)
    return _formulario(request, anexo_id, 200)


def _legalizar(request, anexo_id):
    """S2 uses the same use case as POST /prototipo/api/v1/anexos/<id>/legalizacion/."""
    try:
        _, estado = facade.legalizar_anexo(anexo_id, "secretaria", demo.leer_estado(request))
    except facade.PracticeQueryError as error:
        if error.status == 404:
            return HttpResponseNotFound()
        if error.status == 409:  # ya legalizado: muestra el conflicto con su mensaje
            return _formulario(request, anexo_id, 409)
        return HttpResponseForbidden(str(error))
    try:
        return demo.guardar_estado(request, redirect("prototipo:anexos_secretaria"), estado)
    except facade.PracticeQueryError as error:
        return HttpResponseForbidden(str(error))


def _formulario(request, anexo_id, status):
    anexo, practica = _anexo_y_practica(request, anexo_id)
    if anexo is None or practica is None:
        return HttpResponseNotFound()
    return render(request, "practicas/secretaria_legalizar.html", {
        "usuario_nombre": data.SECRETARIA,
        "anexo": anexo,
        "practica": practica,
        "ya_legalizado": anexo["estado"] == "legalizado",
    }, status=status)


def _anexo_y_practica(request, anexo_id):
    for practica in _practicas_con_legalizaciones(request):
        for anexo in practica.get("anexos", []):
            if anexo["id"] == anexo_id:
                return anexo, practica
    return None, None
