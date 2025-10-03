# notificacoes/admin.py
from django.contrib import admin
from .models import Evento, TemplateEmail, Notificacao

@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'slug', 'ativo')
    prepopulated_fields = {'slug': ('nome',)}

@admin.register(TemplateEmail)
class TemplateEmailAdmin(admin.ModelAdmin):
    list_display = ('evento', 'assunto', 'ativo')
    list_filter = ('evento', 'ativo')

@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ('evento', 'destinatarios', 'data_envio', 'enviado_com_sucesso')
    list_filter = ('evento', 'enviado_com_sucesso')
    readonly_fields = ('evento', 'destinatarios', 'assunto', 'data_envio', 'enviado_com_sucesso')

    def has_add_permission(self, request):
        return False