import math

from django import forms

MAX_EVIDENCIA_BYTES = 5 * 1024 * 1024  # RNF-05
MAX_HORAS_AYUDANTIA = 10  # RF-15, Art. 341


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

