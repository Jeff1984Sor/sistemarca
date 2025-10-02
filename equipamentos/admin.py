# equipamentos/admin.py
from django.contrib import admin
from .models import Equipamento, TipoItem, CategoriaItem, Marca, StatusItem

# ==============================================================================
# ADMINS PARA MODELOS DE APOIO
# ==============================================================================
@admin.register(TipoItem)
class TipoItemAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(CategoriaItem)
class CategoriaItemAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(StatusItem)
class StatusItemAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

# ==============================================================================
# ADMIN PARA O MODELO PRINCIPAL
# ==============================================================================
@admin.register(Equipamento)
class EquipamentoAdmin(admin.ModelAdmin):
    list_display = (
        'numero_item',
        'tipo_item',
        'marca',
        'modelo',
        'posse_status',
        'posse_usuario'
    )
    list_filter = (
        'tipo_item',
        'categoria_item',
        'marca',
        'status_item',
        'posse_status'
    )
    search_fields = (
        'numero_item',
        'modelo',
        'posse_usuario__username'
    )
    # Se você tiver a ação de exportar, mantenha-a aqui
    # actions = [exportar_para_excel]