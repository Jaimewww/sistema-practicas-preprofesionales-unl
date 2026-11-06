"""
Django settings for config project.

The values come from the environment contract of issue #76 (S4): DEBUG is off
unless DJANGO_DEBUG is exactly ``True``; DJANGO_SECRET_KEY has no default value
in the code — without it settings fail closed when ``DEBUG`` is False, and with
``DEBUG`` on Django runs with an ephemeral random key for the process (never
written anywhere). DJANGO_ALLOWED_HOSTS is a comma-separated list. The database is PostgreSQL when POSTGRES_HOST or
POSTGRES_DB is present (the compose stack of #81 provides them) and the local
SQLite file otherwise.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/


def _env_flag(nombre, por_defecto=False):
    """Las banderas del entorno son literales: solo «True» enciende."""
    valor = os.environ.get(nombre)
    if valor is None:
        return por_defecto
    return valor == 'True'


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = _env_flag('DJANGO_DEBUG')

# SECURITY WARNING: keep the secret key used in production secret!
MENSAJE_CLAVE_REQUERIDA = (
    'Falta la variable de entorno DJANGO_SECRET_KEY: no hay valor por defecto '
    'en el código (contrato S4). Expórtela para correr servidores con '
    'DEBUG apagado.'
)
try:
    SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
except KeyError:
    if DEBUG:
        # Solo desarrollo: clave efímera de proceso, sin valor fijado en el
        # código y que no sobrevive al reinicio (cierres de sesión esperados).
        SECRET_KEY = get_random_secret_key()
    else:
        raise ImproperlyConfigured(MENSAJE_CLAVE_REQUERIDA) from None

ALLOWED_HOSTS = [
    host.strip() for host in os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',')
    if host.strip()
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.health',
    'apps.carreras',
    'apps.entidades',
    'apps.practicas',
    'apps.auditoria',
    'apps.actividades',
    'apps.reportes',
    'apps.usuarios',
    'apps.prototipo',
    # Contrato universal de respuesta y OpenAPI (#77).
    'rest_framework',
    'apps.contrato',
    'drf_spectacular',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.prototipo.context_processors.notificaciones',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
# The compose stack of #81 plants POSTGRES_*; without them the local SQLite
# fallback keeps the development and test runs working.

if os.environ.get('POSTGRES_HOST') or os.environ.get('POSTGRES_DB'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', ''),
            'USER': os.environ.get('POSTGRES_USER', ''),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
            'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


AUTH_USER_MODEL = 'usuarios.Usuario'

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Contrato de la API v1 (#77, S2-S4). El envelope es el ÚNICO renderer por
# defecto: sin BrowsableAPIRenderer y sin un JSONRenderer duplicado, ninguna
# respuesta DRF puede salir sin envolver. El shape del error lo define el
# handler; el de éxito, el renderer. Los endpoints de negocio de /api/v1/ son
# de #78 y la autenticación real de #79.
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'apps.contrato.renderer.SuccessEnvelopeRenderer',
    ],
    'EXCEPTION_HANDLER': 'apps.contrato.exceptions.envelope_exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Solo lo mínimo para /api/v1/schema/ y /api/v1/docs/: sin SERVE_INCLUDE_SCHEMA
# el propio schema no se auto-documenta, y el acceso queda abierto porque la
# frontera de autorización es #79.
SPECTACULAR_SETTINGS = {
    'TITLE': 'Sistema de Prácticas Profesionales UNL',
    'DESCRIPTION': 'Contrato universal de respuesta de la API v1.',
    'VERSION': '0.1.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
}
