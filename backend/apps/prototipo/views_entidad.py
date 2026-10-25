"""Entidad receptora y convenios (N1-N2) del prototipo: solo consulta.

Catálogo de entidades (lista y detalle solo lectura) y convenios/cartas de
compromiso. Las tres rutas son solo GET: ninguna pantalla edita ni firma, porque
los convenios son «fuera del MVP» (spec §4, proyecto R). Ver la decisión del
mapa en docs/mapa-pantallas.md §3.6.
"""
from django.http import HttpResponseNotFound
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from . import entidad as catalogo
from .views import solo_en_debug


def _contexto(entidad=None, **extra):
    contexto = {
        "usuario_nombre": catalogo.USUARIO,
        "entidad": entidad,
        "hoy": catalogo.HOY,
    }
    contexto.update(extra)
    return contexto


@solo_en_debug
@require_http_methods(["GET"])
def catalogo_entidades(request):
    """N1: entidades con su instrumento, su vigencia y sus prácticas vigentes."""
    entidades = [
        {
            "entidad": entidad,
            "practicas_vigentes": catalogo.practicas_vigentes_de_la_entidad(entidad["nombre"]),
        }
        for entidad in catalogo.entidades()
    ]
    return render(
        request,
        "practicas/catalogo_entidades.html",
        _contexto(entidades=entidades, total=len(entidades)),
    )


@solo_en_debug
@require_http_methods(["GET"])
def detalle_entidad(request, entidad_id):
    """N1 detalle (HU-07): la entidad y sus prácticas vigentes, solo lectura."""
    entidad = catalogo.get_entidad(entidad_id)
    if entidad is None:
        return HttpResponseNotFound()
    return render(
        request,
        "practicas/entidad_detalle.html",
        _contexto(
            entidad=entidad,
            practicas=catalogo.practicas_vigentes_de_la_entidad(entidad["nombre"]),
        ),
    )


@solo_en_debug
@require_http_methods(["GET"])
def convenios(request):
    """N2: convenios y cartas de compromiso, etiquetados fuera del MVP."""
    lista = catalogo.convenios()
    return render(
        request,
        "practicas/convenios.html",
        _contexto(convenios=lista, total=len(lista)),
    )
