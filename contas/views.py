# contas/views.py

from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages

from .models import Perfil
from .forms import CustomUserCreationForm, UserUpdateForm, PerfilUpdateForm


class SignUpView(generic.CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'contas/signup.html'

class CustomLoginView(LoginView):
    template_name = 'contas/login.html'
    authentication_form = AuthenticationForm

class PerfilView(LoginRequiredMixin, View):
    
    def get(self, request, *args, **kwargs):
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