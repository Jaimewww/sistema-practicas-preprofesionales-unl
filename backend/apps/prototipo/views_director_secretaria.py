"""Director (D1-D2) and Secretary (S1-S2) prototype views.

Both roles belong to the same career as the coordinator (RF-11). The secretary
uses a signed cookie to persist legalizations across reloads.
"""
from copy import deepcopy

from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from . import sample_data as data
from . import secretaria as demo
from .views import TABS, _con_query, solo_en_debug


@solo_en_debug
@require_http_methods(["GET"])
def cierres_director(request):
    practicas = data.practicas_cerradas_de_la_carrera()
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
        "periodos": sorted({p["periodo"] for p in data.practicas_cerradas_de_la_carrera()}, reverse=True),
    })


@solo_en_debug
@require_http_methods(["GET"])
def practica_director(request, practica_id):
    practica = data.get_practica_cerrada_de_la_carrera(practica_id)
    if practica is None:
        return HttpResponseNotFound()
    base = reverse("prototipo:practica_director", args=[practica_id])
    tabs = (*TABS, ("anexos", "Anexos"), ("resultado", "Resultado"))
    tab = request.GET.get("tab", "resumen")
    if tab not in dict(tabs):
        tab = "resumen"
    return render(request, "practicas/director_practica.html", {
        "usuario_nombre": data.DIRECTOR,
        "practica": practica,
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
@require_http_methods(["GET", "POST"])
def legalizar_anexo(request, anexo_id):
    estado = demo.leer_estado(request)
    practicas = _practicas_con_legalizaciones(request)
    anexo = next((a for p in practicas for a in p.get("anexos", []) if a["id"] == anexo_id), None)
    practica = next((p for p in practicas if any(a["id"] == anexo_id for a in p.get("anexos", []))), None)
    if anexo is None:
        return HttpResponseNotFound()
    ya_legalizado = anexo["estado"] == "legalizado"
    if request.method == "POST" and not ya_legalizado:
        demo.legalizar_anexo(estado, anexo_id, data.SECRETARIA)
        response = redirect("prototipo:anexos_secretaria")
        return demo.guardar_estado(request, response, estado)
    return render(request, "practicas/secretaria_legalizar.html", {
        "usuario_nombre": data.SECRETARIA,
        "anexo": anexo,
        "practica": practica,
        "ya_legalizado": ya_legalizado,
    })
