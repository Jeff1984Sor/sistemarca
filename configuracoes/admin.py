# configuracoes/admin.py
from django.contrib import admin
from .models import LogoConfig, Modulo, Tema, Grafico, ConfiguracaoGlobal

@admin.register(LogoConfig)
class LogoConfigAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'ativo', 'logo')
    list_filter = ('ativo',)

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['help_text'] = "Atenção: Apenas um logo pode ser marcado como 'Ativo'. Ao ativar um novo logo, os outros serão desativados automaticamente."
        return super().add_view(request, form_url, extra_context)

@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    list_display = ('nome', 'slug', 'ativo')
    list_editable = ('ativo',)
    search_fields = ('nome', 'slug')
    prepopulated_fields = {'slug': ('nome',)}
    # filter_horizontal é a melhor interface para ManyToManyFields
    filter_horizontal = ('grupos_permitidos',)

@admin.register(Tema)
class TemaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo')
    fieldsets = (
        (None, {'fields': ('nome', 'ativo')}),
        ('Cores', {'fields': ('cor_primaria', 'cor_sucesso', 'cor_perigo', 'cor_barra_nav')}),
        ('Fontes', {'fields': ('fonte_principal',)}),
    )

@admin.register(Grafico)
class GraficoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo_grafico', 'fonte_dados_slug', 'ativo_no_dashboard', 'ordem')
    list_filter = ('tipo_grafico', 'ativo_no_dashboard')
    
    # Permite que você edite a ordem e se o gráfico está ativo diretamente na lista
    list_editable = ('ativo_no_dashboard', 'ordem')
    
    fieldsets = (
        (None, {
            'fields': ('nome', 'ativo_no_dashboard', 'ordem')
        }),
        ('Configuração do Gráfico', {
            'fields': ('tipo_grafico', 'fonte_dados_slug'),
            'description': ("<strong>Fonte de Dados</strong> deve corresponder a um 'slug' definido no código. "
                          "Exemplos: 'casos_por_status', 'casos_por_advogado', 'casos_por_origem'.")
        }),
    )

@admin.register(ConfiguracaoGlobal)
class ConfiguracaoGlobalAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'habilitar_login_microsoft', 'habilitar_robo_modulos')
    
    # Este método impede que alguém crie uma SEGUNDA linha de configurações
    def has_add_permission(self, request):
        return not ConfiguracaoGlobal.objects.exists()

    # Este método impede que alguém delete a linha de configurações
    def has_delete_permission(self, request, obj=None):
        return False