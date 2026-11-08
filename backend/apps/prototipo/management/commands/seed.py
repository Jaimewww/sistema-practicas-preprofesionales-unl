"""Carga los datos de demostración de ``apps.prototipo.sample_data``.

Uso::

    DJANGO_SECRET_KEY=<clave> python manage.py seed

Mapeo, decidido aquí porque ``sample_data`` es el guion de la demo y no un
fixture:

- ``Carrera``: el título del demo es «CÓDIGO - NOMBRE - …». El modelo exige un
  código único y las tres carreras del demo comparten «FEIRNNR», así que el
  código se compone con el primer tramo del nombre
  (``FEIRNNR-computacion``), y el nombre es el resto del título. Se siembran la
  carrera del coordinador y las dos carreras ajenas del catálogo (RF-11); las
  prácticas son solo las de la carrera del coordinador, tal como las ve C1.
- ``ConfiguracionCarrera``: una fila por modalidad con las horas y plazos de
  ``sample_data.CONFIGURACION_CARRERA``. La modalidad «distancia» del demo no
  existe en el modelo y no se siembra.
- ``Periodo``: el demo nombra el período («MAR.26-AGO.26 GRADO»); las fechas no
  están en los datos y se fijan en ``PERIODOS`` con el mes de inicio y el de fin
  del rótulo. Solo se crean los períodos que usan las prácticas sembradas.
- ``EntidadReceptora``: el nombre que trae cada práctica (el demo no tiene más
  campos).
- ``Usuario``: una cuenta por persona del demo, con el rol del papel que juega
  (estudiante, tutor académico, tutor de entidad) más el coordinador, el
  director y la secretaría. El ``username`` es el nombre normalizado a un slug y
  el correo ``<slug>@demo.unl.edu.ec``; la cuenta no tiene contraseña usable.
  El modelo admite una carrera por usuario: se le asigna la del coordinador,
  que es la única que tiene prácticas.
- ``Practica`` y ``AsignacionTutor``: la práctica se crea con
  ``asignar_practica``, que copia las horas de la configuración vigente y
  escribe el historial inicial; el estado del demo se alcanza con
  ``cambiar_estado_practica`` (la misma tabla de transiciones) y los motivos de
  suspensión y cancelación salen del historial del demo. La asignación del tutor
  académico se crea aparte porque ese servicio no la incluye.
- ``PlanActividades``: el contenido es la lista de actividades unida por saltos
  de línea y «validado» se traduce a ``aprobado``. La ``Validacion`` se escribe
  con ``full_clean()`` y no con ``aprobar_plan``: el plan del demo ya está
  decidido y aprobarlo otra vez movería la práctica y duplicaría historial.
- El historial del demo no se copia como tal: ``HistorialEstado.fecha`` es
  ``auto_now_add`` y no admite fechas pasadas, así que el diario se reconstruye
  con la fecha de la siembra. El autor que el demo firma como «SISTEMA» pasa a
  ser el coordinador, porque en los modelos reales el autor es obligatorio.

La siembra es todo o nada (una transacción) y se rechaza si ya hay datos de
demostración cargados: ejecutarla dos veces no duplica ni reescribe nada.
"""

import re
import unicodedata
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.actividades.models import PlanActividades, Validacion
from apps.carreras.models import Carrera, ConfiguracionCarrera
from apps.entidades.models import EntidadReceptora
from apps.practicas.models import AsignacionTutor, Periodo, Practica
from apps.practicas.services import asignar_practica, cambiar_estado_practica
from apps.prototipo import sample_data
from apps.usuarios.models import Usuario

