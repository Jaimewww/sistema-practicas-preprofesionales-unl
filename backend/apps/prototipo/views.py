import copy
import json
from functools import wraps
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.datastructures import MultiValueDict
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST

from . import facade
from .forms import (
    EvaluacionFinalForm,
    IncumplimientoForm,
    InformeExternoForm,
    RevisionForm,
    resultado_evaluacion,
)
from .sample_data import (
    HOY,
    PLAZO_REVISION_DIAS,
    TUTOR_ACADEMICO,
    TUTOR_ENTIDAD,
    USUARIO,
    get_pendiente,
    get_practica_de_la_entidad,
    get_practica_del_tutor,
    get_reporte_de_practicante,
    pendientes_de_revision,
    practicas_de_la_entidad,
    practicas_del_tutor,
    reportes_por_confirmar,
    requisitos_evaluacion,
)
from . import validaciones

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


@solo_en_debug
def indice(request):
    rol = request.GET.get("rol", "estudiante")
    if rol not in facade.ROLES:
        rol = "estudiante"
    return render(request, "practicas/indice.html", {
        "usuario_nombre": "Demostración API", "rol": rol, "roles": facade.ROLES,
        "practicas": facade.practicas_de(rol, envios_de_sesion(request)),
    })


def _practica_param(request):
    return "comunitaria" if request.GET.get("practica") == "comunitaria" else None


def _con_query(url, **params):
    params = {k: v for k, v in params.items() if v}
    return f"{url}?{urlencode(params)}" if params else url


def _url_con_query(name, **params):
    return _con_query(reverse(name), **params)


def envios_de_sesion(request):
    """Reports this browser sent; the demo keeps them only in its session."""
    return request.session.get(facade.SESSION_KEY, {})


@solo_en_debug
def mi_practica(request):
    clave = _practica_param(request)
    practica = facade.practica_del_estudiante(clave, envios_de_sesion(request))
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
        "demo_con_envios": bool(envios_de_sesion(request)),
    }
    return render(request, "practicas/mi_practica.html", context)


@solo_en_debug
@require_POST
def reiniciar_demo(request):
    """Forget the reports this session sent and go back to the sample data."""
    request.session.pop(facade.SESSION_KEY, None)
    return HttpResponseRedirect(reverse("prototipo:mi_practica"))


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
    practica = facade.practica_del_estudiante(clave, envios_de_sesion(request))
    next_url = request.GET.get("next", "")
    if not url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        next_url = _url_con_query("prototipo:mi_practica", practica=clave)
    if request.method == "POST":
        # Same use case as POST /api/v1/practicas/<id>/reportes/.
        try:
            reporte, envios = facade.registrar_reporte(
                practica["id"], "estudiante", request.POST, request.FILES, envios_de_sesion(request)
            )
        except facade.PracticeQueryError as error:
            form = error.form
            if form is None:  # a rule about the practice, not a field
                form = facade.formulario_reporte(practica, request.POST, request.FILES)
                form.is_valid()
                form.add_error(None, str(error))
        else:
            request.session[facade.SESSION_KEY] = envios
            messages.success(
                request, f"Reporte de la semana {reporte['semana']} enviado a revisión."
            )
            return HttpResponseRedirect(next_url)
    elif request.GET.get("errores"):
        data, files = _errores_de_ejemplo()
        form = facade.formulario_reporte(practica, data, files)
        form.is_valid()
    else:
        form = facade.formulario_reporte(practica)
    context = {
        "usuario_nombre": USUARIO["nombre"],
        "practica": practica,
        "form": form,
        "cancelar_url": next_url,
        "mi_practica_url": _url_con_query("prototipo:mi_practica", practica=clave),
    }
    return render(request, "actividades/reporte_semanal_form.html", context)


# Tutors (T1-T5, R1-R5). No database: an action re-renders the screen with the
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
        "pendientes": [] if _vacio(request) else _sin_decidir(request, pendientes_de_revision()),
        "plazo_revision": PLAZO_REVISION_DIAS,
    }
    return render(request, "actividades/pendientes_revision.html", context)


def _sin_decidir(request, pendientes):
    """T1 hides what the overlay (API or T2) already decided."""
    decididas = validaciones.leer_estado(request).get("decisiones", {})
    return [p for p in pendientes if p["clave"] not in decididas]


def _json_de_error(request, error):
    """The same nested body the API answers, shown under the T2 form."""
    from .api import error_de_escritura

    return validaciones.a_json(json.loads(error_de_escritura(request, error).content))


