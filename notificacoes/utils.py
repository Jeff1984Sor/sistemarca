# notificacoes/utils.py
from django.core.mail import send_mail
from django.template import Template, Context
from .models import ConfiguracaoEmail, RegraNotificacao
from casos.models import Caso

def enviar_email_dinamico(assunto, corpo, destinatarios, tipo_conteudo='html'):
    try:
        config = ConfiguracaoEmail.objects.get(ativo=True)
        corpo_texto, corpo_html = ('', corpo) if tipo_conteudo == 'html' else (corpo, None)
        
        send_mail(
            subject=assunto, message=corpo_texto, from_email=config.email_host_user,
            recipient_list=destinatarios, html_message=corpo_html,
            fail_silently=False, connection=config.get_connection()
        )
        print(f"E-mail enviado para {destinatarios} com sucesso.")
    except ConfiguracaoEmail.DoesNotExist:
        print("ERRO DE ENVIO: Nenhuma configuração de e-mail ATIVA encontrada.")
    except Exception as e:
        print(f"ERRO DE ENVIO: {e}")

def disparar_notificacao_workflow(caso: Caso, fase_origem, fase_destino):
    try:
        regra = RegraNotificacao.objects.get(
            workflow=fase_origem.workflow,
            fase_de_origem=fase_origem,
            fase_de_destino=fase_destino
        )
        
        template = Template(regra.template_email.corpo)
        contexto = Context({
            'caso': caso, 
            'cliente': caso.cliente,
            'fase_origem': fase_origem,
            'fase_destino': fase_destino,
        })
        corpo_renderizado = template.render(contexto)
        
        destinatarios = [email.strip() for email in regra.destinatarios.split(',')]
        
        enviar_email_dinamico(
            assunto=regra.template_email.assunto,
            corpo=corpo_renderizado,
            destinatarios=destinatarios,
            tipo_conteudo=regra.template_email.tipo_conteudo
        )
    except RegraNotificacao.DoesNotExist:
        print(f"Nenhuma regra de notificação encontrada para a transição: {fase_origem.nome} -> {fase_destino.nome}")