# clientes/views.py

from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q, ProtectedError
from django.contrib import messages
from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from .models import Cliente, Nacionalidade, EstadoCivil, Profissao
from .forms import ClienteForm

# ==============================================================================
# VIEWS DE CRUD (já estavam boas, mantidas e limpas)
# ==============================================================================
class ClienteListView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = 'clientes/cliente_list.html'
    context_object_name = 'clientes'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().order_by('nome_razao_social')
        search_term = self.request.GET.get('q')
        if search_term:
            queryset = queryset.filter(
                Q(nome_razao_social__icontains=search_term) |
                Q(email__icontains=search_term) |
                Q(cnpj__icontains=search_term) |
                Q(cpf__icontains=search_term)
            )
        return queryset

class ClienteCreateView(LoginRequiredMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/cliente_form.html'
    success_url = reverse_lazy('clientes:cliente_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Cadastrar Novo Cliente'
        return context

class ClienteDetailView(LoginRequiredMixin, DetailView):
    model = Cliente
    template_name = 'clientes/cliente_detail.html'
    context_object_name = 'cliente'

class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/cliente_form.html'
    success_url = reverse_lazy('clientes:cliente_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Cliente'
        return context

class ClienteDeleteView(LoginRequiredMixin, DeleteView):
    model = Cliente
    template_name = 'clientes/cliente_confirm_delete.html'
    success_url = reverse_lazy('clientes:cliente_list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(request, f"Cliente '{self.object}' deletado com sucesso.")
            return response
        except ProtectedError:
            messages.error(
                request, 
                f"Não é possível deletar o cliente '{self.object}' porque ele está associado a um ou mais casos."
            )
            return redirect('clientes:cliente_list')

# ==============================================================================
# VIEWS AJAX PARA OS BOTÕES "+" (a parte nova)
# ==============================================================================
def add_generic_ajax(request, model_class):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        if nome and len(nome) > 2:
            obj, created = model_class.objects.get_or_create(nome=nome)
            if created:
                return JsonResponse({'id': obj.id, 'nome': obj.nome})
            else:
                return JsonResponse({'error': 'Este item já existe.'}, status=400)
    return JsonResponse({'error': 'Requisição inválida ou nome muito curto.'}, status=400)

@login_required
def add_nacionalidade_ajax(request):
    return add_generic_ajax(request, Nacionalidade)

@login_required
def add_estado_civil_ajax(request):
    return add_generic_ajax(request, EstadoCivil)

@login_required
def add_profissao_ajax(request):
    return add_generic_ajax(request, Profissao)