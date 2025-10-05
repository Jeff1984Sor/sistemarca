# aureon_core/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import nested_admin

# Esta é a lista principal de URLs da sua aplicação
urlpatterns = [
    # Rotas de ferramentas e administração
    path('admin/', admin.site.urls),
    #path('oauth2/', include('django_auth_adfs.urls')),
    path('nested_admin/', include('nested_admin.urls')),

    # Rotas dos seus apps
    path('contas/', include('contas.urls')),
    path('clientes/', include('clientes.urls')),
    path('casos/', include('casos.urls')),
    path('equipamentos/', include('equipamentos.urls')), 

    # Adicione o include para 'notificacoes' se ele tiver URLs próprias
    
    # Rota principal (home page) do app 'core'
    path('', include('core.urls')),
]

if 'django_auth_adfs' in settings.INSTALLED_APPS:
    urlpatterns.append(path('oauth2/', include('django_auth_adfs.urls')))
    
# A MÁGICA PARA SERVIR ARQUIVOS DE MÍDIA EM DESENVOLVIMENTO
# Este bloco 'if' deve vir DEPOIS de 'urlpatterns'
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)