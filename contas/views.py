# contas/views.py (ARRUMADO E COMPLETO)

from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages

# Importa os modelos e formulários necessários
from .models import Perfil
from .forms import CustomUserCreationForm, UserUpdateForm, PerfilUpdateForm
from configuracoes.models import ConfiguracaoGlobal


# View para a página de login customizada
class CustomLoginView(LoginView):
    # Usa o formulário de autenticação padrão do Django
    authentication_form = AuthenticationForm
    # Aponta para o seu template de login bonito
    template_name = 'contas/login.html'
    
    def get_context_data(self, **kwargs):
        # Pega o contexto padrão da LoginView (incluindo o 'form')
        context = super().get_context_data(**kwargs)
        
        # Tenta buscar o objeto de configuração e adicioná-lo ao contexto
        try:
            # Usar get_or_create é seguro, pois cria o objeto se ele não existir
            config, created = ConfiguracaoGlobal.objects.get_or_create(pk=1)
            context['config'] = config
        except Exception:
            # Se der qualquer erro (ex: durante o primeiro migrate), não quebra o site
            context['config'] = None
            
        return context

# View para a página de criação de novos usuários
class SignUpView(generic.CreateView):
    form_class = CustomUserCreationForm
    # Redireciona para o login local após o cadastro bem-sucedido
    success_url = reverse_lazy('contas:login_local') 
    template_name = 'contas/signup.html'

# View para a página de edição de perfil do usuário
class PerfilView(LoginRequiredMixin, View):
    
    def get(self, request, *args, **kwargs):
        # Garante que o perfil do usuário exista antes de tentar usá-lo
        perfil_obj, created = Perfil.objects.get_or_create(user=request.user)
        
        user_form = UserUpdateForm(instance=request.user)
        perfil_form = PerfilUpdateForm(instance=perfil_obj)
        
        context = {
            'user_form': user_form,
            'perfil_form': perfil_form
        }
        return render(request, 'contas/perfil.html', context)

    def post(self, request, *args, **kwargs):
        perfil_obj, created = Perfil.objects.get_or_create(user=request.user)
        
        user_form = UserUpdateForm(request.POST, instance=request.user)
        perfil_form = PerfilUpdateForm(request.POST, request.FILES, instance=perfil_obj)

        if user_form.is_valid() and perfil_form.is_valid():
            user_form.save()
            perfil_form.save()
            messages.success(request, 'Seu perfil foi atualizado com sucesso!')
            return redirect('contas:perfil')

        context = {
            'user_form': user_form,
            'perfil_form': perfil_form
        }
        messages.error(request, 'Por favor, corrija os erros abaixo.')
        return render(request, 'contas/perfil.html', context)