PERIODOS = {
    sample_data.PERIODO: (date(2026, 3, 1), date(2026, 8, 31)),
    sample_data.PERIODO_ANTERIOR: (date(2025, 9, 1), date(2026, 1, 31)),
}
CARRERAS = (sample_data.CARRERA_COORDINADOR, *sample_data.CARRERAS_OTRAS)
AUTORIDADES = (
    (sample_data.COORDINADOR, Usuario.Rol.COORDINADOR),
    (sample_data.DIRECTOR, Usuario.Rol.DIRECTOR),
    (sample_data.SECRETARIA, Usuario.Rol.SECRETARIA),
)
ESTADO_PLAN = {
    "validado": PlanActividades.Estado.APROBADO,
    "en_revision": PlanActividades.Estado.EN_REVISION,
}
# La configuración se siembra vigente desde antes del período del demo para que
# `asignar_practica` la encuentre sin depender del día en que se ejecuta.
VIGENTE_DESDE = date(2020, 1, 1)
MENSAJE_YA_SEMBRADO = (
    "Los datos de demostración ya están cargados en esta base: «seed» no se "
    "ejecuta dos veces. Use una base vacía para volver a sembrar."
)


def _slug(texto):
    """Texto a identificador: sin acentos, en minúsculas y con guiones."""
    sin_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore")
    return re.sub(r"[^a-z0-9]+", "-", sin_acentos.decode().lower()).strip("-")


def _carrera(titulo):
    """«FEIRNNR - COMPUTACIÓN - …» a (código único, nombre)."""
    codigo, _, nombre = titulo.partition(" - ")
    return f"{codigo}-{_slug(nombre.split(' - ')[0])}", nombre


