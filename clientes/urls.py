app_name = 'clientes'
from django.urls import path
from . import views
from .views import (
    ClienteListView,
    ClienteCreateView,
    UpdateView, # Esta importação estava errada antes, vamos corrigir
    ClienteUpdateView, # Importe a sua UpdateView correta
    ClienteDeleteView,
    ClienteDetailView  # <-- Importe a nova view
)

urlpatterns = [
    path('', ClienteListView.as_view(), name='cliente_list'),
    path('novo/', ClienteCreateView.as_view(), name='cliente_create'),
    
    # --- ADICIONE ESTA NOVA ROTA ABAIXO ---
    path('<int:pk>/', ClienteDetailView.as_view(), name='cliente_detail'),

    path('<int:pk>/editar/', ClienteUpdateView.as_view(), name='cliente_update'),
    path('<int:pk>/deletar/', ClienteDeleteView.as_view(), name='cliente_delete'),
    path('ajax/add-nacionalidade/', views.add_nacionalidade_ajax, name='add_nacionalidade_ajax'),
    path('ajax/add-estado-civil/', views.add_estado_civil_ajax, name='add_estado_civil_ajax'),
    path('ajax/add-profissao/', views.add_profissao_ajax, name='add_profissao_ajax'),
]