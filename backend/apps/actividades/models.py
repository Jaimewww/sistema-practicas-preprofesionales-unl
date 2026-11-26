"""Modelos de actividades: el plan de actividades y su validación (T022, T023).

``PlanActividades`` es la entidad de HU-01/RF-01: la práctica, la versión del
plan, el contenido que el estudiante se compromete a cumplir y su estado.
``Validacion`` es la decisión del tutor académico sobre un plan o un reporte
semanal (RF-03, RF-04), con la regla del data-model «exactamente uno de los dos».
``ConfirmacionEntidad`` e ``InformeFinal`` son las dos escrituras de HU-07/RF-08:
el tutor de entidad confirma el reporte semanal de su practicante y registra su
informe final (S5). Las transiciones (enviar, devolver, aprobar) son T024 y
viven en ``apps/actividades/services.py``; aquí solo están las entidades y sus
reglas.
"""

from pathlib import Path
from typing import TYPE_CHECKING, ClassVar
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.practicas.models import MENSAJE_TUTOR_ENTIDAD_ROL
from apps.usuarios.models import Usuario

if TYPE_CHECKING:
    # ``Any`` y ``RelatedManager`` solo los necesita el analizador estático para
    # los accesos inversos de ``PlanActividades``.
    from typing import Any

    from django.db.models.fields.related_descriptors import RelatedManager

MENSAJE_VERSION = "La versión del plan debe ser un número entero positivo."
MENSAJE_DECISION = "La decisión debe ser «aprobado» o «devuelto»."
MENSAJE_OBSERVACION = "La observación es obligatoria cuando la decisión es «devuelto»."
MENSAJE_EXACTAMENTE_UNO = (
    "La validación debe referirse exactamente a un plan, a un reporte semanal o al "
    "informe final del estudiante, nunca a más de uno ni a ninguno."
)
MENSAJE_INFORME_ESTUDIANTE_VERSION = (
    "Esa versión del informe final del estudiante ya existe para esta práctica."
)
MENSAJE_CONFIRMACION_UNICA = (
    "Ese reporte ya tiene la confirmación de la entidad: no se confirma dos veces."
)
MENSAJE_INFORME_UNO = (
    "El informe final debe traer su contenido o un archivo PDF, nunca los dos ni "
    "ninguno."
)
MAX_INFORME_BYTES = 5 * 1024 * 1024  # ADR 0005 / RNF-05: 5 MB por archivo.
MENSAJE_ARCHIVO_PDF = "«{nombre}»: solo se admiten archivos PDF."
MENSAJE_ARCHIVO_TAMANO = "«{nombre}» supera el máximo de 5 MB por archivo."


def validar_archivo_informe(archivo):
    """ADR 0005: el archivo del informe final es un PDF de hasta 5 MB.

    Replica la regla que ya aplica el prototipo (``_is_pdf`` y
    ``MAX_EVIDENCIA_BYTES`` en ``apps/prototipo/forms.py``): extensión ``.pdf``,
    firma ``%PDF-`` en los primeros cinco bytes y tope de 5 MB. Se valida el
    contenido además del nombre porque el cliente controla los dos. El archivo
    se rebobina antes y después de leer la firma para que Django guarde el PDF
    completo y no los bytes que quedaron después de la cabecera.

    Es un validador de campo, no ``clean()``: ``full_clean()`` lo ejecuta en
    ``clean_fields()``, antes de las reglas de la entidad, y un archivo vacío no
    lo ejecuta (el campo es opcional).
    """
    nombre = str(getattr(archivo, "name", "") or "")
    if not nombre.lower().endswith(".pdf"):
        raise ValidationError(
            MENSAJE_ARCHIVO_PDF.format(nombre=nombre), code="formato_invalido"
        )
    archivo.seek(0)
    cabecera = archivo.read(5)
    archivo.seek(0)
    if cabecera != b"%PDF-":
        raise ValidationError(
            MENSAJE_ARCHIVO_PDF.format(nombre=nombre), code="formato_invalido"
        )
    if getattr(archivo, "size", 0) > MAX_INFORME_BYTES:
        raise ValidationError(
            MENSAJE_ARCHIVO_TAMANO.format(nombre=nombre), code="tamano_excedido"
        )


