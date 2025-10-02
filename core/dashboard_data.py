# core/dashboard_data.py

from django.db.models import Count, Value
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import Concat
from django.db.models.functions import TruncMonth
from casos.models import Caso, Status, Advogado,Tarefa
from dateutil.relativedelta import relativedelta

Usuario = get_user_model()

def get_casos_por_status():
    """
    Agrupa os casos por status e conta quantos existem em cada um.
    Retorna dados formatados para a Chart.js.
    """
    dados = Caso.objects.values('status__nome').annotate(total=Count('id')).order_by('-total')
    
    labels = [item['status__nome'] for item in dados]
    data = [item['total'] for item in dados]
    
    return {'labels': labels, 'data': data}

def get_casos_encerrados_por_mes():
    """
    Conta quantos casos foram encerrados em cada um dos últimos 6 meses.
    """
    hoje = timezone.now().date()
    seis_meses_atras = hoje - timedelta(days=180)

    # 1. Filtra e agrupa os casos por mês
    dados = Caso.objects.filter(data_encerramento__gte=seis_meses_atras)\
                        .annotate(mes_encerramento=TruncMonth('data_encerramento'))\
                        .values('mes_encerramento')\
                        .annotate(total=Count('id'))\
                        .order_by('mes_encerramento')

    # 2. Formata os dados para a Chart.js
    # Converte a data do mês para uma string "Mês/Ano"
    labels = [item['mes_encerramento'].strftime('%b/%Y') for item in dados]
    data = [item['total'] for item in dados]
    
    return {'labels': labels, 'data': data}

def get_tarefas_pendentes_por_responsavel():
    """
    Agrupa todas as tarefas com status 'Pendente' ou 'Em Andamento'
    e conta quantas existem para cada responsável.
    """
    # 1. Filtra apenas as tarefas que não estão concluídas
    dados = Tarefa.objects.filter(status__in=['P', 'A'])\
                          .exclude(responsavel__isnull=True)\
                          .values('responsavel__first_name', 'responsavel__last_name')\
                          .annotate(total=Count('id'))\
                          .order_by('-total')

    # 2. Formata os dados para a Chart.js
    # Junta o primeiro e último nome para criar o label
    labels = [
        f"{item['responsavel__first_name']} {item['responsavel__last_name']}".strip() 
        for item in dados
    ]
    data = [item['total'] for item in dados]
    
    return {'labels': labels, 'data': data}

def get_casos_por_advogado():
    """
    Pega TODOS os advogados e conta quantos casos (related_name='casos') cada um tem.
    """
    # 1. A MÁGICA ACONTECE AQUI:
    # Começamos pelos Advogados, não pelos Casos.
    # Anotamos (annotate) uma nova coluna chamada 'num_casos' que é a contagem
    # de casos relacionados a cada advogado.
    advogados_com_casos = Advogado.objects.annotate(
        num_casos=Count('casos') # Assumindo que o related_name de Caso->Advogado é 'caso'
    ).order_by('-num_casos')

    # 2. Prepara os dados para a Chart.js
    labels = []
    data = []

    for advogado in advogados_com_casos:
        # Pega o nome completo do usuário associado ao advogado
        nome = advogado.user.get_full_name() or advogado.user.username
        labels.append(nome)
        data.append(advogado.num_casos)
    
    return {'labels': labels, 'data': data}


def get_casos_novos_por_cliente_produto():
    """
    Agrupa os casos criados nos últimos 6 meses por Mês e por Cliente+Produto.
    Prepara os dados para um gráfico de barras agrupadas/empilhadas.
    """
    hoje = timezone.now().date()
    seis_meses_atras = (hoje - relativedelta(months=5)).replace(day=1)

    # 1. Busca todos os dados relevantes do banco
    dados_db = Caso.objects.filter(data_entrada_rca__gte=seis_meses_atras)\
        .annotate(mes=TruncMonth('data_entrada_rca'))\
        .values('mes', 'cliente__nome_razao_social', 'produto__nome')\
        .annotate(total=Count('id'))\
        .order_by('mes', 'cliente__nome_razao_social', 'produto__nome')

    # 2. Processa os dados para o formato da Chart.js
    labels_meses = [] # Ex: ['Abr/25', 'Mai/25', ...]
    datasets = {} # Ex: {'Tokio - RCG': [0, 5, 2, ...], 'Tokio - E&O': [3, 0, 8, ...]}
    
    # Gera os labels para os últimos 6 meses
    for i in range(6):
        mes = (hoje - relativedelta(months=5-i)).replace(day=1)
        labels_meses.append(mes.strftime('%b/%y'))

    # Inicializa os datasets com zeros para todos os meses
    for item in dados_db:
        dataset_label = f"{item['cliente__nome_razao_social']} - {item['produto__nome']}"
        if dataset_label not in datasets:
            datasets[dataset_label] = [0] * 6 # Cria uma lista com 6 zeros

    # Preenche os datasets com os valores do banco
    for item in dados_db:
        dataset_label = f"{item['cliente__nome_razao_social']} - {item['produto__nome']}"
        mes_label = item['mes'].strftime('%b/%y')
        
        if mes_label in labels_meses:
            index_do_mes = labels_meses.index(mes_label)
            datasets[dataset_label][index_do_mes] = item['total']

    # 3. Converte o dicionário de datasets para a lista final que a Chart.js espera
    datasets_final = []
    for label, data_values in datasets.items():
        datasets_final.append({
            'label': label,
            'data': data_values,
            # Cores e outras opções podem ser adicionadas aqui
        })
    
    return {'labels': labels_meses, 'datasets': datasets_final}

# Este dicionário é a "ponte" entre o slug do admin e a função em Python
FONTES_DE_DADOS = {
    'casos_por_status': get_casos_por_status,
    'casos_por_advogado': get_casos_por_advogado,
    'tarefas_pendentes_por_responsavel': get_tarefas_pendentes_por_responsavel,
    'casos_encerrados_por_mes': get_casos_encerrados_por_mes,
    'casos_novos_cliente_produto': get_casos_novos_por_cliente_produto,
    # Quando você quiser criar um novo gráfico, você vai:
    # 1. Criar a função aqui (ex: get_tarefas_por_status).
    # 2. Adicionar o slug e a função a este dicionário.
    # 3. Cadastrar o gráfico no admin com o novo slug.
}