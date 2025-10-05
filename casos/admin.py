# casos/admin.py (ATUALIZADO E COMPLETO)

from django.contrib import admin
import nested_admin # Se você usa nested_admin, ele precisa estar aqui
from .models import (
    Campo, OpcaoCampo, EstruturaPasta, Produto, RegraCampo, Caso,
    AndamentoCaso, ValorCampoCaso, Advogado, Status, FluxoInterno,
    Timesheet, EmailTemplate, UserSignature, EmailCaso, GraphWebhookSubscription,
    FluxoTrabalho, EtapaFluxo, AcaoEtapa, OpcaoDecisao, InstanciaAcao, HistoricoEtapa,
    DespesaCaso, AcordoCaso, ParcelaAcordo # Nossos novos modelos
)

# ==============================================================================
# INLINES: Seções que aparecerão DENTRO da página de outros modelos
# ==============================================================================

# Mostra as despesas dentro da página do Caso
class DespesaCasoInline(nested_admin.NestedTabularInline): # Usando Nested para compatibilidade
    model = DespesaCaso
    extra = 1 # Começa com 1 formulário em branco para adicionar uma nova despesa
    ordering = ('-data_despesa',)

# Mostra as parcelas dentro da página do Acordo
class ParcelaAcordoInline(nested_admin.NestedTabularInline):
    model = ParcelaAcordo
    # Campos calculados pelo nosso "robô" (sinal), então não devem ser editáveis aqui
    readonly_fields = ('numero_parcela', 'data_vencimento') 
    extra = 0 # Não permite adicionar parcelas manualmente por aqui
    can_delete = False # Impede a exclusão de parcelas individuais

# Mostra os acordos dentro da página do Caso
class AcordoCasoInline(nested_admin.NestedStackedInline):
    model = AcordoCaso
    inlines = [ParcelaAcordoInline] # Aninhamos as parcelas DENTRO do acordo
    extra = 0 # Não começa com um acordo em branco

# Mostra os valores dos campos dinâmicos dentro da página do Caso
class ValorCampoCasoInline(nested_admin.NestedTabularInline):
    model = ValorCampoCaso
    extra = 0

# ==============================================================================
# ADMIN PRINCIPAL: A configuração das páginas de listagem e edição
# ==============================================================================

@admin.register(Caso)
class CasoAdmin(nested_admin.NestedModelAdmin): # Precisa herdar de NestedModelAdmin
    list_display = ('id', 'titulo_caso', 'cliente', 'produto', 'status', 'etapa_atual', 'advogado_responsavel', 'data_entrada_rca')
    list_filter = ('status', 'cliente', 'produto', 'advogado_responsavel')
    search_fields = ('titulo_caso', 'cliente__nome_razao_social')
    date_hierarchy = 'data_entrada_rca'
    
    # AQUI ESTÁ A MÁGICA: Adicionamos as seções de Acordos e Despesas
    inlines = [ValorCampoCasoInline, AcordoCasoInline, DespesaCasoInline]

@admin.register(AcordoCaso)
class AcordoCasoAdmin(nested_admin.NestedModelAdmin):
    list_display = ('id', 'caso', 'data_acordo', 'quantidade_parcelas', 'valor_parcela', 'valor_total')
    inlines = [ParcelaAcordoInline] # Mostra as parcelas aqui também

@admin.register(ParcelaAcordo)
class ParcelaAcordoAdmin(admin.ModelAdmin):
    list_display = ('id', 'acordo', 'numero_parcela', 'data_vencimento', 'situacao')
    list_filter = ('situacao', 'data_vencimento')
    list_editable = ('situacao',) # Permite mudar a situação (quitar) diretamente na lista

# Registrando outros modelos para que apareçam no admin
# (Você pode customizá-los depois se precisar)
admin.site.register(Campo)
admin.site.register(OpcaoCampo)
admin.site.register(EstruturaPasta)
admin.site.register(Produto)
admin.site.register(RegraCampo)
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
admin.site.register(FluxoTrabalho)
admin.site.register(EtapaFluxo)
admin.site.register(AcaoEtapa)
admin.site.register(OpcaoDecisao)
admin.site.register(InstanciaAcao)
admin.site.register(HistoricoEtapa)
admin.site.register(DespesaCaso)