def ruta_informe_final(instance, filename):
    """Ruta única por archivo: ``informes_finales/practica-<id>/<uuid>.pdf``.

    El nombre que envía el cliente no se usa como nombre en disco: dos informes
    de la misma práctica no pueden pisarse y el nombre original queda solo como
    metadato del ``FieldFile``.
    """
    sufijo = Path(str(filename)).suffix.lower() or ".pdf"
    return f"informes_finales/practica-{instance.practica_id}/{uuid4().hex}{sufijo}"


def ruta_informe_estudiante(instance, filename):
    """Ruta única del informe del estudiante: ``informes_estudiante/practica-<id>/<uuid>.pdf``.

    Misma regla que el informe del tutor de entidad y por la misma razón: dos
    versiones del informe de una práctica no pueden pisarse en el disco y el
    nombre que envía el cliente queda solo como metadato del ``FieldFile``.
    """
    sufijo = Path(str(filename)).suffix.lower() or ".pdf"
    return f"informes_estudiante/practica-{instance.practica_id}/{uuid4().hex}{sufijo}"


def validar_version_positiva(version):
    """Exige una versión desde 1; la primera versión del plan es la 1.

    Es un validador de campo, no ``Model.clean()``: Django lo ejecuta dentro de
    ``Field.clean()`` después de convertir el valor, así que un valor no
    numérico falla como ``ValidationError`` de campo y nunca llega aquí.
    """
    if version < 1:
        raise ValidationError(MENSAJE_VERSION)


class PlanActividades(models.Model):
    """Plan de actividades de una práctica (HU-01, RF-01).

    ``version`` empieza en 1 y la aporta quien crea la fila: el servicio de
    T024 crea la versión siguiente cuando el estudiante reenvía tras una
    devolución, así que el modelo no incrementa ni renumera nada. La pareja
    (``practica``, ``version``) es única en la base: la invariante no depende
    solo del bloqueo del servicio. ``contenido`` es obligatorio y el estado inicial es
    ``en_revision``; aprobar y devolver son transiciones de T024.

    ``practica`` usa ``PROTECT`` y las filas se conservan: una versión anterior
    no se borra al registrar otra. La versión debe ser un entero positivo y la
    comprueba ``validar_version_positiva`` dentro de ``full_clean()``. Este
    modelo no llama a ``full_clean()`` desde ``save()`` ni desde
    ``objects.create()``.
    """

    if TYPE_CHECKING:
        # ``Django`` crea estos atributos al cargar el modelo: ``practica_id``
        # para la clave foránea y ``validaciones`` para el ``related_name`` de
        # ``Validacion.plan``; ``get_estado_display`` lo genera ``choices``.
        practica_id: int
        validaciones: RelatedManager[Any]

        def get_estado_display(self) -> str: ...

    class Estado(models.TextChoices):
        EN_REVISION = "en_revision", "En revisión"
        APROBADO = "aprobado", "Aprobado"
        DEVUELTO = "devuelto", "Devuelto"

    practica = models.ForeignKey(
        "practicas.Practica",
        on_delete=models.PROTECT,
        related_name="planes_actividades",
    )
    version = models.PositiveIntegerField(
        default=1, validators=[validar_version_positiva]
    )
    contenido = models.TextField()
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.EN_REVISION
    )

    class Meta:
        verbose_name = "plan de actividades"
        verbose_name_plural = "planes de actividades"
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["practica", "version"],
                name="actividades_plan_version_unica_por_practica",
                violation_error_message=(
                    "Esa versión del plan ya existe para esta práctica."
                ),
            )
        ]

    def __str__(self):
        return f"Plan v{self.version} - práctica {self.practica_id}"


