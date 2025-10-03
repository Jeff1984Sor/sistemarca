# casos/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
# Importações dos modelos e serviços necessários
from .models import Caso,Timesheet, AndamentoCaso



@receiver(post_save, sender=Timesheet)
def registrar_timesheet_no_andamento(sender, instance, created, **kwargs):
    """
    Toda vez que um novo Timesheet é criado, este signal cria um registro
    correspondente no Andamento do Caso.
    """
    if created:
        # Cria uma única entrada de andamento, usando a data de execução do timesheet
        AndamentoCaso.objects.create(
            caso=instance.caso,
            data_andamento=instance.data_execucao,
            usuario_criacao=instance.profissional,
            descricao=f"Lançamento de Timesheet realizado ({instance.tempo_formatado}):\n{instance.descricao}"
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