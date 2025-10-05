# contas/urls.py (ATUALIZADO)

from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import SignUpView, PerfilView, CustomLoginView # Importamos a CustomLoginView

app_name = 'contas'

urlpatterns = [
    # URLs de Autenticação
    path('signup/', SignUpView.as_view(), name='signup'),
    
    # Rota para o login local (usuário/senha)
    # A URL agora é 'login-local/' e o nome é 'login_local'
    path(
        'login-local/', 
        CustomLoginView.as_view(), # Usando a CustomLoginView para passar o 'config' para o template
        name='login_local'
    ),
    
    # Rota de Logout
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # URLs de Perfil e Senha
    path('perfil/', PerfilView.as_view(), name='perfil'),
    
    path(
        'perfil/trocar-senha/', 
        auth_views.PasswordChangeView.as_view(
            template_name='contas/trocar_senha.html',
            success_url=reverse_lazy('contas:trocar_senha_done')
        ), 
        name='trocar_senha'
    ),
    
    path(
        'perfil/trocar-senha/done/', 
        auth_views.PasswordChangeDoneView.as_view(
            template_name='contas/trocar_senha_done.html'
        ), 
        name='trocar_senha_done'
    ),
]