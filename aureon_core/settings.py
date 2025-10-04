import os
import dj_database_url
from pathlib import Path
from dotenv import load_dotenv 

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-default-key-for-dev')

IS_PRODUCTION = 'RENDER' in os.environ

if IS_PRODUCTION:
    DEBUG = False
else:
    DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Adiciona a URL do Ngrok se estiver em desenvolvimento e a variável existir
NGROK_HOSTNAME = os.environ.get('NGROK_HOSTNAME')
if not IS_PRODUCTION and NGROK_HOSTNAME:
    ALLOWED_HOSTS.append(NGROK_HOSTNAME)

INSTALLED_APPS = [
    'admin_interface', 
    'colorfield', 
    'django_auth_adfs',
    'nested_admin',
    'django.contrib.admin', 
    'django.contrib.auth', 
    'django.contrib.contenttypes',
    'django.contrib.sessions', 
    'django.contrib.messages', 
    'django.contrib.staticfiles',
    'core.apps.CoreConfig', 
    'contas.apps.ContasConfig', 
    'clientes.apps.ClientesConfig',
    'casos.apps.CasosConfig', 
    'notificacoes.apps.NotificacoesConfig',
    'equipamentos.apps.EquipamentosConfig', 
    'configuracoes.apps.ConfiguracoesConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware', 
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', 
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware', 
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware', 
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'aureon_core.urls'
WSGI_APPLICATION = 'aureon_core.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
if 'DATABASE_URL' in os.environ:
    DATABASES['default'] = dj_database_url.config(conn_max_age=600, ssl_require=True)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'configuracoes.context_processors.modulos_visiveis',
                'configuracoes.context_processors.logo_processor',
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = (
    'contas.auth.CustomAdfsAuthCodeBackend',
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_ADFS = {
    "CLIENT_ID": os.environ.get('SHAREPOINT_CLIENT_ID'),
    "CLIENT_SECRET": os.environ.get('SHAREPOINT_CLIENT_SECRET'),
    "TENANT_ID": os.environ.get('SHAREPOINT_TENANT_ID'),
    "RELYING_PARTY_ID": os.environ.get('SHAREPOINT_CLIENT_ID'),
    "AUDIENCE": os.environ.get('SHAREPOINT_CLIENT_ID'),
    "CLAIM_MAPPING": {
        "first_name": "given_name",
        "last_name": "family_name",
        "email": "upn",
    },
    "GROUPS_CLAIM": "groups", 
    "MIRROR_GROUPS": True,
    "SCOPES": [
        "openid", "profile", "email", 
        "https://graph.microsoft.com/Sites.ReadWrite.All",
        "https://graph.microsoft.com/Mail.ReadWrite",
        "https://graph.microsoft.com/Mail.Send",
        "offline_access"
    ],
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STORAGES = {
    "default": { "BACKEND": "django.core.files.storage.FileSystemStorage" },
    "staticfiles": { "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage" },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'
LOGIN_URL = 'login'
X_FRAME_OPTIONS = "SAMEORIGIN"
SILENCED_SYSTEM_CHECKS = ["security.W019"]
INTERNAL_IPS = ["127.0.0.1"]

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

WEBHOOK_BASE_URL = os.environ.get('WEBHOOK_BASE_URL')

STATICFILES_DIRS = [BASE_DIR / 'static']

SHAREPOINT_SITE_URL = "rcostaadvcombr.sharepoint.com"
SHAREPOINT_DRIVE_ID = os.environ.get('SHAREPOINT_DRIVE_ID')

CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')