# notificacoes/admin.py

from django.contrib import admin
from .models import Evento, TemplateEmail, ConfiguracaoEmail

@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'slug', 'descricao')
    prepopulated_fields = {'slug': ('nome',)} # Magia para preencher o slug automaticamente

@admin.register(TemplateEmail)
class TemplateEmailAdmin(admin.ModelAdmin):
    list_display = ('nome_template', 'evento', 'assunto', 'ativo')
    list_filter = ('evento', 'ativo')
    search_fields = ('nome_template', 'assunto', 'corpo')
    filter_horizontal = ('enviar_para_grupos',) # Melhora a seleção de grupos

@admin.register(ConfiguracaoEmail)
class ConfiguracaoEmailAdmin(admin.ModelAdmin):
    list_display = ('apelido', 'email_host_user', 'ativo')