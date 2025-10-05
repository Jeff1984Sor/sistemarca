# contas/urls.py (VERSÃO FINAL E LIMPA)

from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import SignUpView, PerfilView, CustomLoginView

app_name = 'contas'

urlpatterns = [
    # URLs de Autenticação
    path('signup/', SignUpView.as_view(), name='signup'),
    
    path(
        'login-local/', 
        CustomLoginView.as_view(), 
        name='login_local'
    ),
    
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