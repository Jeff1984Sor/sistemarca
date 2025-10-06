from django.contrib import admin

# Register your models here.
# em contas/admin.py

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

# Importa a nossa nova função de sincronização
from casos.microsoft_graph_service import sincronizar_usuarios_azure

# Ação customizada
@admin.action(description='Sincronizar usuários com o Azure AD')
def sincronizar_com_azure(modeladmin, request, queryset):
    """
    Ação do admin que dispara a sincronização de usuários.
    """
    try:
        resultado = sincronizar_usuarios_azure()
        messages.success(request, resultado)
    except Exception as e:
        messages.error(request, f"Ocorreu um erro durante a sincronização: {e}")

# Criamos uma classe de Admin para o modelo User
class UserAdmin(BaseUserAdmin):
    # Adicionamos nossa nova ação à lista de ações disponíveis
    actions = [sincronizar_com_azure]

# Desregistramos o UserAdmin padrão do Django
admin.site.unregister(User)
# E registramos o nosso UserAdmin customizado no lugar
admin.site.register(User, UserAdmin)