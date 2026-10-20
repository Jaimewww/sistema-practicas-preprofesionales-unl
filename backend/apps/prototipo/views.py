from functools import wraps
from urllib.parse import urlencode

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.datastructures import MultiValueDict
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import ReporteSemanalForm
from .sample_data import USUARIO, get_practica

TABS = (
    ("resumen", "Resumen"),
    ("plan", "Plan"),
    ("reportes", "Reportes semanales"),
    ("informe", "Informe final"),
)


def solo_en_debug(view):
    """The prototype never opens a public route (RNF-01): 404 unless DEBUG."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not settings.DEBUG:
            raise Http404
        return view(request, *args, **kwargs)

    return wrapper


def _practica_param(request):
    return "comunitaria" if request.GET.get("practica") == "comunitaria" else None


def _url_con_query(name, **params):
    params = {k: v for k, v in params.items() if v}
    url = reverse(name)
    return f"{url}?{urlencode(params)}" if params else url


@solo_en_debug
def mi_practica(request):
    clave = _practica_param(request)
    practica = get_practica(clave)
    tab = request.GET.get("tab")
    if tab not in dict(TABS):
        tab = "resumen"
    tabs = [
        {
            "clave": key,
            "etiqueta": label,
            "url": _url_con_query(
                "prototipo:mi_practica", tab=key if key != "resumen" else None, practica=clave
            ),
            "activa": key == tab,
        }
        for key, label in TABS
    ]
    next_url = _url_con_query("prototipo:mi_practica", tab="reportes", practica=clave)
    context = {
        "usuario_nombre": USUARIO["nombre"],
        "practica": practica,
        "tab": tab,
        "tabs": tabs,
        "reportar_url": _url_con_query(
            "prototipo:reporte_semanal_nuevo", practica=clave, next=next_url
        ),
    }
    return render(request, "practicas/mi_practica.html", context)


def _errores_de_ejemplo():
    """Bound data that triggers the three E4 error states of S6."""
    pdf_pesado = SimpleUploadedFile(
        "informe-completo.pdf", b"%PDF-1.4\n", content_type="application/pdf"
    )
    pdf_pesado.size = 6 * 1024 * 1024 + 300 * 1024  # not allocated, just reported
    foto = SimpleUploadedFile("foto-taller.png", b"\x89PNG\r\n", content_type="image/png")
    return (
        {
            "semana": "9",
            "actividades": "Calificación de talleres y tutorías de refuerzo.",
            "horas": "12",
        },
        MultiValueDict({"evidencias": [foto, pdf_pesado]}),
    )


@solo_en_debug
def reporte_semanal_nuevo(request):
    clave = _practica_param(request)
    practica = get_practica(clave)
    next_url = request.GET.get("next", "")
    if not url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        next_url = _url_con_query("prototipo:mi_practica", practica=clave)
    kwargs = {
        "es_ayudantia": practica["es_ayudantia"],
        "semanas": practica["semanas_para_reportar"],
    }
    if request.method == "POST":
        form = ReporteSemanalForm(request.POST, request.FILES, **kwargs)
        # Prototype: a valid report is not stored, it only returns to E2.
        if form.is_valid():
            return HttpResponseRedirect(next_url)
    elif request.GET.get("errores"):
        data, files = _errores_de_ejemplo()
        form = ReporteSemanalForm(data, files, **kwargs)
        form.is_valid()
    else:
        form = ReporteSemanalForm(**kwargs)
    context = {
        "usuario_nombre": USUARIO["nombre"],
        "practica": practica,
        "form": form,
        "cancelar_url": next_url,
        "mi_practica_url": _url_con_query("prototipo:mi_practica", practica=clave),
    }
    return render(request, "actividades/reporte_semanal_form.html", context)
