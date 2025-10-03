# core/dashboard_data.py

from django.db.models import Count
from collections import defaultdict
import json

# Removido: 'Tarefa' da lista de imports
from casos.models import Caso, Status, Advogado
from django.contrib.auth import get_user_model

User = get_user_model()

def get_casos_por_status():
    """Retorna dados para o gráfico de pizza de casos por status."""
    dados_status = Status.objects.annotate(total_casos=Count('caso')).filter(total_casos__gt=0)
    labels = [s.nome for s in dados_status]
    data = [s.total_casos for s in dados_status]
    
    # Você pode definir uma paleta de cores aqui se quiser
    # cores = ['#FF6384', '#36A2EB', '#FFCE56', ...]

    return {"labels": labels, "data": data}


def get_casos_por_advogado():
    """Retorna dados para o gráfico de barras de casos por advogado."""
    dados_advogado = Advogado.objects.annotate(total_casos=Count('casos_responsavel')).filter(total_casos__gt=0).order_by('-total_casos')
    labels = [a.user.get_full_name() or a.user.username for a in dados_advogado]
    data = [a.total_casos for a in dados_advogado]

    return {"labels": labels, "data": data}

# A lógica de tarefas será reconstruída com os novos modelos de workflow.
# def get_tarefas_por_responsavel():
#     # ... código antigo comentado ...
#     return {}