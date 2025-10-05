# aureon_core/urls.py (ATUALIZADO PARA DJANGO-ALLAUTH)

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# A importação do nested_admin não é mais necessária aqui,
# pois a sua URL já está sendo incluída.

urlpatterns = [
    # Rotas de ferramentas e administração
    path('admin/', admin.site.urls),
    
    # --- ROTA PARA O DJANGO-ALLAUTH ---
    # Adiciona todas as URLs necessárias para o novo sistema de login
    # (ex: /accounts/login/, /accounts/logout/, /accounts/microsoft/login/, etc.)
    path('accounts/', include('allauth.urls')),
    
    # --- SUAS URLS EXISTENTES ---
    # Mantive a do nested_admin por precaução, embora o allauth não dependa dela.
    path('nested_admin/', include('nested_admin.urls')),
    path('contas/', include('contas.urls')),
    path('clientes/', include('clientes.urls')),
    path('casos/', include('casos.urls')),
    path('equipamentos/', include('equipamentos.urls')), 
    path('', include('core.urls')), # Rota principal (home page)
]

# Lógica para servir arquivos de mídia em desenvolvimento (mantida)
if settings.DEBUG:
    # A LINHA CORRETA E COMPLETA
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)