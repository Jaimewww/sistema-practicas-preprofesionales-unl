"""Modelo de usuario del sistema con rol y carrera (T012, RF-11, data-model.md)."""

from asgiref.sync import sync_to_async
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.db import models


class UsuarioManager(UserManager):
    """Reutiliza la creación de Django y valida el modelo antes de escribir."""

    def _create_user_object(self, username, email, password, **extra_fields):
        usuario = super()._create_user_object(
            username, email, password, **extra_fields
        )
        usuario.full_clean()
        return usuario

    async def _acreate_user(self, username, email, password, **extra_fields):
        usuario = super()._create_user_object(
            username, email, password, **extra_fields
        )
        await sync_to_async(usuario.full_clean)()
        await usuario.asave(using=self._db)
        return usuario


class Usuario(AbstractUser):
    """Cuenta de acceso con un solo rol del MVP y la carrera que lo acota.

    Hereda el login por ``username``, el hash de contraseña, las sesiones y las
    banderas de privilegio. La creación pública (``createsuperuser``,
    ``create_user`` y ``create_superuser``) valida con ``full_clean()`` antes
    de escribir; ``save()`` directo no valida.
    """

    class Rol(models.TextChoices):
        ESTUDIANTE = "estudiante", "Estudiante"
        TUTOR_ACADEMICO = "tutor_academico", "Tutor académico"
        TUTOR_ENTIDAD = "tutor_entidad", "Tutor de entidad"
        COORDINADOR = "coordinador", "Coordinador"
        DIRECTOR = "director", "Director"
        SECRETARIA = "secretaria", "Secretaría"

    ROLES_CON_CARRERA = frozenset(
        {Rol.COORDINADOR, Rol.TUTOR_ACADEMICO, Rol.DIRECTOR, Rol.SECRETARIA}
    )
    REQUIRED_FIELDS = ["nombre", "email", "rol"]

    nombre = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    rol = models.CharField(max_length=20, choices=Rol.choices)
    carrera = models.ForeignKey(
        "carreras.Carrera",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="usuarios",
    )

    objects = UsuarioManager()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def clean(self):
        """Exige carrera en los roles cuyo alcance de datos es una carrera (RF-11)."""
        super().clean()
        if self.rol in self.ROLES_CON_CARRERA and self.carrera_id is None:
            raise ValidationError(
                {"carrera": "La carrera es obligatoria para este rol."}
            )