@solo_en_debug
@solo_get_y_post
def revisar(request, clave):
    pendiente = get_pendiente(clave)
    if pendiente is None:
        raise Http404
    estado = validaciones.leer_estado(request)
    validaciones.aplicar(pendiente, estado)
    decidido, resultado, nuevo = False, None, None
    if request.method == "POST":
        form = RevisionForm(request.POST)
        if form.is_valid():
            devolver = form.cleaned_data["accion"] == "devolver"
            datos = {
                "decision": "devuelto" if devolver else "aprobado",
                "observacion": form.cleaned_data["observacion"],
            }
            nuevo = copy.deepcopy(estado)
            try:
                decidida = validaciones.decidir(clave, nuevo, datos)
            except facade.PracticeQueryError as error:
                resultado = _json_de_error(request, error)
            else:
                pendiente, decidido = decidida, True
                resultado = validaciones.a_json(validaciones.to_pendiente_dto(pendiente))
    elif request.GET.get("errores"):
        form = RevisionForm({"accion": "devolver", "observacion": ""})
        form.is_valid()
    else:
        form = RevisionForm()

    def pantalla(pendiente, decidido, resultado):
        return render(request, "actividades/revisar.html", {
            "usuario_nombre": TUTOR_ACADEMICO,
            "pendiente": pendiente,
            "documento": pendiente["documento"],
            "practica": pendiente["practica"],
            "form": form,
            "decidido": decidido,
            "resultado": resultado,
            "resultado_error": resultado is not None and not decidido,
        })

    response = pantalla(pendiente, decidido, resultado)
    if decidido and not validaciones.guardar_estado(request, response, nuevo):
        # The cookie is full: keep the screen as it was and show the API's own 500.
        error = facade.PracticeQueryError(500, "error_interno", "La demostración alcanzó su límite.")
        original = validaciones.aplicar(get_pendiente(clave), estado)
        response = pantalla(original, False, _json_de_error(request, error))
    return response


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


@solo_en_debug
@require_http_methods(["GET"])
def mis_practicantes(request):
    context = {
        "usuario_nombre": TUTOR_ENTIDAD,
        "practicas": [] if _vacio(request) else practicas_de_la_entidad(),
    }
    return render(request, "practicas/mis_practicantes.html", context)


@solo_en_debug
@require_http_methods(["GET"])
def reportes_por_confirmar_lista(request):
    context = {
        "usuario_nombre": TUTOR_ENTIDAD,
        "pendientes": [] if _vacio(request) else reportes_por_confirmar(),
    }
    return render(request, "actividades/reportes_por_confirmar.html", context)


@solo_en_debug
@solo_get_y_post
def confirmar_reporte(request, practica_id, semana):
    encontrado = get_reporte_de_practicante(practica_id, semana)
    if encontrado is None:
        raise Http404
    practica, reporte = encontrado
    confirmado_ahora = False
    if request.method == "POST" and not reporte["confirmado_por_entidad"]:
        # HU-07 case 2: who confirmed and when.
        reporte.update(
            confirmado_por_entidad=True, confirmado_por=TUTOR_ENTIDAD, confirmado_el=HOY
        )
        confirmado_ahora = True
    context = {
        "usuario_nombre": TUTOR_ENTIDAD,
        "practica": practica,
        "reporte": reporte,
        "confirmado_ahora": confirmado_ahora,
    }
    return render(request, "actividades/confirmar_reporte.html", context)


def _practica_de_la_entidad_o_404(practica_id):
    practica = get_practica_de_la_entidad(practica_id)
    if practica is None:
        raise Http404
    return practica


@solo_en_debug
@solo_get_y_post
def informe_externo(request, practica_id):
    practica = _practica_de_la_entidad_o_404(practica_id)
    registrado = None
    if request.method == "POST":
        form = InformeExternoForm(request.POST, request.FILES)
        if form.is_valid():
            registrado = {
                "registrado_por": TUTOR_ENTIDAD,
                "registrado_el": HOY,
                "archivo": form.cleaned_data["archivo"].name,
            }
    else:
        form = InformeExternoForm()
    context = {
        "usuario_nombre": TUTOR_ENTIDAD,
        "practica": practica,
        "form": form,
        "registrado": registrado,
        "practicantes_url": reverse("prototipo:mis_practicantes"),
    }
    return render(request, "practicas/informe_externo_form.html", context)


@solo_en_debug
@solo_get_y_post
def reportar_incumplimiento(request, practica_id):
    practica = _practica_de_la_entidad_o_404(practica_id)
    reportado = None
    if request.method == "POST":
        form = IncumplimientoForm(request.POST)
        if form.is_valid():
            # RF-18: the alert goes to the academic tutor of this práctica.
            reportado = {
                "reportado_por": TUTOR_ENTIDAD,
                "reportado_el": HOY,
                "avisado_a": practica["tutor_academico"],
            }
    else:
        form = IncumplimientoForm()
    context = {
        "usuario_nombre": TUTOR_ENTIDAD,
        "practica": practica,
        "form": form,
        "reportado": reportado,
        "practicantes_url": reverse("prototipo:mis_practicantes"),
    }
    return render(request, "practicas/incumplimiento_form.html", context)
