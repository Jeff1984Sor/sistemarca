# core/views.py (CORRIGIDO E FINAL)

import calendar
import json
from collections import defaultdict
from datetime import date
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone

from casos.models import Caso, InstanciaAcao, Status
from django.contrib.auth import get_user_model

User = get_user_model()

def get_casos_por_status():
    dados_status = Status.objects.annotate(total_casos=Count('caso')).filter(total_casos__gt=0)
    labels = [s.nome for s in dados_status]
    data = [s.total_casos for s in dados_status]
    return {"labels": labels, "data": data}

# ===== A CORREÇÃO ESTÁ AQUI =====
def get_casos_por_advogado():
    """Retorna dados para o gráfico de barras de casos por advogado."""
    
    # Filtramos para pegar apenas usuários que TÊM um objeto Advogado relacionado.
    # O '__isnull=False' garante que a consulta não quebre para usuários sem o relacionamento.
    dados_advogado = User.objects.filter(
        advogado__isnull=False
    ).annotate(
        total_casos=Count('advogado__casos_responsavel')
    ).filter(total_casos__gt=0).order_by('-total_casos')

    labels = [a.get_full_name() or a.username for a in dados_advogado]
    data = [a.total_casos for a in dados_advogado]

    return {"labels": labels, "data": data}
# =================================

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "core/home.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        hoje = timezone.now().date()
        ano_atual = hoje.year
        usuario_logado = self.request.user

        tarefas_para_hoje = InstanciaAcao.objects.filter(
            responsavel=usuario_logado,
            status='P',
            prazo_final__date=hoje
        ).select_related('caso', 'acao_modelo').order_by('prazo_final')
        
        context['tarefas_para_hoje'] = tarefas_para_hoje
        
        if hoje.month <= 6:
            mes_inicial_semestre, mes_final_semestre = 1, 6
        else:
            mes_inicial_semestre, mes_final_semestre = 7, 12
        
        inicio_semestre = date(hoje.year, mes_inicial_semestre, 1)
        
        contagem_db_semestre = Caso.objects.filter(
            data_encerramento__isnull=False, data_encerramento__gte=inicio_semestre
        ).annotate(mes=TruncMonth('data_encerramento')).values('mes').annotate(total=Count('id'))
        
        contagem_por_mes_semestre = {item['mes']: item['total'] for item in contagem_db_semestre}
        
        placar_da_meta = []
        total_semestre = 0
        for num_mes in range(mes_inicial_semestre, mes_final_semestre + 1):
            mes_atual = date(hoje.year, num_mes, 1)
            total_do_mes = contagem_por_mes_semestre.get(mes_atual, 0)
            placar_da_meta.append({'mes_str': mes_atual.strftime('%B').capitalize(), 'total': total_do_mes})
            total_semestre += total_do_mes
        context['placar_da_meta'] = placar_da_meta
        context['total_semestre'] = total_semestre

        casos_do_ano = Caso.objects.filter(data_entrada_rca__year=ano_atual).select_related('cliente', 'produto')
        dados_matriz = defaultdict(lambda: defaultdict(int))
        chaves_unicas = set()
        for caso in casos_do_ano:
            if caso.cliente and caso.produto and caso.data_entrada_rca:
                chave = f"{caso.cliente.nome_razao_social} - {caso.produto.nome}"
                mes = caso.data_entrada_rca.month
                dados_matriz[chave][mes] += 1
                chaves_unicas.add(chave)
        
        tabela_entradas = []
        totais_por_mes = [0] * 12
        for chave in sorted(list(chaves_unicas)):
            linha = {'chave': chave, 'valores_mes': []}
            soma_linha = 0
            for mes_num in range(1, 13):
                valor = dados_matriz[chave].get(mes_num, 0)
                linha['valores_mes'].append(valor)
                soma_linha += valor
                totais_por_mes[mes_num - 1] += valor
            linha['total_linha'] = soma_linha
            tabela_entradas.append(linha)
        
        context['tabela_entradas'] = tabela_entradas
        context['nomes_meses'] = [calendar.month_abbr[i].capitalize() for i in range(1, 13)]
        context['totais_por_mes'] = totais_por_mes
        context['total_geral_entradas'] = sum(totais_por_mes)
        context['ano_atual'] = ano_atual
        
        context['dados_grafico_status_json'] = json.dumps(get_casos_por_status())
        context['dados_grafico_advogado_json'] = json.dumps(get_casos_por_advogado())
        
        return context