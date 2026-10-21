from functools import wraps
from urllib.parse import urlencode

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.datastructures import MultiValueDict
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from .forms import (
    EvaluacionFinalForm,
    ReporteSemanalForm,
    RevisionForm,
    resultado_evaluacion,
)
from .sample_data import (
    ESTADO_REPORTE,
    HOY,
    PLAZO_REVISION_DIAS,
    TUTOR_ACADEMICO,
    USUARIO,
    get_pendiente,
    get_practica,
    get_practica_del_tutor,
    pendientes_de_revision,
    practicas_del_tutor,
    requisitos_evaluacion,
)

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


def _con_query(url, **params):
    params = {k: v for k, v in params.items() if v}
    return f"{url}?{urlencode(params)}" if params else url


def _url_con_query(name, **params):
    return _con_query(reverse(name), **params)


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


# Tutors (T1-T5). No database: an action re-renders the screen with the
# new state, its author and HOY as the date. Nothing is ever deleted (RF-10),
# so these views only answer GET and POST.

solo_get_y_post = require_http_methods(["GET", "POST"])


def _vacio(request):
    """`?vacio=1` shows a list's empty state (map, section 4)."""
    return bool(request.GET.get("vacio"))


@solo_en_debug
@require_http_methods(["GET"])
def pendientes_revision(request):
    context = {
        "usuario_nombre": TUTOR_ACADEMICO,
        "pendientes": [] if _vacio(request) else pendientes_de_revision(),
        "plazo_revision": PLAZO_REVISION_DIAS,
    }
    return render(request, "actividades/pendientes_revision.html", context)


def _decidir(pendiente, form):
    """Apply the T2 decision to the sample item, recording who and when (RF-04)."""
    devolver = form.cleaned_data["accion"] == "devolver"
    estado = "devuelto" if devolver else "validado"
    pendiente["documento"].update(
        estado=estado,
        estado_display=ESTADO_REPORTE[estado],
        validado_por=TUTOR_ACADEMICO,
        validado_el=HOY,
        observacion=form.cleaned_data["observacion"] if devolver else "",
    )
    pendiente.update(estado=estado, estado_display=ESTADO_REPORTE[estado])


@solo_en_debug
@solo_get_y_post
def revisar(request, clave):
    pendiente = get_pendiente(clave)
    if pendiente is None:
        raise Http404
    decidido = False
    if request.method == "POST":
        form = RevisionForm(request.POST)
        if form.is_valid():
            _decidir(pendiente, form)
            decidido = True
    elif request.GET.get("errores"):
        form = RevisionForm({"accion": "devolver", "observacion": ""})
        form.is_valid()
    else:
        form = RevisionForm()
    context = {
        "usuario_nombre": TUTOR_ACADEMICO,
        "pendiente": pendiente,
        "documento": pendiente["documento"],
        "practica": pendiente["practica"],
        "form": form,
        "decidido": decidido,
    }
    return render(request, "actividades/revisar.html", context)


@solo_en_debug
@require_http_methods(["GET"])
def mis_tutorados(request):
    context = {
        "usuario_nombre": TUTOR_ACADEMICO,
        "practicas": [] if _vacio(request) else practicas_del_tutor(),
    }
    return render(request, "practicas/mis_tutorados.html", context)


def _practica_del_tutor_o_404(practica_id):
    practica = get_practica_del_tutor(practica_id)
    if practica is None:
        raise Http404
    return practica


@solo_en_debug
@require_http_methods(["GET"])
def practica_tutor(request, practica_id):
    practica = _practica_del_tutor_o_404(practica_id)
    base_url = reverse("prototipo:practica_tutor", args=[practica_id])
    tab = request.GET.get("tab")
    if tab not in dict(TABS):
        tab = "resumen"
    tabs = [
        {
            "clave": key,
            "etiqueta": label,
            "url": _con_query(base_url, tab=key if key != "resumen" else None),
            "activa": key == tab,
        }
        for key, label in TABS
    ]
    # T2 links for whatever of this práctica is in review.
    revisar_urls = {
        p["clave"]: reverse("prototipo:revisar", args=[p["clave"]])
        for p in pendientes_de_revision()
        if p["practica"]["id"] == practica_id
    }
    for reporte in practica["reportes"]:
        reporte["revisar_url"] = revisar_urls.get(f"reporte-{practica_id}-{reporte['semana']}")
    context = {
        "usuario_nombre": TUTOR_ACADEMICO,
        "practica": practica,
        "tab": tab,
        "tabs": tabs,
        "plan_revisar_url": revisar_urls.get(f"plan-{practica_id}"),
        "informe_revisar_url": revisar_urls.get(f"informe-{practica_id}"),
        "evaluacion_url": reverse("prototipo:evaluacion_final", args=[practica_id]),
    }
    return render(request, "practicas/practica_detalle.html", context)


@solo_en_debug
@solo_get_y_post
def evaluacion_final(request, practica_id):
    practica = _practica_del_tutor_o_404(practica_id)
    faltantes = requisitos_evaluacion(practica)
    evaluacion = None
    if request.method == "POST":
        form = EvaluacionFinalForm(request.POST, faltantes=faltantes)
        if form.is_valid():
            porcentaje = form.cleaned_data["porcentaje"]
            resultado, resultado_display = resultado_evaluacion(porcentaje)
            evaluacion = {
                "porcentaje": porcentaje,
                "resultado": resultado,
                "resultado_display": resultado_display,
                "registrado_por": TUTOR_ACADEMICO,
                "registrado_el": HOY,
            }
    else:
        form = EvaluacionFinalForm(faltantes=faltantes)
    context = {
        "usuario_nombre": TUTOR_ACADEMICO,
        "practica": practica,
        "form": form,
        "faltantes": faltantes,
        "evaluacion": evaluacion,
        "practica_url": reverse("prototipo:practica_tutor", args=[practica_id]),
    }
    return render(request, "practicas/evaluacion_final_form.html", context)

