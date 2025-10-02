# notificacoes/models.py

from django.db import models
from django.core.mail.backends.smtp import EmailBackend
from django.contrib.auth.models import Group

class Evento(models.Model):
    """
    Define um gatilho para uma notificação.
    Ex: 'Criação de Novo Caso', 'Envio de Relatório de Timesheet'.
    """
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome do Evento")
    slug = models.SlugField(unique=True, help_text="Identificador único para usar no código (será preenchido automaticamente). Ex: 'novo_caso_criado'")
    descricao = models.TextField(blank=True, help_text="Descreva o que este evento significa e quais variáveis de contexto estão disponíveis (ex: {{ caso }}, {{ usuario_acao }}).")

    def __str__(self):
        return self.nome

class TemplateEmail(models.Model):
    """
    Define o conteúdo e os destinatários de um e-mail para um determinado evento.
    """
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name="templates")
    nome_template = models.CharField(max_length=150, help_text="Nome interno para identificar este template, ex: 'E-mail de boas-vindas para cliente'")
    assunto = models.CharField(max_length=200, help_text="Pode usar variáveis como {{ caso.titulo_caso }}")
    corpo = models.TextField(verbose_name="Corpo do E-mail", help_text="Pode usar variáveis como {{ caso.cliente.nome_razao_social }} e {{ usuario_acao.get_full_name }}.")
    destinatarios_fixos = models.TextField(blank=True, verbose_name="Enviar Cópia Para (E-mails Fixos)", help_text="E-mails fixos, separados por vírgula. Ex: email1@exemplo.com")
    enviar_para_grupos = models.ManyToManyField(Group, blank=True, verbose_name="Enviar para Grupos de Usuários", help_text="Envia para todos os usuários nestes grupos.")
    ativo = models.BooleanField(default=True, help_text="Se desmarcado, este template não será usado.")

    def __str__(self):
        return f"Template '{self.nome_template}' para o evento '{self.evento.nome}'"

    class Meta:
        verbose_name = "Template de E-mail"
        verbose_name_plural = "Templates de E-mail"

class ConfiguracaoEmail(models.Model):
    """
    Permite que você configure o servidor de envio de e-mail (SMTP) pelo Admin.
    """
    apelido = models.CharField(max_length=100, help_text="Ex: E-mail Principal do Sistema")
    email_host = models.CharField(max_length=100, verbose_name="Servidor SMTP (Ex: smtp.office365.com)")
    email_port = models.PositiveIntegerField(default=587, verbose_name="Porta")
    email_host_user = models.EmailField(verbose_name="Usuário (e-mail de envio)")
    email_host_password = models.CharField(max_length=100, verbose_name="Senha (ou Senha de App)")
    email_use_tls = models.BooleanField(default=True, verbose_name="Usar TLS")
    ativo = models.BooleanField(default=True, help_text="Apenas UMA configuração pode estar ativa.")

    def __str__(self):
        return self.apelido

    def save(self, *args, **kwargs):
        if self.ativo:
            ConfiguracaoEmail.objects.filter(ativo=True).exclude(pk=self.pk).update(ativo=False)
        super().save(*args, **kwargs)
    
    def get_connection(self):
        return EmailBackend(
            host=self.email_host, port=self.email_port, username=self.email_host_user,
            password=self.email_host_password, use_tls=self.email_use_tls,
            fail_silently=False
        )

    class Meta:
        verbose_name = "Configuração de Servidor de E-mail"