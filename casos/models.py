# casos/models.py

from django.db import models
from django.conf import settings
from clientes.models import Cliente
from datetime import timedelta
from django.db.models import Sum
from django.template import Template, Context # Adicione estas importações no topo
from django.conf import settings
from django.utils import timezone

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
class HistoricoFase(models.Model):
    caso = models.ForeignKey('Caso', on_delete=models.CASCADE, related_name='historico_fases')
    fase = models.ForeignKey('FaseWorkflow', on_delete=models.PROTECT)
    data_entrada = models.DateTimeField(auto_now_add=True)
    data_saida = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Caso #{self.caso.id} na fase '{self.fase.nome}'"

    @property
    def tempo_na_fase(self):
        """Calcula o tempo gasto na fase em dias."""
        # Se a fase ainda não terminou, calcula até agora.
        data_final = self.data_saida or timezone.now()
        
        delta = data_final - self.data_entrada
        dias = delta.days
        
        # Garante que o mínimo seja sempre 1 dia
        return max(dias, 1)

    class Meta:
        ordering = ['data_entrada']

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
    status = models.ForeignKey('Status', on_delete=models.PROTECT)
    advogado_responsavel = models.ForeignKey('Advogado', on_delete=models.SET_NULL, blank=True, null=True,related_name='casos', verbose_name="Advogado Responsável")
    analista = models.ForeignKey('Analista', on_delete=models.SET_NULL, blank=True, null=True)
    data_entrada_rca = models.DateField(verbose_name="Data de Entrada")
    fase_atual_workflow = models.ForeignKey('FaseWorkflow', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Fase Atual do Workflow")
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
        resultado = self.timesheets.aggregate(total_tempo=Sum('tempo'))
        total_duration = resultado.get('total_tempo')
        if total_duration:
            total_seconds = int(total_duration.total_seconds())
            horas = total_seconds // 3600
            minutos = (total_seconds % 3600) // 60
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

class Analista(models.Model):
    nome = models.CharField(max_length=100)
    def __str__(self): return self.nome

class TipoTarefa(models.Model):
    TIPO_PRAZO_CHOICES = (('U', 'Dias Úteis'), ('C', 'Dias Corridos'))
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome do Tipo de Tarefa")
    prazo_dias = models.IntegerField(verbose_name="Prazo Padrão (em dias)")
    tipo_prazo = models.CharField(max_length=1, choices=TIPO_PRAZO_CHOICES, default='U', verbose_name="Tipo de Prazo")
    recorrente = models.BooleanField(default=False, verbose_name="É uma tarefa recorrente?")
    def __str__(self): return self.nome
    class Meta:
        verbose_name = "Tipo de Tarefa"
        verbose_name_plural = "Tipos de Tarefa"

class Workflow(models.Model):
    nome = models.CharField(max_length=150, unique=True)
    def __str__(self): return self.nome

class FaseWorkflow(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='fases')
    nome = models.CharField(max_length=100)
    ordem = models.PositiveIntegerField()
    atualiza_status_para = models.ForeignKey(Status, on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self): return f"{self.workflow.nome} - {self.ordem}: {self.nome}"
    class Meta:
        ordering = ['workflow', 'ordem']
        unique_together = ('workflow', 'ordem')

class TarefaPadraoWorkflow(models.Model):
    fase = models.ForeignKey(FaseWorkflow, on_delete=models.CASCADE, related_name='tarefas_padrao')
    tipo_tarefa = models.ForeignKey(TipoTarefa, on_delete=models.PROTECT)
    responsavel_override = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    ordem = models.PositiveIntegerField(default=0, blank=False, null=False)
    class Meta:
        # ===== ADICIONE ESTA LINHA PARA ORDENAR POR PADRÃO =====
        ordering = ['ordem']
        # =======================================================

    def __str__(self): return self.tipo_tarefa.nome

class RegraWorkflow(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
    def __str__(self): return f"Regra: {self.cliente} + {self.produto}"
    class Meta:
        unique_together = ('cliente', 'produto')
        verbose_name = "Regra de Workflow"
        verbose_name_plural = "Regras de Workflow"

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

class Tarefa(models.Model):
    STATUS_TAREFA_CHOICES = (('P', 'Pendente'), ('A', 'Em Andamento'), ('C', 'Concluída'))
    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, related_name='tarefas')
    tipo_tarefa = models.ForeignKey(TipoTarefa, on_delete=models.PROTECT, verbose_name="Tipo de Tarefa")
    status = models.CharField(max_length=1, choices=STATUS_TAREFA_CHOICES, default='P')
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_conclusao = models.DateTimeField(blank=True, null=True, verbose_name="Data de Conclusão Real")
    responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    observacao = models.TextField(blank=True)
    
    # ESTE É O NOSSO CAMPO DE PRAZO
    prazo_final = models.DateField(blank=True, null=True, verbose_name="Prazo Final")
    
    descricao_conclusao = models.TextField(blank=True, verbose_name="Descrição da Conclusão")
    origem_fase_workflow = models.ForeignKey(FaseWorkflow, on_delete=models.SET_NULL, null=True, blank=True, help_text="Fase do workflow que gerou esta tarefa.")

    def __str__(self):
        return f"{self.tipo_tarefa.nome} - Caso #{self.caso.id}"
    
    @property
    def data_conclusao_prevista(self):
        # 1. Se um prazo final foi definido manualmente, ele tem prioridade.
        if self.prazo_final:
            return self.prazo_final
        
        # 2. Se não, calcula o prazo padrão a partir do tipo de tarefa.
        if self.tipo_tarefa and self.data_criacao:
            # ... (sua lógica de cálculo de dias úteis/corridos continua aqui)
            if self.tipo_tarefa.tipo_prazo == 'C':
                return self.data_criacao.date() + timedelta(days=self.tipo_tarefa.prazo_dias)
            else:
                dias_uteis_adicionados = 0
                data_atual = self.data_criacao.date()
                while dias_uteis_adicionados < self.tipo_tarefa.prazo_dias:
                    data_atual += timedelta(days=1)
                    if data_atual.weekday() < 5:
                        dias_uteis_adicionados += 1
                return data_atual
        
        return None

    class Meta:
        ordering = ['data_criacao']
    STATUS_TAREFA_CHOICES = (('P', 'Pendente'), ('A', 'Em Andamento'), ('C', 'Concluída'))
    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, related_name='tarefas')
    tipo_tarefa = models.ForeignKey(TipoTarefa, on_delete=models.PROTECT, verbose_name="Tipo de Tarefa")
    status = models.CharField(max_length=1, choices=STATUS_TAREFA_CHOICES, default='P')
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_conclusao = models.DateTimeField(blank=True, null=True, verbose_name="Data de Conclusão Real")
    responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    observacao = models.TextField(blank=True)
    prazo_final = models.DateField(blank=True, null=True, verbose_name="Prazo Final")
    descricao_conclusao = models.TextField(blank=True, verbose_name="Descrição da Conclusão")
    origem_fase_workflow = models.ForeignKey(FaseWorkflow, on_delete=models.SET_NULL, null=True, blank=True, help_text="Fase do workflow que gerou esta tarefa.")
    def __str__(self): return f"{self.tipo_tarefa.nome} - Caso #{self.caso.id}"
    @property
    @property
    def prazo_calculado(self):
        """
        Calcula a data de conclusão prevista para a tarefa.
        Dá prioridade MÁXIMA para o campo 'prazo_final' se ele for preenchido.
        Caso contrário, calcula com base no prazo padrão do Tipo de Tarefa.
        """
        # 1. Se um prazo final foi definido manualmente, ele é a resposta.
        if self.prazo_final:
            return self.prazo_final
        
        # 2. Se não, continua com o cálculo padrão.
        if self.tipo_tarefa and self.data_criacao:
            # Cálculo para dias corridos
            if self.tipo_tarefa.tipo_prazo == 'C':
                return self.data_criacao.date() + timedelta(days=self.tipo_tarefa.prazo_dias)
            # Cálculo para dias úteis
            else:
                dias_uteis_adicionados = 0
                data_atual = self.data_criacao.date()
                dias_a_adicionar = self.tipo_tarefa.prazo_dias
                
                # Otimização para não contar o dia da criação se for dia útil
                if data_atual.weekday() < 5:
                    dias_a_adicionar -= 1
                
                while dias_uteis_adicionados < dias_a_adicionar:
                    data_atual += timedelta(days=1)
                    if data_atual.weekday() < 5: # 0-4 são Seg-Sex
                        dias_uteis_adicionados += 1
                return data_atual
        
        # Retorna None se não for possível calcular de nenhuma forma
        return None
    class Meta:
        ordering = ['data_criacao']



class Timesheet(models.Model):
    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, related_name='timesheets')
    data_execucao = models.DateField(verbose_name="Data de Execução")
    profissional = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="Profissional")
    tempo = models.DurationField(verbose_name="Tempo Gasto (HH:MM)")
    descricao = models.TextField(verbose_name="Descrição da Atividade")
    data_cadastro = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"Lançamento de {self.profissional.username} em {self.data_execucao.strftime('%d/%m/%Y')}"
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