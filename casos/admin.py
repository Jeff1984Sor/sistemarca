# casos/admin.py (COMPLETO E COM O WORKFLOW UNIFICADO)

from django.contrib import admin
import nested_admin
from .models import (
    Campo, OpcaoCampo, EstruturaPasta, Produto, RegraCampo, Caso,
    AndamentoCaso, ValorCampoCaso, Advogado, Status, FluxoInterno,
    Timesheet, EmailTemplate, UserSignature, EmailCaso, GraphWebhookSubscription,
    FluxoTrabalho, EtapaFluxo, AcaoEtapa, OpcaoDecisao, InstanciaAcao, HistoricoEtapa,
    DespesaCaso, AcordoCaso, ParcelaAcordo
)

# ==============================================================================
# INLINES: Seções que aparecerão DENTRO da página de outros modelos
# ==============================================================================

class DespesaCasoInline(nested_admin.NestedTabularInline):
    model = DespesaCaso
    extra = 1
    ordering = ('-data_despesa',)

class ParcelaAcordoInline(nested_admin.NestedTabularInline):
    model = ParcelaAcordo
    readonly_fields = ('numero_parcela', 'data_vencimento')
    extra = 0
    can_delete = False

class AcordoCasoInline(nested_admin.NestedStackedInline):
    model = AcordoCaso
    inlines = [ParcelaAcordoInline]
    extra = 0

class ValorCampoCasoInline(nested_admin.NestedTabularInline):
    model = ValorCampoCaso
    extra = 0
    autocomplete_fields = ['campo']

# ==============================================================================
# ADMIN DO WORKFLOW ANINHADO (ESTRUTURA UNIFICADA)
# ==============================================================================

class OpcaoDecisaoInline(nested_admin.NestedTabularInline):
    model = OpcaoDecisao
    extra = 1
    fk_name = 'acao_etapa'

class AcaoEtapaInline(nested_admin.NestedStackedInline):
    model = AcaoEtapa
    extra = 1
    inlines = [OpcaoDecisaoInline]
    fk_name = 'etapa_fluxo'
    ordering = ['titulo']

class EtapaFluxoInline(nested_admin.NestedStackedInline):
    model = EtapaFluxo
    extra = 1
    inlines = [AcaoEtapaInline]
    fk_name = 'fluxo_trabalho'
    ordering = ['ordem']

@admin.register(FluxoTrabalho)
class FluxoTrabalhoAdmin(nested_admin.NestedModelAdmin):
    list_display = ('nome', 'cliente', 'produto')
    inlines = [EtapaFluxoInline]
    autocomplete_fields = ['cliente', 'produto'] # Adicionado para facilitar

# ==============================================================================
# ADMIN PRINCIPAL: A configuração das páginas de listagem e edição
# ==============================================================================

@admin.register(RegraCampo)
class RegraCampoAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'cliente', 'produto')
    list_filter = ('cliente', 'produto')
    filter_horizontal = ('campos',)
    autocomplete_fields = ['cliente', 'produto']

@admin.register(Caso)
class CasoAdmin(nested_admin.NestedModelAdmin):
    list_display = ('id', 'titulo_caso', 'cliente', 'produto', 'status', 'etapa_atual', 'advogado_responsavel', 'data_entrada_rca')
    list_filter = ('status', 'cliente', 'produto', 'advogado_responsavel')
    search_fields = ('titulo_caso', 'cliente__nome_razao_social')
    date_hierarchy = 'data_entrada_rca'
    autocomplete_fields = ['cliente', 'produto', 'status', 'etapa_atual', 'advogado_responsavel']
    inlines = [ValorCampoCasoInline, AcordoCasoInline, DespesaCasoInline]

@admin.register(AcordoCaso)
class AcordoCasoAdmin(nested_admin.NestedModelAdmin):
    list_display = ('id', 'caso', 'data_acordo', 'quantidade_parcelas', 'valor_parcela', 'valor_total')
    inlines = [ParcelaAcordoInline]
    autocomplete_fields = ['caso']

@admin.register(ParcelaAcordo)
class ParcelaAcordoAdmin(admin.ModelAdmin):
    list_display = ('id', 'acordo', 'numero_parcela', 'data_vencimento', 'situacao')
    list_filter = ('situacao', 'data_vencimento')
    list_editable = ('situacao',)
    autocomplete_fields = ['acordo']

@admin.register(Campo)
class CampoAdmin(admin.ModelAdmin):
    list_display = ('nome_label', 'nome_tecnico', 'tipo_campo')
    search_fields = ('nome_label', 'nome_tecnico')
    prepopulated_fields = {'nome_tecnico': ('nome_label',)}

# ==============================================================================
# REGISTRO DOS OUTROS MODELOS (SEM OS DO WORKFLOW)
# ==============================================================================

# Modelos que não precisam de uma configuração de admin customizada no momento
admin.site.register(OpcaoCampo)
admin.site.register(EstruturaPasta)
admin.site.register(Produto)
admin.site.register(AndamentoCaso)
admin.site.register(ValorCampoCaso)
admin.site.register(Advogado)
admin.site.register(Status)
admin.site.register(FluxoInterno)
admin.site.register(Timesheet)
admin.site.register(EmailTemplate)
admin.site.register(UserSignature)
admin.site.register(EmailCaso)
admin.site.register(GraphWebhookSubscription)
admin.site.register(InstanciaAcao)
admin.site.register(HistoricoEtapa)
admin.site.register(DespesaCaso)

# Os modelos do Workflow (EtapaFluxo, AcaoEtapa, OpcaoDecisao)
# NÃO são registrados aqui porque já estão como "inlines" dentro do FluxoTrabalhoAdmin.