class Validacion(models.Model):
    """Decisión del tutor académico sobre un plan o un reporte (T023, RF-03, RF-04).

    El data-model pide «exactamente uno de los dos» entre ``plan_id`` y
    ``reporte_id``: una ``CheckConstraint`` lo impone en la base y ``clean()`` lo
    repite dentro de ``full_clean()``, así que ``objects.create()`` falla con
    ``IntegrityError`` y ``full_clean()`` con ``ValidationError``. Los dos lados
    son opcionales en el esquema porque la restricción es la que exige el par.

    ``decision`` solo admite «aprobado» o «devuelto», y ``observacion`` es
    obligatoria con «devuelto»: se valida en ``clean()`` dentro de
    ``full_clean()``, como el resto de las reglas condicionales del proyecto.
    ``autor`` y ``fecha`` son automáticos en el sentido de RF-04: la fecha la
    pone la base al insertar y el autor lo escribe el servicio que valida.
    """

    class Decision(models.TextChoices):
        APROBADO = "aprobado", "Aprobado"
        DEVUELTO = "devuelto", "Devuelto"

    if TYPE_CHECKING:
        # ``plan``, ``reporte`` e ``informe_estudiante`` son claves foráneas
        # opcionales, así que sus ``*_id`` son ``int | None``; ``decision`` tiene
        # ``choices`` y Django genera ``get_decision_display`` al cargar el modelo.
        plan_id: int | None
        reporte_id: int | None
        informe_estudiante_id: int | None
        autor_id: int
        practica_id: int

        def get_decision_display(self) -> str: ...

    practica = models.ForeignKey(
        "practicas.Practica", on_delete=models.PROTECT, related_name="validaciones"
    )
    plan = models.ForeignKey(
        PlanActividades,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="validaciones",
    )
    reporte = models.ForeignKey(
        "reportes.ReporteSemanal",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="validaciones",
    )
    informe_estudiante = models.ForeignKey(
        "InformeEstudiante",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="validaciones",
    )
    decision = models.CharField(
        max_length=20,
        choices=Decision.choices,
        error_messages={"invalid_choice": MENSAJE_DECISION},
    )
    observacion = models.TextField(blank=True, default="")
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="validaciones"
    )
    fecha = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        verbose_name = "validación"
        verbose_name_plural = "validaciones"
        constraints: ClassVar[list] = [
            models.CheckConstraint(
                condition=(
                    models.Q(
                        plan__isnull=False,
                        reporte__isnull=True,
                        informe_estudiante__isnull=True,
                    )
                    | models.Q(
                        plan__isnull=True,
                        reporte__isnull=False,
                        informe_estudiante__isnull=True,
                    )
                    | models.Q(
                        plan__isnull=True,
                        reporte__isnull=True,
                        informe_estudiante__isnull=False,
                    )
                ),
                name="actividades_validacion_plan_reporte_o_informe",
                violation_error_message=MENSAJE_EXACTAMENTE_UNO,
            )
        ]

    def __str__(self):
        return (
            f"Validación {self.get_decision_display()} - plan {self.plan_id} "
            f"/ reporte {self.reporte_id} / informe {self.informe_estudiante_id}"
        )

    def clean(self):
        """Exige exactamente uno de plan, reporte o informe, y observación al devolver.

        La restricción «exactamente uno de tres» se comprueba contando las
        referencias no nulas: con dos o con ninguna se rechaza en la clave
        ``reporte``, que es la que el cliente ya conoce de la migración
        anterior. La base impone la misma regla con su ``CheckConstraint``.
        """
        super().clean()
        referencias = (
            self.plan_id,
            self.reporte_id,
            self.informe_estudiante_id,
        )
        presentes = [
            referencia for referencia in referencias if isinstance(referencia, int)
        ]
        if len(presentes) != 1:
            raise ValidationError({"reporte": MENSAJE_EXACTAMENTE_UNO})
        if (
            self.decision == self.Decision.DEVUELTO
            and not (self.observacion or "").strip()
        ):
            raise ValidationError({"observacion": MENSAJE_OBSERVACION})


