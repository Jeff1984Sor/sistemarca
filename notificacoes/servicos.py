# notificacoes/servicos.py

import json
from django.template import Template, Context
from django.utils import timezone
from .models import TemplateEmail
from casos.models import Caso, FluxoInterno
from casos.microsoft_graph_service import enviar_email as enviar_email_graph

def enviar_notificacao(slug_evento, contexto, anexo_buffer=None, nome_anexo=None, content_type_anexo=None):
    """
    Função central para enviar e-mails via Microsoft Graph baseados em modelos
    e registrar a comunicação no Fluxo Interno do caso.
    """
    
    try:
        template_email = TemplateEmail.objects.get(evento__slug=slug_evento, ativo=True)
    except TemplateEmail.DoesNotExist:
        return False, f"Nenhum template ativo para o evento '{slug_evento}'."
    except TemplateEmail.MultipleObjectsReturned:
        template_email = TemplateEmail.objects.filter(evento__slug=slug_evento, ativo=True).first()

    try:
        template_assunto = Template(template_email.assunto)
        template_corpo = Template(template_email.corpo)
        contexto_django = Context(contexto)
        assunto_final = template_assunto.render(contexto_django)
        corpo_final = template_corpo.render(contexto_django)
    except Exception as e:
        return False, f"Erro ao processar o template: {e}"

    lista_emails = []
    if template_email.destinatarios_fixos:
        lista_emails.extend([email.strip() for email in template_email.destinatarios_fixos.split(',') if email.strip()])
    for grupo in template_email.enviar_para_grupos.all():
        for user in grupo.user_set.all():
            if user.email and user.email not in lista_emails:
                lista_emails.append(user.email)
    
    destinatarios_finais = sorted(list(set(lista_emails)))
    if not destinatarios_finais:
        return False, "Nenhum destinatário configurado para este evento."

    usuario_acao = contexto.get('usuario_acao')
    if not usuario_acao or not usuario_acao.email:
        return False, "Erro: O usuário que disparou a ação não tem um e-mail válido para ser o remetente."

    try:
        destinatarios_str = ", ".join(destinatarios_finais)
        
        sucesso = enviar_email_graph(
            remetente_email=usuario_acao.email,
            para=destinatarios_str,
            assunto=assunto_final,
            corpo=corpo_final,
        )
        
        if not sucesso:
            return False, "O serviço da Microsoft retornou uma falha ao tentar enviar o e-mail."

        caso_obj = contexto.get('caso')
        if caso_obj and isinstance(caso_obj, Caso):
            resumo_email = f"Evento: {template_email.evento.nome}"
            conteudo_completo = (
                f"De: {usuario_acao.email}\n"
                f"Para: {destinatarios_str}\n"
                f"Assunto: {assunto_final}\n\n"
                f"--- Conteúdo ---\n{corpo_final}"
            )
            if nome_anexo:
                conteudo_completo += f"\n\nAnexo: {nome_anexo}"
            
            descricao_fluxo_interno = f"[EMAIL]::{resumo_email}|||{conteudo_completo}"
            
            FluxoInterno.objects.create(
                caso=caso_obj,
                data_fluxo=timezone.now().date(),
                descricao=descricao_fluxo_interno,
                usuario_criacao=usuario_acao
            )
        
        return True, "E-mail enviado com sucesso via Microsoft Graph."
        
    except Exception as e:
        print(f"ERRO CRÍTICO ao tentar enviar notificação '{slug_evento}' via Graph. Erro: {e}")
        return False, "Erro técnico no envio do e-mail."