from django.contrib import admin
from .models import (
    Caso, Produto, Campo, ValorCampoCaso, FluxoInterno, Tarefa, 
    Timesheet, TipoTarefa, FaseWorkflow, Advogado, Status, Analista, 
    Cliente, Workflow, AndamentoCaso, EstruturaPasta, 
    EmailTemplate, UserSignature, EmailCaso
)

# Não precisamos mais dos 'admin.site.register' simples aqui,
# pois usaremos os decoradores que são mais organizados.

@admin.register(Caso)
class CasoAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo_caso', 'cliente', 'produto', 'status', 'data_entrada_rca')
    search_fields = ('titulo_caso', 'id')
    list_filter = ('cliente', 'produto', 'status')

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(Campo)
class CampoAdmin(admin.ModelAdmin):
    list_display = ('nome_label', 'nome_tecnico', 'tipo_campo')
    search_fields = ('nome_label', 'nome_tecnico')

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('nome', 'assunto')
    search_fields = ('nome', 'assunto', 'corpo')

@admin.register(UserSignature)
class UserSignatureAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'nome', 'is_default')
    list_filter = ('usuario',)
    search_fields = ('usuario__username', 'nome')

@admin.register(EmailCaso)
class EmailCasoAdmin(admin.ModelAdmin):
    list_display = ('caso', 'assunto', 'de', 'para', 'data_envio', 'is_sent')
    list_filter = ('caso', 'is_sent', 'data_envio')
    search_fields = ('assunto', 'de', 'para', 'corpo_html')
    readonly_fields = ('caso', 'microsoft_message_id', 'de', 'para', 'assunto', 'preview', 'corpo_html', 'data_envio', 'is_sent', 'thread_id')
    
    def has_add_permission(self, request):
        return False

# Registra os modelos que não precisam de uma classe Admin customizada
admin.site.register(ValorCampoCaso)
admin.site.register(FluxoInterno)
admin.site.register(Tarefa)
admin.site.register(Timesheet)
admin.site.register(TipoTarefa)
admin.site.register(FaseWorkflow)
admin.site.register(Advogado)
admin.site.register(Status)
admin.site.register(Analista)
admin.site.register(Workflow)
admin.site.register(AndamentoCaso)
admin.site.register(EstruturaPasta)