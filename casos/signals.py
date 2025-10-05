# casos/signals.py (COM A FUNÇÃO MUDAR_DE_FASE CORRIGIDA)

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

# Importa TODOS os modelos necessários para TODAS as funções
from .models import (
    Caso, Timesheet, AndamentoCaso, AcordoCaso, ParcelaAcordo,
    HistoricoEtapa, InstanciaAcao, EtapaFluxo
)

# A biblioteca python-dateutil é necessária. Lembre-se de adicioná-la ao requirements.txt
try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    raise ImportError(
        "A biblioteca 'python-dateutil' não foi encontrada. "
        "Por favor, instale-a com 'pip install python-dateutil' e adicione ao requirements.txt."
    )


@receiver(post_save, sender=Timesheet)
def registrar_timesheet_no_andamento(sender, instance, created, **kwargs):
    if created:
        AndamentoCaso.objects.create(
            caso=instance.caso,
            data_andamento=instance.data_execucao,
            usuario_criacao=instance.profissional,
            descricao=f"Lançamento de Timesheet realizado ({instance.tempo_formatado}):\n{instance.descricao}"
        )


@receiver(post_save, sender=AcordoCaso, dispatch_uid="criar_ou_atualizar_parcelas_acordo_signal")
def criar_ou_atualizar_parcelas(sender, instance, created, **kwargs):
    if created:
        instance.parcelas.all().delete()
        parcelas_a_criar = []
        for i in range(instance.quantidade_parcelas):
            data_vencimento = instance.data_acordo + relativedelta(months=i)
            parcelas_a_criar.append(
                ParcelaAcordo(
                    acordo=instance,
                    numero_parcela=i + 1,
                    data_vencimento=data_vencimento
                )
            )
        if parcelas_a_criar:
            ParcelaAcordo.objects.bulk_create(parcelas_a_criar)


# ==============================================================================
# FUNÇÃO CENTRAL DO WORKFLOW: MUDAR DE ETAPA (VERSÃO CORRIGIDA)
# ==============================================================================
def mudar_de_etapa(caso: Caso, nova_etapa: EtapaFluxo, usuario_acao=None):
    """
    Função central que executa todas as ações ao mudar de etapa do workflow.
    
    :param caso: A instância do Caso que está mudando de etapa.
    :param nova_etapa: A nova EtapaFluxo para a qual o caso será movido. Pode ser None se o fluxo terminou.
    :param usuario_acao: O usuário que executou a ação que disparou a mudança (opcional).
    """
    etapa_antiga = caso.etapa_atual
    
    # 1. Atualiza o histórico da etapa antiga (marca a data de saída)
    if etapa_antiga:
        HistoricoEtapa.objects.filter(
            caso=caso, 
            etapa=etapa_antiga, 
            data_saida__isnull=True
        ).update(data_saida=timezone.now())

    # 2. Atualiza o caso com a nova etapa e data
    caso.etapa_atual = nova_etapa
    caso.data_entrada_fase = timezone.now() if nova_etapa else None
    
    # (Opcional) Se sua EtapaFluxo tivesse um campo para atualizar o status, a lógica entraria aqui.
    # Ex: if nova_etapa and nova_etapa.atualiza_status_para:
    #         caso.status = nova_etapa.atualiza_status_para
    
    caso.save(update_fields=['etapa_atual', 'data_entrada_fase'])

    if nova_etapa:
        # 3. Cria o novo registro de histórico para a nova etapa
        HistoricoEtapa.objects.create(caso=caso, etapa=nova_etapa)

        # 4. Cria as novas instâncias de ação (tarefas) para a nova etapa
        for acao_modelo in nova_etapa.acoes.all():
            responsavel = None
            if acao_modelo.tipo_responsavel == 'CRIADOR_ACAO' and usuario_acao:
                responsavel = usuario_acao
            elif acao_modelo.tipo_responsavel == 'RESPONSAVEL_CASO':
                responsavel = caso.advogado_responsavel.user if caso.advogado_responsavel else None
            elif acao_modelo.tipo_responsavel == 'USUARIO_FIXO':
                responsavel = acao_modelo.responsavel_fixo
            
            InstanciaAcao.objects.create(
                caso=caso,
                acao_modelo=acao_modelo,
                responsavel=responsavel
            )
        
        # 5. (Pendente) Dispara a notificação de avanço de etapa
        # Aqui entraria a chamada para a função enviar_notificacao, que precisa ser definida
        # contexto = { 'caso': caso, 'etapa_antiga': etapa_antiga, 'nova_etapa': nova_etapa }
        # enviar_notificacao(slug_evento='avanco-etapa-workflow', contexto=contexto)
        print(f"Caso #{caso.id} movido para a etapa: {nova_etapa.nome}")
        
    else:
        # O workflow terminou
        print(f"Workflow do Caso #{caso.id} foi concluído.")
        # (Pendente) Disparar um evento de "workflow concluído"