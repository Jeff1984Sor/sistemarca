# casos/models.py

from django.db import models
from django.conf import settings
from clientes.models import Cliente
from datetime import timedelta
from django.db.models import Sum
from django.template import Template, Context # Adicione estas importações no topo
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

# ==============================================================================
# SEÇÃO 1: ESTRUTURA DE CAMPOS DINÂMICOS - O CORAÇÃO DA NOVA LÓGICA
# ==============================================================================

class Campo(models.Model):
    """
    REGISTRO DE TODOS OS CAMPOS POSSÍVEIS.
    """
    TIPO_CHOICES = [
        ('text', 'Texto Curto (CharField)'),
        ('textarea', 'Texto Longo (TextField)'),
        ('number', 'Número Decimal (DecimalField)'),
        ('integer', 'Número Inteiro (IntegerField)'),
        ('date', 'Data (DateField)'),
        ('url', 'Link (URLField)'),
        ('select', 'Lista (Seleção)'),
    ]
    
    # ===== OS CAMPOS QUE ESTAVAM FALTANDO ESTÃO AQUI =====
    nome_label = models.CharField(max_length=100, unique=True, verbose_name="Nome de Exibição do Campo")
    nome_tecnico = models.SlugField(max_length=100, unique=True, help_text="Nome interno do campo (automático)")
    tipo_campo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='text')
    # ====================================================

    class Meta:
        verbose_name = "Campo Customizado"
        verbose_name_plural = "Campos Customizados"
        ordering = ['nome_label']

    def __str__(self):
        return self.nome_label

class OpcaoCampo(models.Model):
    """ Armazena uma opção para um Campo do tipo 'Lista'. """
    campo = models.ForeignKey(Campo, on_delete=models.CASCADE, related_name='opcoes', limit_choices_to={'tipo_campo': 'select'})
    valor = models.CharField(max_length=255)

    def __str__(self):
        return self.valor

    class Meta:
        verbose_name = "Opção de Campo de Lista"
        verbose_name_plural = "Opções de Campos de Lista"
        unique_together = ('campo', 'valor') # Evita opções duplicadas para o mesmo campo
    
    nome_label = models.CharField(max_length=100, unique=True, verbose_name="Nome de Exibição do Campo")
    nome_tecnico = models.SlugField(max_length=100, unique=True, help_text="Nome interno do campo (automático), ex: 'valor_causa'")
    
        
    class Meta:
        verbose_name = "Campo Customizado"
        verbose_name_plural = "Campos Customizados"
        ordering = ['nome_label']

    def __str__(self):
        return self.valor

class EstruturaPasta(models.Model):
    nome_pasta = models.CharField(max_length=100, verbose_name="Nome da Subpasta")
    
    def __str__(self):
        return self.nome_pasta

    class Meta:
        verbose_name = "Estrutura de Pasta"
        verbose_name_plural = "Estruturas de Pasta"

class Produto(models.Model):
    """
    O PRODUTO ESCOLHE QUAIS CAMPOS ELE USA.
    """
    nome = models.CharField(max_length=100, unique=True, verbose_name="Produto / Objeto do Serviço")
    estrutura_pastas = models.ManyToManyField(EstruturaPasta, blank=True, verbose_name="Estrutura de Pastas no SharePoint")
    
    def __str__(self):
        return self.nome

