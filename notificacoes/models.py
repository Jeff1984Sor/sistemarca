# notificacoes/models.py

from django.db import models
from django.contrib.auth.models import Group

class Evento(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, help_text="Identificador único para o sistema (ex: 'novo-caso-criado').")
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

class TemplateEmail(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='templates')
    assunto = models.CharField(max_length=255)
    corpo = models.TextField(help_text="Corpo do e-mail. Pode usar variáveis do Django Template.")
    destinatarios_fixos = models.TextField(blank=True, help_text="E-mails separados por vírgula.")
    enviar_para_grupos = models.ManyToManyField(Group, blank=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"Template para o evento: {self.evento.nome}"

class Notificacao(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.SET_NULL, null=True)
    destinatarios = models.TextField()
    assunto = models.CharField(max_length=255)
    data_envio = models.DateTimeField(auto_now_add=True)
    enviado_com_sucesso = models.BooleanField(default=False)

    def __str__(self):
        status = "Sucesso" if self.enviado_com_sucesso else "Falha"
        return f"Notificação do evento '{self.evento.nome}' em {self.data_envio.strftime('%d/%m/%Y')} - {status}"

    class Meta:
        ordering = ['-data_envio']