# equipamentos/views.py
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Equipamento
from .forms import EquipamentoForm
from .models import TipoItem, CategoriaItem, Marca, StatusItem
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse


class EquipamentoListView(LoginRequiredMixin, ListView):
    model = Equipamento
    template_name = 'equipamentos/equipamento_list.html'
    context_object_name = 'equipamentos'
    paginate_by = 15
    # Removemos o get_queryset para usar o padrão (listar tudo)
    ordering = ['numero_item']

class EquipamentoCreateView(LoginRequiredMixin, CreateView):
    model = Equipamento
    form_class = EquipamentoForm
    template_name = 'equipamentos/equipamento_form.html'
    success_url = reverse_lazy('equipamentos:equipamento_list')
    # Removemos o form_valid, pois não precisamos mais associar a empresa

# Faça o mesmo para DetailView, UpdateView e DeleteView: remova o get_queryset
class EquipamentoDetailView(LoginRequiredMixin, DetailView):
    model = Equipamento
    template_name = 'equipamentos/equipamento_detail.html'

class EquipamentoUpdateView(LoginRequiredMixin, UpdateView):
    model = Equipamento
    form_class = EquipamentoForm
    template_name = 'equipamentos/equipamento_form.html'
    success_url = reverse_lazy('equipamentos:equipamento_list')

class EquipamentoDeleteView(LoginRequiredMixin, DeleteView):
    model = Equipamento
    template_name = 'equipamentos/equipamento_confirm_delete.html'
    success_url = reverse_lazy('equipamentos:equipamento_list')

# ==========================================================
# VIEWS AJAX PARA OS BOTÕES "+"
# Adicione este bloco de código ao seu views.py
# ==========================================================

# Função genérica para não repetir código
def add_generic_ajax(request, model_class):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        if nome:
            obj, created = model_class.objects.get_or_create(nome=nome)
            return JsonResponse({'id': obj.id, 'nome': obj.nome})
    return JsonResponse({'error': 'Requisição inválida'}, status=400)

@login_required
def add_tipo_item_ajax(request):
    return add_generic_ajax(request, TipoItem)

@login_required
def add_categoria_item_ajax(request):
    return add_generic_ajax(request, CategoriaItem)

@login_required
def add_marca_ajax(request):
    return add_generic_ajax(request, Marca)

@login_required
def add_status_item_ajax(request):
    return add_generic_ajax(request, StatusItem)