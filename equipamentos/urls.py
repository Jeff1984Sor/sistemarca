# equipamentos/urls.py

from django.urls import path
from . import views
from .views import (
    EquipamentoListView,
    EquipamentoDetailView,
    EquipamentoCreateView,
    EquipamentoUpdateView,
    EquipamentoDeleteView,
    # As views AJAX também são importadas através do 'from . import views'
)

# A definição do app_name deve vir aqui
app_name = 'equipamentos'

urlpatterns = [
    # URLs do CRUD de Equipamentos
    path('', views.EquipamentoListView.as_view(), name='equipamento_list'),
    path('novo/', views.EquipamentoCreateView.as_view(), name='equipamento_create'),
    path('<int:pk>/', views.EquipamentoDetailView.as_view(), name='equipamento_detail'),
    path('<int:pk>/editar/', views.EquipamentoUpdateView.as_view(), name='equipamento_update'),
    path('<int:pk>/deletar/', views.EquipamentoDeleteView.as_view(), name='equipamento_delete'),

    # URLS PARA AS NOVAS VIEWS AJAX
    path('ajax/add-tipo-item/', views.add_tipo_item_ajax, name='add_tipo_item_ajax'),
    path('ajax/add-categoria-item/', views.add_categoria_item_ajax, name='add_categoria_item_ajax'),
    path('ajax/add-marca/', views.add_marca_ajax, name='add_marca_ajax'),
    path('ajax/add-status-item/', views.add_status_item_ajax, name='add_status_item_ajax'),
]