# clientes/admin.py
from django.contrib import admin
from .models import Cliente, Nacionalidade, EstadoCivil, Profissao

# Registra os novos modelos de apoio para serem gerenciados no admin
admin.site.register(Nacionalidade)
admin.site.register(EstadoCivil)
admin.site.register(Profissao)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome_razao_social', 'tipo_pessoa', 'email', 'cidade', 'uf')
    list_filter = ('tipo_pessoa', 'cidade', 'uf')
    search_fields = ('nome_razao_social', 'email', 'cnpj', 'cpf')

    # Organiza os campos em abas/seções
    fieldsets = (
        ("Identificação", {
            'fields': ('tipo_pessoa', 'nome_razao_social', 'email', 'telefone')
        }),
        ("Dados de Pessoa Jurídica", {
            'classes': ('collapse', 'pj-fields'), # Classe para o JS
            'fields': ('cnpj', 'inscricao_estadual')
        }),
        ("Dados de Pessoa Física", {
            'classes': ('collapse', 'pf-fields'), # Classe para o JS
            'fields': ('cpf', 'rg', 'nacionalidade', 'estado_civil', 'profissao')
        }),
        ("Endereço", {
            'classes': ('collapse',),
            'fields': ('cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'uf', ('latitude', 'longitude'))
        }),
    )

    # Adiciona o JavaScript para mostrar/esconder os campos
    class Media:
        js = ('clientes/js/admin_cliente_form.js',)