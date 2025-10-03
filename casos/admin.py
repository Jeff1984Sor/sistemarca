import nested_admin
from django.contrib import admin
from .models import (
    Caso, Produto, Campo, ValorCampoCaso, FluxoInterno, Timesheet, 
    Advogado, Status, Cliente, AndamentoCaso, EstruturaPasta, 
    EmailTemplate, UserSignature, EmailCaso,
    FluxoTrabalho, EtapaFluxo, AcaoEtapa, OpcaoDecisao, InstanciaAcao, HistoricoEtapa
)

class OpcaoDecisaoInline(nested_admin.NestedStackedInline):
    model = OpcaoDecisao
    extra = 1
    fk_name = 'acao_etapa'
    fieldsets = (
        (None, {'fields': ('label_do_botao',)}),
        ('Ações de Workflow & Ações', {'classes': ('collapse',), 'fields': ('avancar_proxima_etapa', 'mudar_etapa_para', 'criar_nova_acao', 'aguardar_dias')}),
        ('Ações de Dados & Comunicação', {'classes': ('collapse',), 'fields': ('atualizar_status_caso', 'enviar_email', 'modelo_email')}),
    )

class AcaoEtapaInline(nested_admin.NestedStackedInline):
    model = AcaoEtapa
    extra = 1
    inlines = [OpcaoDecisaoInline]
    fk_name = 'etapa_fluxo'
    fieldsets = (
        ('Definição da Ação', {'fields': ('titulo', 'instrucoes')}),
        ('Prazo', {'fields': (('prazo_dias', 'tipo_prazo'),)}),
        ('Atribuição de Responsável', {'fields': ('tipo_responsavel', 'responsavel_fixo')}),
    )

class EtapaFluxoInline(nested_admin.NestedTabularInline):
    model = EtapaFluxo
    extra = 1
    inlines = [AcaoEtapaInline]
    fk_name = 'fluxo_trabalho'
    ordering = ('ordem',)

@admin.register(FluxoTrabalho)
class FluxoTrabalhoAdmin(nested_admin.NestedModelAdmin):
    list_display = ('nome', 'cliente', 'produto')
    inlines = [EtapaFluxoInline]
    fieldsets = ((None, {'fields': ('nome', 'descricao', ('cliente', 'produto'))}),)

@admin.register(Caso)
class CasoAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo_caso', 'cliente', 'produto', 'status', 'etapa_atual')
    search_fields = ('titulo_caso', 'id')
    list_filter = ('cliente', 'produto', 'status', 'etapa_atual')

# --- REGISTRO DOS OUTROS MODELOS ---
# (Pode adicionar @admin.register para cada um se quiser customizar)
admin.site.register(Produto)
admin.site.register(Campo)
admin.site.register(ValorCampoCaso)
admin.site.register(FluxoInterno)
admin.site.register(Timesheet)
admin.site.register(Advogado)
admin.site.register(Status)
admin.site.register(AndamentoCaso)
admin.site.register(EstruturaPasta)
admin.site.register(EmailTemplate)
admin.site.register(UserSignature)
admin.site.register(EmailCaso)
admin.site.register(InstanciaAcao)
admin.site.register(HistoricoEtapa)