class Command(BaseCommand):
    help = "Carga los datos de demostración de apps.prototipo.sample_data."

    def handle(self, *args, **options):
        if Carrera.objects.filter(codigo__in=[_carrera(t)[0] for t in CARRERAS]).exists():
            # Idempotente (comentario de review de #76): el entrypoint de Docker
            # (#88) corre seed en cada arranque, así que la segunda corrida es
            # un no-op informado, no un error.
            self.stdout.write(MENSAJE_YA_SEMBRADO)
            return
        practicas = sample_data.practicas_de_la_carrera()
        with transaction.atomic():
            resumen = self._sembrar(practicas)
        self.stdout.write(
            "Semilla de demostración cargada: "
            + ", ".join(f"{cantidad} {etiqueta}" for etiqueta, cantidad in resumen)
            + "."
        )

    def _sembrar(self, practicas):
        carreras = self._carreras()
        periodos = self._periodos(practicas)
        entidades = self._entidades(practicas)
        usuarios = self._usuarios(practicas, carreras)
        validaciones = 0
        for origen in practicas:
            practica = self._practica(origen, carreras, periodos, entidades, usuarios)
            self._asignacion(practica, origen, usuarios)
            validaciones += self._plan(practica, origen, usuarios)
        return (
            ("carreras", len(carreras)),
            ("períodos", len(periodos)),
            ("entidades receptoras", len(entidades)),
            ("usuarios", len(usuarios)),
            ("prácticas", len(practicas)),
            ("asignaciones de tutor", len(practicas)),
            ("planes de actividades", len(practicas)),
            ("validaciones", validaciones),
        )

    def _carreras(self):
        carreras = {}
        for titulo in CARRERAS:
            codigo, nombre = _carrera(titulo)
            carreras[titulo] = Carrera.objects.create(codigo=codigo, nombre=nombre)
        configuracion = sample_data.CONFIGURACION_CARRERA
        for modalidad in (Practica.Tipo.LABORAL, Practica.Tipo.COMUNITARIA):
            fila = ConfiguracionCarrera(
                carrera=carreras[sample_data.CARRERA_COORDINADOR],
                modalidad=modalidad,
                horas_requeridas=configuracion[f"horas_{modalidad}"],
                plazo_reporte_dias=configuracion["plazo_reporte_dias"],
                plazo_revision_dias=configuracion["plazo_revision_dias"],
                umbral_rezago=configuracion["umbral_rezago"],
                vigente_desde=VIGENTE_DESDE,
            )
            fila.full_clean()
            fila.save()
        return carreras

    def _periodos(self, practicas):
        periodos = {}
        for nombre in sorted({origen["periodo"] for origen in practicas}):
            inicio, fin = PERIODOS[nombre]
            periodo = Periodo(nombre=nombre, fecha_inicio=inicio, fecha_fin=fin)
            periodo.full_clean()
            periodo.save()
            periodos[nombre] = periodo
        return periodos

    def _entidades(self, practicas):
        entidades = {}
        for nombre in sorted({origen["entidad"] for origen in practicas if origen["entidad"]}):
            entidad = EntidadReceptora(nombre=nombre)
            entidad.full_clean()
            entidad.save()
            entidades[nombre] = entidad
        return entidades

    def _usuarios(self, practicas, carreras):
        personas = {}
        for origen in practicas:
            personas.setdefault(origen["estudiante"], Usuario.Rol.ESTUDIANTE)
            personas.setdefault(origen["tutor_academico"], Usuario.Rol.TUTOR_ACADEMICO)
            if origen["tutor_entidad"]:
                personas.setdefault(origen["tutor_entidad"], Usuario.Rol.TUTOR_ENTIDAD)
        for nombre, rol in AUTORIDADES:
            personas.setdefault(nombre, rol)
        carrera = carreras[sample_data.CARRERA_COORDINADOR]
        return {
            nombre: self._usuario(nombre, rol, carrera)
            for nombre, rol in personas.items()
        }

    def _usuario(self, nombre, rol, carrera):
        base = _slug(nombre)
        identificador = base
        numero = 2
        while Usuario.objects.filter(username=identificador).exists():
            identificador = f"{base}-{numero}"
            numero += 1
        usuario = Usuario(
            username=identificador,
            nombre=nombre,
            email=f"{identificador}@demo.unl.edu.ec",
            rol=rol,
            carrera=carrera,
        )
        usuario.set_unusable_password()
        usuario.full_clean()
        usuario.save()
        return usuario

    def _practica(self, origen, carreras, periodos, entidades, usuarios):
        practica = asignar_practica(
            estudiante=usuarios[origen["estudiante"]],
            carrera=carreras[origen["carrera"]],
            periodo=periodos[origen["periodo"]],
            tipo=origen["tipo"],
            autor=usuarios[sample_data.COORDINADOR],
            entidad=entidades.get(origen["entidad"]),
            subtipo=origen["subtipo"],
            proyecto_vinculacion=origen["proyecto_vinculacion"],
            tutor_entidad=usuarios.get(origen["tutor_entidad"]),
        )
        for entrada in origen["historial"][1:]:
            practica = cambiar_estado_practica(
                practica=practica,
                nuevo_estado=entrada["estado_nuevo"],
                autor=usuarios.get(entrada["autor"], usuarios[sample_data.COORDINADOR]),
                motivo=entrada["motivo"] or "",
            )
        return practica

    def _asignacion(self, practica, origen, usuarios):
        asignacion = AsignacionTutor(
            practica=practica,
            tutor_academico=usuarios[origen["tutor_academico"]],
            desde=origen["historial"][0]["fecha"],
        )
        asignacion.full_clean()
        asignacion.save()

    def _plan(self, practica, origen, usuarios):
        plan_origen = origen["plan"]
        plan = PlanActividades(
            practica=practica,
            version=1,
            contenido="\n".join(plan_origen["actividades"]),
            estado=ESTADO_PLAN[plan_origen["estado"]],
        )
        plan.full_clean()
        plan.save()
        if plan.estado != PlanActividades.Estado.APROBADO:
            return 0
        validacion = Validacion(
            practica=practica,
            plan=plan,
            decision=Validacion.Decision.APROBADO,
            autor=usuarios[origen["tutor_academico"]],
        )
        validacion.full_clean()
        validacion.save()
        return 1