class RegraCampo(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    campos = models.ManyToManyField(Campo, verbose_name="Campos Customizados para esta Regra")

    formato_titulo = models.TextField(
        verbose_name="Formato do Título do Caso",
        blank=True,
        help_text="Defina o formato do título. Use {{ nome_do_campo }} para as variáveis. Ex: Aviso: {{ aviso }} - Segurado: {{ segurado }} - Tomador: {{ tomador }}"
    )

    def __str__(self):
        return f"Regra de Campos para: {self.cliente} + {self.produto}"

    class Meta:
        unique_together = ('cliente', 'produto')
        verbose_name = "Regra de Campos Customizados"
        verbose_name_plural = "Regras de Campos Customizados"

class Caso(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    produto = models.ForeignKey('Produto', on_delete=models.PROTECT)
    etapa_atual = models.ForeignKey('EtapaFluxo', on_delete=models.SET_NULL, null=True, blank=True, related_name='casos_nesta_etapa')
    status = models.ForeignKey('Status', on_delete=models.PROTECT)
    advogado_responsavel = models.ForeignKey('Advogado', on_delete=models.SET_NULL, blank=True, null=True,related_name='casos_responsavel', verbose_name="Advogado Responsável")
    data_entrada_rca = models.DateField(verbose_name="Data de Entrada")
    data_entrada_fase = models.DateTimeField(null=True, blank=True, verbose_name="Data de Entrada na Fase Atual")
    data_encerramento = models.DateField(verbose_name="Data de Encerramento", null=True, blank=True)
    titulo_caso = models.CharField(max_length=512, verbose_name="Título do Caso", blank=True)

    sharepoint_folder_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="ID da Pasta no SharePoint")
    sharepoint_folder_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL da Pasta no SharePoint")
    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.titulo_caso or f"Caso #{self.id}"

    @property
    def dias_na_fase_atual(self):
        if not self.fase_atual_workflow or not self.data_entrada_fase:
            return 0
        delta = timezone.now() - self.data_entrada_fase
        return max(delta.days, 1)

    @property
    def total_horas_trabalhadas(self):
        # Agora somamos o campo 'minutos_gastos'
        total_minutos = self.timesheets.aggregate(total=Sum('minutos_gastos'))['total'] or 0
        
        if total_minutos > 0:
            horas = total_minutos // 60
            minutos = total_minutos % 60
            return f"{horas:02d}:{minutos:02d}"
        return "00:00"
class AndamentoCaso(models.Model):
    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, related_name='andamentos_caso')
    data_andamento = models.DateField(default=timezone.now, verbose_name="Data do Andamento")
    descricao = models.TextField(verbose_name="Descrição")
    usuario_criacao = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        verbose_name="Usuário"
    )

    def __str__(self):
        return f"Andamento em {self.data_andamento.strftime('%d/%m/%Y')} para o Caso #{self.caso.id}"

    class Meta:
        ordering = ['-data_andamento']
        verbose_name = "Andamento do Caso"
        verbose_name_plural = "Andamentos do Caso"


class ValorCampoCaso(models.Model):
    """
    Armazena o VALOR de um Campo dinâmico para um Caso específico.
    """
    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, related_name='valores_dinamicos')
    campo = models.ForeignKey(Campo, on_delete=models.CASCADE)
    valor = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('caso', 'campo')
        verbose_name = "Valor de Campo Customizado"
        verbose_name_plural = "Valores de Campos Customizados"
        ordering = ['campo__nome_label']

    def __str__(self):
        return f"{self.campo.nome_label}: {self.valor or ''}"

# ==============================================================================
# SEÇÃO 2: MODELOS DE APOIO E WORKFLOW (TODOS OS SEUS OUTROS MODELOS)
# Estes modelos são mantidos como estavam, pois são essenciais para o sistema.
# ==============================================================================

class Advogado(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Usuário do Sistema")
    def __str__(self): return self.user.get_full_name() or self.user.username

class Status(models.Model):
    nome = models.CharField(max_length=50, unique=True)
    def __str__(self): return self.nome
    class Meta:
        verbose_name_plural = "Status"

class FluxoInterno(models.Model):
    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, related_name='fluxo_interno') # related_name mudou
    data_fluxo = models.DateField(verbose_name="Data") # Renomeado de data_andamento
    descricao = models.TextField(verbose_name="Descrição")
    usuario_criacao = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Usuário")
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Registro de Fluxo Interno em {self.data_fluxo.strftime('%d/%m/%Y')} para o Caso #{self.caso.id}"

    class Meta:
        ordering = ['-data_fluxo', '-data_cadastro']
        verbose_name = "Fluxo Interno"
        verbose_name_plural = "Fluxo Interno"




class Timesheet(models.Model):
    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, related_name='timesheets')
    data_execucao = models.DateField(verbose_name="Data de Execução")
    profissional = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="Profissional")
    
    # --- A GRANDE MUDANÇA ESTÁ AQUI ---
    minutos_gastos = models.PositiveIntegerField(default=0, verbose_name="Tempo Gasto (em minutos)")
    
    descricao = models.TextField(verbose_name="Descrição da Atividade")
    data_cadastro = models.DateTimeField(auto_now_add=True)

    @property
    def tempo_formatado(self):
        """Retorna o tempo no formato HH:MM para exibição."""
        if not self.minutos_gastos:
            return "00:00"
        horas = self.minutos_gastos // 60
        minutos = self.minutos_gastos % 60
        return f"{horas:02d}:{minutos:02d}"

    def __str__(self):
        return f"Lançamento de {self.profissional.username} em {self.data_execucao.strftime('%d/%m/%Y')}"

    class Meta:
        ordering = ['-data_execucao']