class ConfirmacionEntidad(models.Model):
    """Confirmación del tutor de entidad sobre un reporte semanal (HU-07, RF-08).

    Es la escritura del caso 2 de HU-07: queda registrado **quién** confirmó
    —``tutor_entidad``, con el rol acotado en el esquema y releído de la fila
    guardada por el servicio— y **cuándo** (``fecha``, la pone la base al
    insertar). El data-model no define más campos: no hay estado, ni observación,
    ni una ``practica`` duplicada, y la confirmación **no** cambia el estado del
    reporte ni el de la práctica (S9).

    Un reporte se confirma una sola vez: la ``UniqueConstraint`` de ``reporte``
    lo impone en la base, así que ``objects.create()`` —que no ejecuta
    ``full_clean()``— también falla con ``IntegrityError``. ``PROTECT`` conserva
    la fila aunque se intente borrar el reporte o el usuario.
    """

    if TYPE_CHECKING:
        # ``Django`` añade los ``*_id`` de las claves foráneas al cargar el modelo.
        reporte_id: int
        tutor_entidad_id: int

    reporte = models.ForeignKey(
        "reportes.ReporteSemanal",
        on_delete=models.PROTECT,
        related_name="confirmaciones_entidad",
    )
    tutor_entidad = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        limit_choices_to={"rol": Usuario.Rol.TUTOR_ENTIDAD},
        related_name="confirmaciones_entidad",
        error_messages={"invalid": MENSAJE_TUTOR_ENTIDAD_ROL},
    )
    fecha = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        verbose_name = "confirmación de entidad"
        verbose_name_plural = "confirmaciones de entidad"
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["reporte"],
                name="actividades_confirmacion_unica_por_reporte",
                violation_error_message=MENSAJE_CONFIRMACION_UNICA,
            )
        ]

    def __str__(self):
        return (
            f"Confirmación - reporte {self.reporte_id} - tutor {self.tutor_entidad_id}"
        )


class InformeFinal(models.Model):
    """Informe final del tutor de entidad sobre la práctica (HU-07, RF-08).

    Es la escritura del caso 1 de HU-07: el informe queda asociado a la práctica
    con su autor (``tutor_entidad``, rol acotado en el esquema) y su fecha
    automática. El data-model pide «contenido **o** archivo» y esta entidad lo
    impone como «exactamente uno», igual que ``Validacion`` con plan o reporte:
    la ``CheckConstraint`` lo exige en la base y ``clean()`` lo repite dentro de
    ``full_clean()``, así que ni los dos vacíos ni los dos llenos entran por
    ninguna ruta.

    ``archivo`` es un ``FileField`` (ADR 0005) con ruta única por archivo y la
    validación de PDF de hasta 5 MB como validador de campo; no hay ``MEDIA_ROOT``
    en los settings, así que la ruta se resuelve contra el almacenamiento por
    defecto. El vacío de un ``FileField`` es la cadena vacía y no ``NULL`` —la
    recomendación de Django— porque la ``CheckConstraint`` se evalúa también en
    Python dentro de ``full_clean()`` y ahí un ``FieldFile`` vacío nunca es
    ``None``: con ``NULL`` la restricción se leería al revés. Registrar el
    informe **no** cambia el estado de la práctica ni escribe historial (S9): el
    cierre es de otra unidad.
    """

    if TYPE_CHECKING:
        practica_id: int
        tutor_entidad_id: int

    practica = models.ForeignKey(
        "practicas.Practica",
        on_delete=models.PROTECT,
        related_name="informes_finales",
    )
    tutor_entidad = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        limit_choices_to={"rol": Usuario.Rol.TUTOR_ENTIDAD},
        related_name="informes_finales",
        error_messages={"invalid": MENSAJE_TUTOR_ENTIDAD_ROL},
    )
    contenido = models.TextField(null=True, blank=True)
    archivo = models.FileField(
        upload_to=ruta_informe_final,
        blank=True,
        default="",
        validators=[validar_archivo_informe],
    )
    fecha = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        verbose_name = "informe final"
        verbose_name_plural = "informes finales"
        constraints: ClassVar[list] = [
            models.CheckConstraint(
                condition=(
                    models.Q(contenido__isnull=False, archivo="")
                    | (models.Q(contenido__isnull=True) & ~models.Q(archivo=""))
                ),
                name="actividades_informe_final_contenido_o_archivo",
                violation_error_message=MENSAJE_INFORME_UNO,
            )
        ]

    def __str__(self):
        return f"Informe final - práctica {self.practica_id} - tutor {self.tutor_entidad_id}"

    def clean(self):
        """Exige contenido **o** archivo —exactamente uno—, nunca ambos ni ninguno.

        El texto se mira recortado: un contenido en blanco no cuenta como
        contenido. El rechazo se reporta en las dos claves porque el cliente
        necesita saber que las dos rutas de entrada están mal, no una.
        """
        super().clean()
        texto = (self.contenido or "").strip()
        if bool(texto) == bool(self.archivo):
            raise ValidationError(
                {"contenido": MENSAJE_INFORME_UNO, "archivo": MENSAJE_INFORME_UNO}
            )


