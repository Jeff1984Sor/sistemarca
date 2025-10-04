# contas/urls.py (ATUALIZADO)

from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import SignUpView, PerfilView # Removemos a importação de CustomLoginView

app_name = 'contas'

urlpatterns = [
    # URLs de Autênticação

    # Rota para o usuário criar uma nova conta (se aplicável)
    path('signup/', SignUpView.as_view(), name='signup'),
    
    # Rota de Login - ESTA É A MUDANÇA PRINCIPAL
    # Estamos usando a LoginView padrão do Django e dizendo a ela para usar
    # nosso novo template com as duas opções de login.
    path(
        'login/', 
        auth_views.LoginView.as_view(
            template_name='contas/login.html'
        ), 
        name='login'
    ),
    
    # Rota de Logout - Já estava correta
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # URLs de Perfil e Senha - Já estavam corretas
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