# notificacoes/servicos.py

from django.template import Template, Context
from django.core.mail import EmailMessage
from django.utils import timezone
from .models import TemplateEmail, ConfiguracaoEmail

# Importa os modelos corretos do app 'casos'
from casos.models import FluxoInterno, Caso

# notificacoes/servicos.py

from django.template import Template, Context
from django.core.mail import EmailMessage
from django.utils import timezone
from .models import TemplateEmail, ConfiguracaoEmail
from casos.models import FluxoInterno, Caso

def enviar_notificacao(slug_evento, contexto, anexo_buffer=None, nome_anexo=None, content_type_anexo=None):
    """
    Função central e robusta para enviar e-mails baseados em modelos do admin
    E TAMBÉM registrar a comunicação no Fluxo Interno do caso com um resumo.
    """
    
    # --- BUSCAR CONFIGURAÇÃO DO SERVIDOR ---
    try:
        config_email = ConfiguracaoEmail.objects.get(ativo=True)
    except ConfiguracaoEmail.DoesNotExist:
        mensagem_erro = "ERRO: Nenhuma configuração de servidor de e-mail está marcada como 'Ativa'."
        print(mensagem_erro); return False, "Erro: Nenhum servidor de e-mail ativo."
    except ConfiguracaoEmail.MultipleObjectsReturned:
        mensagem_erro = "ERRO: Mais de uma configuração de servidor está marcada como 'Ativa'."
        print(mensagem_erro); return False, "Erro: Múltiplos servidores de e-mail ativos."

    # --- BUSCAR TEMPLATE DO E-MAIL ---
    try:
        template_email = TemplateEmail.objects.get(evento__slug=slug_evento, ativo=True)
    except TemplateEmail.DoesNotExist:
        mensagem_aviso = f"AVISO: Nenhum template ativo para o evento '{slug_evento}'."
        print(mensagem_aviso); return False, f"Nenhum template ativo para '{slug_evento}'."
    except TemplateEmail.MultipleObjectsReturned:
        mensagem_aviso = f"AVISO: Múltiplos templates ativos para '{slug_evento}'. Usando o primeiro."
        print(mensagem_aviso)
        template_email = TemplateEmail.objects.filter(evento__slug=slug_evento, ativo=True).first()

    # --- RENDERIZAR ASSUNTO E CORPO ---
    try:
        template_assunto = Template(template_email.assunto)
        template_corpo = Template(template_email.corpo)
        contexto_django = Context(contexto)
        assunto_final = template_assunto.render(contexto_django)
        corpo_final = template_corpo.render(contexto_django)
    except Exception as e:
        mensagem_erro = f"ERRO: Falha ao renderizar template para '{slug_evento}'. Erro: {e}"
        print(mensagem_erro); return False, "Erro ao processar o template."

    # --- MONTAR LISTA DE DESTINATÁRIOS ---
    lista_emails = []
    if template_email.destinatarios_fixos:
        lista_emails.extend([email.strip() for email in template_email.destinatarios_fixos.split(',') if email.strip()])
    for grupo in template_email.enviar_para_grupos.all():
        for user in grupo.user_set.all():
            if user.email and user.email not in lista_emails:
                lista_emails.append(user.email)
    
    destinatarios_finais = sorted(list(set(lista_emails)))
    if not destinatarios_finais:
        return False, "Nenhum destinatário configurado."

    # --- CRIAR E ENVIAR O E-MAIL ---
    try:
        conexao = config_email.get_connection()
        email = EmailMessage(subject=assunto_final, body=corpo_final, from_email=config_email.email_host_user, to=destinatarios_finais, connection=conexao)
        
        if anexo_buffer and nome_anexo:
            anexo_buffer.seek(0)
            content_type = content_type_anexo or 'application/octet-stream'
            email.attach(nome_anexo, anexo_buffer.read(), content_type)
        
        email.send()
        
        # ===================================================================
        # ===== REGISTRO NO FLUXO INTERNO (LÓGICA ATUALIZADA) =====
        # ===================================================================
        caso_obj = contexto.get('caso')
        if caso_obj and isinstance(caso_obj, Caso):
            destinatarios_str = ", ".join(destinatarios_finais)
            
            # Parte 1: O resumo visível na lista
            resumo_email = f"Evento: {template_email.evento.nome}"
            
            # Parte 2: O conteúdo completo para o modal
            conteudo_completo = (
                f"Para: {destinatarios_str}\n"
                f"Assunto: {assunto_final}\n\n"
                f"--- Conteúdo ---\n{corpo_final}"
            )
            if nome_anexo:
                conteudo_completo += f"\n\nAnexo: {nome_anexo}"
            
            # Junta tudo com os marcadores
            descricao_fluxo_interno = f"[EMAIL]::{resumo_email}|||{conteudo_completo}"
            
            usuario_acao = contexto.get('usuario_acao')
            
            FluxoInterno.objects.create(
                caso=caso_obj,
                data_fluxo=timezone.now().date(),
                descricao=descricao_fluxo_interno,
                usuario_criacao=usuario_acao
            )
        
        return True, "E-mail enviado com sucesso."
        
    except Exception as e:
        mensagem_erro = f"ERRO SMTP ao enviar notificação '{slug_evento}'. Erro: {e}"
        print(mensagem_erro)
        return False, "Erro técnico no envio do e-mail."