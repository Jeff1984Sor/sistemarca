from django.urls import path
from . import views

app_name = 'casos'

urlpatterns = [
    path('', views.CasoListView.as_view(), name='caso_list'),
    path('novo/', views.CasoCreateView.as_view(), name='caso_create'),
    path('<int:pk>/', views.CasoDetailView.as_view(), name='caso_detail'),
    path('<int:pk>/editar/', views.CasoUpdateView.as_view(), name='caso_update'),
    
    path('pesquisa/', views.CasoPesquisaView.as_view(), name='caso_pesquisa'),
    path('kanban/', views.KanbanView.as_view(), name='kanban_board'),
    path('exportar/excel/', views.exportar_casos_excel, name='exportar_casos_excel'),
    
    path('acoes/', views.AcaoListView.as_view(), name='acao_list'),
    path('acoes/exportar/', views.exportar_acoes_excel, name='exportar_acoes_excel'),

    path('<int:caso_pk>/add_andamento_caso/', views.add_andamento_caso, name='add_andamento_caso'),
    path('<int:caso_pk>/andamentos/exportar-excel/', views.exportar_andamentos_excel, name='exportar_andamentos_excel'),
    path('<int:caso_pk>/andamentos/exportar-pdf/', views.exportar_andamentos_pdf, name='exportar_andamentos_pdf'),
    path('<int:caso_pk>/add_fluxo_interno/', views.add_fluxo_interno, name='add_fluxo_interno'),
   
    path('<int:caso_pk>/timesheet/exportar-pdf/', views.exportar_timesheet_pdf, name='exportar_timesheet_pdf'),
    path('<int:caso_pk>/timesheet/exportar-excel/', views.exportar_timesheet_excel, name='exportar_timesheet_excel'),
    path('<int:caso_pk>/timesheet/enviar-email/', views.enviar_timesheet_email, name='enviar_timesheet_email'),
    path('<int:caso_pk>/email/enviar/', views.enviar_email_view, name='enviar_email_caso'),
    path('<int:caso_pk>/add_timesheet/', views.add_timesheet, name='add_timesheet'),
    path('timesheet/<int:pk>/editar/', views.LancamentoHorasUpdateView.as_view(), name='timesheet_update'),
    path('timesheet/<int:ts_pk>/delete/', views.delete_timesheet, name='delete_timesheet'),
  
  
    path('<int:caso_pk>/anexos/nova-pasta/', views.criar_pasta_anexo_view, name='criar_pasta_anexo'),
    path('<int:caso_pk>/anexos/upload/', views.upload_arquivo_anexo_view, name='upload_arquivo_anexo'),
    path('<int:caso_pk>/anexos/deletar/<str:item_id>/', views.deletar_item_view, name='deletar_item_anexo'),
    path('anexos/listar/<str:folder_id>/', views.listar_subpasta_ajax, name='listar_subpasta_ajax'),
    path('anexos/preview/<str:item_id>/', views.preview_arquivo_view, name='preview_arquivo'),

    path('ajax/get-campos-produto/', views.get_campos_for_produto_ajax, name='get_campos_for_produto_ajax'),
    path('ajax/update-fase/', views.update_caso_fase_ajax, name='update_caso_fase_ajax'),
    path('ajax/add-status/', views.add_status_ajax, name='add_status_ajax'),
    path('ajax/add-analista/', views.add_analista_ajax, name='add_analista_ajax'),
    path('ajax/add-produto/', views.add_produto_ajax, name='add_produto_ajax'),
    
    path('acao/<int:acao_pk>/executar/<int:opcao_pk>/', views.executar_acao, name='executar_acao_decisao'),
    path('acao/<int:acao_pk>/executar/', views.executar_acao, name='executar_acao_simples'),
    path('acao/<int:acao_instancia_pk>/reabrir/', views.reabrir_acao, name='reabrir_acao'),
    path('acao/<int:acao_instancia_pk>/deletar/', views.deletar_acao, name='deletar_acao'),
]