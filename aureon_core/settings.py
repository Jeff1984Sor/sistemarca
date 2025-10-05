# aureon_core/settings.py (ATUALIZADO PARA DJANGO-ALLAUTH)

import os
import dj_database_url
from pathlib import Path
from dotenv import load_dotenv 

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-default-key-for-dev')

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

NGROK_HOSTNAME = os.environ.get('NGROK_HOSTNAME')
if not RENDER_EXTERNAL_HOSTNAME and NGROK_HOSTNAME:
    ALLOWED_HOSTS.append(NGROK_HOSTNAME)

# ==============================================================================
# 1. DEFINIÇÕES BASE DAS APLICAÇÕES E TEMPLATES
# ==============================================================================

INSTALLED_APPS = [
    'admin_interface', 
    'colorfield', 
    'nested_admin',
    'django.contrib.admin', 
    'django.contrib.auth', 
    'django.contrib.contenttypes',
    'django.contrib.sessions', 
    'django.contrib.messages', 
    'django.contrib.staticfiles',
    
    # Apps do django-allauth (NECESSÁRIAS PARA O NOVO LOGIN)
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.microsoft', # Provedor da Microsoft

    # Seus apps
    'core.apps.CoreConfig', 
    'contas.apps.ContasConfig', 
    'clientes.apps.ClientesConfig',
    'casos.apps.CasosConfig', 
    'notificacoes.apps.NotificacoesConfig',
    'equipamentos.apps.EquipamentosConfig', 
    'configuracoes.apps.ConfiguracoesConfig',
]

# NECESSÁRIO PARA O DJANGO-ALLAUTH
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',
    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'aureon_core' / 'templates'], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request', # allauth precisa disso
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'configuracoes.context_processors.logo_processor',
                'configuracoes.context_processors.modulos_visiveis', # Robô reativado
            ],
        },
    },
]

# ==============================================================================
# CONFIGURAÇÕES PADRÃO (MIDDLEWARE, BANCO DE DADOS, ETC.)
# ==============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware', 
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', 
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware', 
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware', 
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Middleware do allauth (adicionado)
    "allauth.account.middleware.AccountMiddleware",
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

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==============================================================================
# CONFIGURAÇÕES DO DJANGO-ALLAUTH
# ==============================================================================

# Redireciona para a home após o login (seja local ou social)
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'
# Página de login padrão agora será a do allauth, mas podemos customizar
LOGIN_URL = 'account_login' 

# Configurações específicas do provedor Microsoft
SOCIALACCOUNT_PROVIDERS = {
    'microsoft': {
        'TENANT': os.environ.get('SHAREPOINT_TENANT_ID'),
        'SCOPE': [
            'User.Read', # Permissão básica para ler o perfil
            'Sites.ReadWrite.All',
            'Mail.ReadWrite',
            'Mail.Send',
            'offline_access',
        ],
    }
}

# Mapeia os campos da Microsoft para os campos do usuário Django
SOCIALACCOUNT_ADAPTER = 'contas.adapter.MySocialAccountAdapter'
ACCOUNT_EMAIL_VERIFICATION = "none" # Simplifica o fluxo por enquanto
ACCOUNT_AUTHENTICATION_METHOD = "username_email" # Permite logar com user ou email
ACCOUNT_EMAIL_REQUIRED = True

# ==============================================================================
# OUTRAS CONFIGURAÇÕES
# ==============================================================================

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
# ... (o resto das suas configurações como STATIC_URL, MEDIA_URL, etc., podem continuar como estão)
# Removi os blocos dinâmicos e de AUTH_ADFS que não são mais necessários
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