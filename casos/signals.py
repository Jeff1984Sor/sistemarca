# casos/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
# Importações dos modelos e serviços necessários
from .models import Caso, RegraWorkflow, Tarefa, FaseWorkflow, HistoricoFase, Timesheet, AndamentoCaso
from notificacoes.servicos import enviar_notificacao

# ==============================================================================
# SINAL 1: AÇÕES NA CRIAÇÃO DE UM NOVO CASO
# ==============================================================================
@receiver(post_save, sender=Caso)
def acoes_novo_caso(sender, instance, created, **kwargs):
    if created:
        # Ação 1: Iniciar o workflow (continua aqui)
        if not instance.fase_atual_workflow:
            try:
                regra = RegraWorkflow.objects.get(cliente=instance.cliente, produto=instance.produto)
                primeira_fase = regra.workflow.fases.order_by('ordem').first()
                if primeira_fase:
                    mudar_de_fase(instance, nova_fase=primeira_fase)
            except RegraWorkflow.DoesNotExist:
                pass

        # Ação 2: Enviar notificação por e-mail (continua aqui)
        contexto = {
            'caso': instance,
            'cliente': instance.cliente,
            'usuario_acao': None
        }
        enviar_notificacao(slug_evento='novo-caso-criado', contexto=contexto)
    """
    Quando um novo caso é criado, esta função dispara duas ações:
    1. Aplica o workflow inicial.
    2. Envia a notificação de "novo caso criado".
    """
    if created:
        # Ação 1: Iniciar o workflow
        if not instance.fase_atual_workflow:
            try:
                regra = RegraWorkflow.objects.get(cliente=instance.cliente, produto=instance.produto)
                primeira_fase = regra.workflow.fases.order_by('ordem').first()
                if primeira_fase:
                    mudar_de_fase(instance, nova_fase=primeira_fase)
            except RegraWorkflow.DoesNotExist:
                pass # Nenhuma regra de workflow encontrada, não faz nada.
    try:
            token = get_sharepoint_token()
            nome_pasta_caso = f"{instance.id} - {instance.titulo_caso}"
            
            pasta_criada = criar_pasta_caso(token, nome_pasta_caso)
            
            if pasta_criada:
                id_pasta_pai = pasta_criada['id']
                # Pega os nomes das subpastas a partir da configuração do Produto
                subpastas = [p.nome_pasta for p in instance.produto.estrutura_pastas.all()]
                if subpastas:
                    criar_subpastas(token, id_pasta_pai, subpastas)
    except Exception as e:
            print(f"ERRO CRÍTICO NA INTEGRAÇÃO COM SHAREPOINT: {e}")
            # Aqui você pode adicionar uma lógica para notificar o admin do erro
        # Ação 2: Enviar notificação por e-mail
    contexto = {
            'caso': instance,
            'cliente': instance.cliente,
            'usuario_acao': None # Ação do sistema
        }
    enviar_notificacao(slug_evento='novo-caso-criado', contexto=contexto)

# ==============================================================================
# SINAL 2: VERIFICAR AVANÇO DE FASE AO CONCLUIR TAREFA
# ==============================================================================
@receiver(post_save, sender=Tarefa)
def verificar_conclusao_da_fase(sender, instance, **kwargs):
    """
    Quando uma tarefa é concluída, verifica se todas as tarefas da fase
    foram finalizadas para então avançar o workflow.
    """
    if instance.status == 'C' and instance.origem_fase_workflow:
        caso = instance.caso
        fase_concluida = instance.origem_fase_workflow

        if caso.fase_atual_workflow != fase_concluida:
            return # Proteção contra execução dupla

        tarefas_restantes = Tarefa.objects.filter(caso=caso, origem_fase_workflow=fase_concluida, status__in=['P', 'A']).exists()

        if not tarefas_restantes:
            ordem_atual = fase_concluida.ordem
            proxima_fase = fase_concluida.workflow.fases.filter(ordem__gt=ordem_atual).order_by('ordem').first()
            mudar_de_fase(caso, nova_fase=proxima_fase)

# ==============================================================================
# SINAL 3: REGISTRAR TIMESHEET NO ANDAMENTO
# ==============================================================================
@receiver(post_save, sender=Timesheet)
@receiver(post_save, sender=Timesheet)
def registrar_timesheet_no_andamento(sender, instance, created, **kwargs):
    """
    Quando um novo Timesheet é criado, cria um registro de Andamento
    correspondente COM TODOS OS DETALHES.
    """
    if created:
        # Formata o tempo de 'timedelta' para 'HH:MM'
        total_seconds = int(instance.tempo.total_seconds())
        horas = total_seconds // 3600
        minutos = (total_seconds % 3600) // 60
        tempo_formatado = f"{horas:02d}:{minutos:02d}"
        
        # Formata a data de execução
        data_execucao_formatada = instance.data_execucao.strftime("%d/%m/%Y")
        
        # Pega o nome do profissional
        nome_profissional = instance.profissional.get_full_name() or instance.profissional.username

        # ==========================================================
        # ===== NOVA DESCRIÇÃO, AGORA COMPLETA E DETALHADA =====
        # ==========================================================
        descricao_andamento = (
            f"--- Timesheet ---\n"
            f"Data da Execução: {data_execucao_formatada}\n"
            f"Profissional: {nome_profissional}\n"
            f"Tempo Gasto: {tempo_formatado}\n"
            f"Descrição: {instance.descricao}"
        )
        
        AndamentoCaso.objects.create(
            caso=instance.caso,
            descricao=descricao_andamento,
            usuario_criacao=instance.profissional,
            # Usa a data do lançamento como a data do andamento
            data_andamento=instance.data_execucao 
        )
# ==============================================================================
# FUNÇÃO AUXILIAR: LÓGICA CENTRAL PARA MUDAR DE FASE
# ==============================================================================
def mudar_de_fase(caso, nova_fase):
    """
    Função central que executa todas as ações ao mudar de fase:
    1. Atualiza o histórico da fase antiga.
    2. Atualiza o status e a fase do caso.
    3. Cria o novo registro de histórico.
    4. Cria as novas tarefas padrão.
    5. Dispara a notificação de avanço de fase.
    """
    fase_antiga = caso.fase_atual_workflow
    
    # Atualiza o histórico da fase antiga (marca a data de saída)
    if fase_antiga:
        HistoricoFase.objects.filter(caso=caso, fase=fase_antiga, data_saida__isnull=True).update(data_saida=timezone.now())

    if nova_fase:
        # Atualiza o caso com a nova fase
        caso.fase_atual_workflow = nova_fase
        if nova_fase.atualiza_status_para:
            caso.status = nova_fase.atualiza_status_para
        caso.save(update_fields=['fase_atual_workflow', 'status'])

        # Cria o novo registro de histórico para a nova fase
        HistoricoFase.objects.create(caso=caso, fase=nova_fase)

        # Cria as novas tarefas para a nova fase
        for tarefa_padrao in nova_fase.tarefas_padrao.all():
            Tarefa.objects.create(
                caso=caso,
                tipo_tarefa=tarefa_padrao.tipo_tarefa,
                responsavel=tarefa_padrao.responsavel_override,
                origem_fase_workflow=nova_fase
            )
        
        # Dispara a notificação de avanço de fase
        contexto = { 'caso': caso, 'fase_antiga': fase_antiga, 'nova_fase': nova_fase }
        enviar_notificacao(slug_evento='avanco-fase-workflow', contexto=contexto)

    else:
        # O workflow terminou
        caso.fase_atual_workflow = None
        caso.save(update_fields=['fase_atual_workflow'])
        # Opcional: Disparar um evento de "workflow concluído"