class EmailTemplate(models.Model):
    nome = models.CharField(max_length=100, unique=True, help_text="Nome do modelo para identificação interna.")
    assunto = models.CharField(max_length=255, help_text="Assunto do e-mail. Pode usar variáveis como {{ caso.titulo_caso }}.")
    corpo = models.TextField(help_text="Corpo do e-mail em HTML. Use variáveis como {{ caso.cliente.nome_razao_social }} ou {{ user.get_full_name }}.")

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Modelo de E-mail"
        verbose_name_plural = "Modelos de E-mail"


class UserSignature(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assinaturas")
    nome = models.CharField(max_length=100, help_text="Nome da assinatura (ex: 'Padrão', 'Simplificada').")
    corpo_html = models.TextField(verbose_name="Assinatura em HTML")
    is_default = models.BooleanField(default=False, verbose_name="É a assinatura padrão?")

    def __str__(self):
        return f"{self.usuario.username} - {self.nome}"

    class Meta:
        verbose_name = "Assinatura de Usuário"
        verbose_name_plural = "Assinaturas de Usuários"


class EmailCaso(models.Model):
    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, related_name="emails")
    microsoft_message_id = models.CharField(max_length=255, unique=True, help_text="ID único do e-mail na Microsoft Graph.")
    de = models.CharField(max_length=255, verbose_name="De")
    para = models.TextField(verbose_name="Para")
    assunto = models.CharField(max_length=255, verbose_name="Assunto")
    preview = models.CharField(max_length=255, verbose_name="Pré-visualização do corpo")
    corpo_html = models.TextField(verbose_name="Corpo do E-mail")
    data_envio = models.DateTimeField(verbose_name="Data de Envio/Recebimento")
    is_sent = models.BooleanField(default=False, help_text="True se foi enviado do sistema, False se foi recebido.")
    
    # Para encadear conversas
    thread_id = models.CharField(max_length=255, blank=True, null=True, help_text="ID da thread de conversação.")

    def __str__(self):
        return f"E-mail para o Caso #{self.caso.id}: {self.assunto}"

    class Meta:
        ordering = ['-data_envio']
        verbose_name = "E-mail do Caso"
        verbose_name_plural = "E-mails dos Casos"

