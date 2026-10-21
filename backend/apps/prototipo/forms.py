import math

from django import forms

MAX_EVIDENCIA_BYTES = 5 * 1024 * 1024  # RNF-05
MAX_HORAS_AYUDANTIA = 10  # RF-15, Art. 341
NOTA_MINIMA_APROBACION = 70  # percent, RF-17, Art. 339


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """File field that accepts several files and reports every invalid one."""

    widget = MultipleFileInput

    def clean(self, data, initial=None):
        files = list(data) if isinstance(data, (list, tuple)) else [data]
        files = files or [None]
        cleaned, errors = [], []
        for file in files:
            try:
                cleaned.append(super().clean(file, initial))
            except forms.ValidationError as error:
                errors.extend(error.error_list)
        if errors:
            raise forms.ValidationError(errors)
        return cleaned


def _is_pdf(file):
    if not file.name.lower().endswith(".pdf"):
        return False
    head = file.read(5)
    file.seek(0)
    return head == b"%PDF-"


def _error_de_pdf(file):
    """The RNF-05 message for `file`, or None when it is a PDF of up to 5 MB."""
    if not _is_pdf(file):
        return f"«{file.name}»: solo se admiten archivos PDF."
    if file.size > MAX_EVIDENCIA_BYTES:
        megabytes = math.ceil(file.size / 1024 / 1024 * 10) / 10
        return (
            f"«{file.name}» pesa {megabytes} MB y supera el máximo "
            "de 5 MB por archivo."
        )
    return None


class ReporteSemanalForm(forms.Form):
    """Weekly report (E4, RF-02, RF-15)."""

    semana = forms.ChoiceField(
        label="Semana",
        choices=[],
        help_text="Elija la semana que va a reportar.",
    )
    actividades = forms.CharField(
        label="Actividades realizadas",
        widget=forms.Textarea(attrs={"rows": 6}),
        help_text="Describa lo que hizo esta semana, una actividad por línea.",
    )
    horas = forms.IntegerField(
        label="Horas",
        min_value=1,
        widget=forms.NumberInput(attrs={"min": 1, "inputmode": "numeric"}),
        error_messages={"min_value": "Ingrese al menos 1 hora."},
    )
    evidencias = MultipleFileField(
        label="Evidencias",
        help_text=(
            "Suba uno o varios archivos PDF que respalden sus actividades, "
            "de hasta 5 MB cada uno."
        ),
        error_messages={"required": "Adjunte al menos un archivo PDF."},
    )

    def __init__(self, *args, es_ayudantia=False, semanas=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.es_ayudantia = es_ayudantia
        self.fields["semana"].choices = [("", "-- Seleccione --"), *semanas]
        if es_ayudantia:
            self.fields["horas"].help_text = (
                f"Una ayudantía admite hasta {MAX_HORAS_AYUDANTIA} horas "
                "semanales (Art. 341)."
            )
        else:
            self.fields["horas"].help_text = "Ingrese las horas dedicadas esta semana."

    def clean_horas(self):
        horas = self.cleaned_data["horas"]
        if self.es_ayudantia and horas > MAX_HORAS_AYUDANTIA:
            raise forms.ValidationError(
                f"Una ayudantía no puede reportar más de {MAX_HORAS_AYUDANTIA} "
                "horas semanales (Art. 341 del Reglamento de Régimen Académico). "
                f"Ingresó {horas}."
            )
        return horas

    def clean_evidencias(self):
        errors = [
            error
            for error in map(_error_de_pdf, self.cleaned_data["evidencias"])
            if error
        ]
        if errors:
            raise forms.ValidationError(errors)
        return self.cleaned_data["evidencias"]


class RevisionForm(forms.Form):
    """Tutor decision on a plan, weekly report or final report (T2, RF-03)."""

    accion = forms.ChoiceField(
        label="Decisión",
        choices=[("validar", "Validar"), ("devolver", "Devolver")],
        error_messages={
            "required": "Elija «Validar» o «Devolver».",
            "invalid_choice": "Elija «Validar» o «Devolver».",
        },
    )
    observacion = forms.CharField(
        label="Observación",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text=(
            "Obligatoria para devolver: indique qué debe corregir el estudiante."
        ),
    )

    def clean(self):
        cleaned = super().clean()
        observacion = cleaned.get("observacion", "").strip()
        if cleaned.get("accion") == "devolver" and not observacion:
            self.add_error(
                "observacion",
                "Escriba una observación para devolver: el estudiante necesita "
                "saber qué corregir.",
            )
        cleaned["observacion"] = observacion
        return cleaned


def resultado_evaluacion(porcentaje):
    """(clave, etiqueta) of the result: «aprobada» from 70 % (RF-17, Art. 339)."""
    if porcentaje >= NOTA_MINIMA_APROBACION:
        return "aprobada", "Aprobada"
    return "no_aprobada", "No aprobada"


class EvaluacionFinalForm(forms.Form):
    """Final evaluation of a práctica (T5, HU-11, RF-17)."""

    porcentaje = forms.DecimalField(
        label="Desempeño",
        min_value=0,
        max_value=100,
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"min": 0, "max": 100, "step": "0.01"}),
        help_text=(
            "Porcentaje de 0 a 100. La práctica queda «aprobada» desde "
            f"{NOTA_MINIMA_APROBACION} % y «no aprobada» por debajo (Art. 339)."
        ),
        error_messages={
            "min_value": "Ingrese un porcentaje entre 0 y 100.",
            "max_value": "Ingrese un porcentaje entre 0 y 100.",
        },
    )

    def __init__(self, *args, faltantes=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.faltantes = list(faltantes)

    def clean(self):
        if self.faltantes:
            raise forms.ValidationError(
                "No se puede registrar la evaluación final: falta "
                f"{' y '.join(self.faltantes)}."
            )
        return super().clean()


class InformeExternoForm(forms.Form):
    """Final report of the entity tutor (R4, HU-07 case 1, RF-08)."""

    valoracion = forms.CharField(
        label="Valoración del desempeño",
        widget=forms.Textarea(attrs={"rows": 6}),
        help_text="Describa cómo cumplió el practicante las actividades del plan.",
    )
    archivo = forms.FileField(
        label="Informe firmado",
        help_text="Suba el informe firmado en PDF, de hasta 5 MB.",
        error_messages={"required": "Adjunte el informe firmado en PDF."},
    )

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]
        error = _error_de_pdf(archivo)
        if error:
            raise forms.ValidationError(error)
        return archivo


class IncumplimientoForm(forms.Form):
    """Breach reported by the entity tutor to the academic tutor (R5, RF-18)."""

    descripcion = forms.CharField(
        label="Descripción",
        widget=forms.Textarea(attrs={"rows": 6}),
        help_text=(
            "Describa qué incumplió el practicante y desde cuándo. "
            "Se avisará a su tutor académico."
        ),
        error_messages={"required": "Describa el incumplimiento."},
    )
