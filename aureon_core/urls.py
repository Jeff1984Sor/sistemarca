# aureon_core/urls.py (VERSÃO FINAL E LIMPA)

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Rotas de administração
    path('admin/', admin.site.urls),
    path('nested_admin/', include('nested_admin.urls')),

    # Rota principal do sistema de autenticação (django-allauth)
    path('accounts/', include('allauth.urls')),
    
    # Rotas dos seus aplicativos
    path('contas/', include('contas.urls')),
    path('clientes/', include('clientes.urls')),
    path('casos/', include('casos.urls')),
    path('equipamentos/', include('equipamentos.urls')), 
    
    # Rota principal (home page)
    path('', include('core.urls')),
]

# Adiciona as URLs para servir arquivos de mídia em ambiente de desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)