class GraphWebhookSubscription(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subscription_id = models.CharField(max_length=255, unique=True)
    expiration_datetime = models.DateTimeField()

    def __str__(self):
        return f"Webhook for {self.user.username}"
    


class FluxoTrabalho(models.Model):
    nome = models.CharField(max_length=200, unique=True)
    descricao = models.TextField(blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Fluxo de Trabalho"
        verbose_name_plural = "1. Fluxos de Trabalho" # O '1.' ajuda a ordenar no Admin
        unique_together = ('cliente', 'produto')

class EtapaFluxo(models.Model):
    fluxo_trabalho = models.ForeignKey(FluxoTrabalho, on_delete=models.CASCADE, related_name='etapas')
    nome = models.CharField(max_length=100)
    ordem = models.PositiveIntegerField(default=0)
    sla_dias = models.PositiveIntegerField(default=0, verbose_name="SLA (dias)", help_text="Prazo ideal em dias para esta etapa. 0 para sem SLA.")

    def __str__(self):
        return f"{self.fluxo_trabalho.nome} - Etapa {self.ordem}: {self.nome}"

    class Meta:
        ordering = ['fluxo_trabalho', 'ordem']
        unique_together = ('fluxo_trabalho', 'ordem')
        verbose_name = "Etapa do Fluxo"
        verbose_name_plural = "2. Etapas dos Fluxos"

class AcaoEtapa(models.Model):
    PRAZO_CHOICES = [
        ('corridos', 'Dias Corridos'),
        ('uteis', 'Dias Úteis'),
    ]
    TIPO_RESPONSAVEL_CHOICES = [
        ('CRIADOR_ACAO', 'Usuário que Concluiu a Ação Anterior'),
        ('RESPONSAVEL_CASO', 'Responsável Pelo Caso'),
        ('USUARIO_FIXO', 'Usuário Fixo (especificar abaixo)'),
    ]

    etapa_fluxo = models.ForeignKey(EtapaFluxo, on_delete=models.CASCADE, related_name='acoes')
    titulo = models.CharField(max_length=200, verbose_name="Título da Ação/Tarefa")
    instrucoes = models.TextField(blank=True, verbose_name="Instruções Padrão")
    
    prazo_dias = models.PositiveIntegerField(
        default=0, 
        verbose_name="Prazo (em dias)",
        help_text="Número de dias para concluir a tarefa após sua criação. 0 para sem prazo."
    )
    tipo_prazo = models.CharField(
        max_length=10, 
        choices=PRAZO_CHOICES, 
        default='uteis', 
        verbose_name="Tipo de Prazo"
    )
    
    tipo_responsavel = models.CharField(
        max_length=20,
        choices=TIPO_RESPONSAVEL_CHOICES,
        default='CRIADOR_ACAO',
        verbose_name="Atribuir Responsável Para"
    )
    
    responsavel_fixo = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Usuário Fixo",
        help_text="Usado apenas se o tipo acima for 'Usuário Fixo'."
    )

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = "Ação da Etapa"
        verbose_name_plural = "3. Ações das Etapas"

class OpcaoDecisao(models.Model):
    acao_etapa = models.ForeignKey(AcaoEtapa, on_delete=models.CASCADE, related_name='opcoes_decisao')
    label_do_botao = models.CharField(max_length=100, verbose_name="Texto do Botão de Decisão")
    
    # Ações de Workflow
    avancar_proxima_etapa = models.BooleanField(default=False, verbose_name="Avançar para Próxima Etapa?")
    mudar_etapa_para = models.ForeignKey(EtapaFluxo, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Mover para a Etapa Específica")
    
    # Ações de Tarefa
    criar_nova_acao = models.ForeignKey(AcaoEtapa, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Criar Nova Ação/Tarefa", related_name='+')
    aguardar_dias = models.PositiveIntegerField(default=0, verbose_name="Aguardar (dias)", help_text="Cria uma tarefa de lembrete para o futuro. 0 para desativado.")
    
    # Ações de Dados e Comunicação
    atualizar_status_caso = models.ForeignKey(Status, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Atualizar Status do Caso para")
    enviar_email = models.BooleanField(default=False, verbose_name="Enviar E-mail Automático?")
    modelo_email = models.ForeignKey('notificacoes.TemplateEmail', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Usar Modelo de E-mail")
    # Adicionar campo para destinatários depois, se necessário

    def __str__(self):
        return f"Opção '{self.label_do_botao}' para a ação '{self.acao_etapa.titulo}'"
    
    class Meta:
        verbose_name = "Opção de Decisão"
        verbose_name_plural = "4. Opções de Decisão"


class InstanciaAcao(models.Model):
    STATUS_CHOICES = [('P', 'Pendente'), ('C', 'Concluída')]

    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, related_name='acoes_em_andamento')
    acao_modelo = models.ForeignKey(AcaoEtapa, on_delete=models.PROTECT, verbose_name="Ação a ser executada")
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    descricao_conclusao = models.TextField(blank=True)
    prazo_final = models.DateTimeField(null=True, blank=True, verbose_name="Prazo Final")

    def __str__(self):
        return f"Ação '{self.acao_modelo.titulo}' para o Caso #{self.caso.id}"

    class Meta:
        verbose_name = "Instância de Ação"
        verbose_name_plural = "Instâncias de Ações"

class HistoricoEtapa(models.Model):
    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, related_name='historico_etapas')
    etapa = models.ForeignKey(EtapaFluxo, on_delete=models.PROTECT)
    data_entrada = models.DateTimeField(auto_now_add=True)
    data_saida = models.DateTimeField(null=True, blank=True)

    @property
    def tempo_na_etapa(self):
        if self.data_saida:
            delta = self.data_saida - self.data_entrada
            return f"{delta.days} dias" if delta.days > 0 else "Menos de 1 dia"
        return "Em andamento"

    def __str__(self):
        return f"Caso #{self.caso.id} na etapa '{self.etapa.nome}'"
    
    class Meta:
        ordering = ['-data_entrada']
        verbose_name = "Histórico de Etapa"
        verbose_name_plural = "Históricos de Etapas"