class InformeEstudiante(models.Model):
    """Informe final que el estudiante presenta al cerrar su práctica (RF-16, C-10).

    Es la entidad de HU-10: el estudiante de la práctica presenta su informe
    final de actividades —un PDF de hasta 5 MB (ADR 0005, RNF-05)—, el informe
    queda «en revisión» y su tutor académico lo ve pendiente; el tutor lo valida
    o lo devuelve con observación reutilizando la decisión de C-04, que escribe
    ``Validacion`` con ``informe_estudiante``.

    **Nombre**: ``InformeFinal`` (arriba) es el informe del **tutor de entidad**
    sobre la práctica (HU-07, C-13, RF-08); el informe del **estudiante** es esta
    entidad. El nombre se elige para no romper nada de RF-08 ni reutilizar una
    tabla con otro autor y otro ciclo de vida (ver README de la app).

    ``version`` empieza en 1 y la aporta el servicio: un informe devuelto y
    reenviado deja dos versiones y solo la última cuenta como «revisado» para el
    cierre. La pareja (``practica``, ``version``) es única en la base, así que la
    invariante no depende solo del bloqueo del servicio. ``estado`` inicia
    ``en_revision`` y no cambia ``Practica.estado``: la transición ``en revisión
    final`` → ``en curso`` sigue sin implementarse hasta que P-05 se decida.

    ``estudiante`` es el autor guardado de la fila y no lleva ``limit_choices_to``
    por rol: el rol lo exige el servicio contra la fila persistida de la práctica
    (``practica.estudiante_id``), que es la única fuente del permiso. ``archivo``
    es obligatorio y se valida como PDF de hasta 5 MB con el validador de campo
    ``validar_archivo_informe`` de RF-08, reutilizado en lugar de duplicado.
    """

    if TYPE_CHECKING:
        practica_id: int
        estudiante_id: int

    class Estado(models.TextChoices):
        EN_REVISION = "en_revision", "En revisión"
        VALIDADO = "validado", "Validado"
        DEVUELTO = "devuelto", "Devuelto"

    practica = models.ForeignKey(
        "practicas.Practica",
        on_delete=models.PROTECT,
        related_name="informes_estudiante",
    )
    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="informes_estudiante",
    )
    version = models.PositiveIntegerField(
        default=1, validators=[validar_version_positiva]
    )
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.EN_REVISION
    )
    fecha = models.DateTimeField(auto_now_add=True, editable=False)
    archivo = models.FileField(
        upload_to=ruta_informe_estudiante,
        validators=[validar_archivo_informe],
    )

    class Meta:
        verbose_name = "informe final del estudiante"
        verbose_name_plural = "informes finales del estudiante"
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["practica", "version"],
                name="actividades_informe_estudiante_version_unica",
                violation_error_message=MENSAJE_INFORME_ESTUDIANTE_VERSION,
            )
        ]

    def __str__(self):
        return (
            f"Informe del estudiante v{self.version} - práctica "
            f"{self.practica_id} - {self.estado}"
        )
