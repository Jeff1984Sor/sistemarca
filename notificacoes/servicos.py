# notificacoes/servicos.py (ATUALIZADO E SIMPLIFICADO)

from django.template import Template, Context
from .models import TemplateEmail
from casos.models import Caso, FluxoInterno
from django.utils import timezone

# A importação do 'enviar_email_graph' foi REMOVIDA daqui, 
# pois a view agora é responsável pelo envio.

def preparar_notificacao(slug_evento, contexto):
    """
    Função central para PREPARAR os dados de um e-mail a ser enviado.
    Ela encontra o template, renderiza o conteúdo e determina os destinatários.
    
    Retorna: (sucesso, dados_ou_erro)
    - Em caso de sucesso: (True, {'assunto': ..., 'corpo': ..., 'destinatarios': [...]})
    - Em caso de erro: (False, "Mensagem de erro")
    """
    try:
        # 1. Encontra o template de e-mail ativo para o evento
        template_email = TemplateEmail.objects.get(evento__slug=slug_evento, ativo=True)
    except TemplateEmail.DoesNotExist:
        return False, f"Nenhum template de e-mail ativo encontrado para o evento '{slug_evento}'."
    except TemplateEmail.MultipleObjectsReturned:
        # Se houver múltiplos, pega o primeiro como fallback seguro
        template_email = TemplateEmail.objects.filter(evento__slug=slug_evento, ativo=True).first()

    try:
        # 2. Renderiza o assunto e o corpo do e-mail usando o contexto fornecido
        template_assunto = Template(template_email.assunto)
        template_corpo = Template(template_email.corpo)
        contexto_django = Context(contexto)
        
        assunto_final = template_assunto.render(contexto_django).strip()
        corpo_final = template_corpo.render(contexto_django)
    except Exception as e:
        return False, f"Erro ao renderizar o template de e-mail: {e}"

    # 3. Monta a lista de e-mails dos destinatários
    lista_emails = []
    
    # Adiciona destinatários fixos, se houver
    if template_email.destinatarios_fixos:
        emails_fixos = [email.strip() for email in template_email.destinatarios_fixos.split(',') if email.strip()]
        lista_emails.extend(emails_fixos)
    
    # Adiciona usuários dos grupos selecionados
    for grupo in template_email.enviar_para_grupos.all():
        for user in grupo.user_set.all():
            if user.email and user.email not in lista_emails:
                lista_emails.append(user.email)
    
    # Garante que não haja e-mails duplicados
    destinatarios_finais = sorted(list(set(lista_emails)))
    
    if not destinatarios_finais:
        return False, "Nenhum destinatário foi configurado para este evento de notificação."

    # 4. Retorna um dicionário com todos os dados prontos para o envio
    dados_email = {
        'assunto': assunto_final,
        'corpo': corpo_final,
        'destinatarios': destinatarios_finais
    }
    
    return True, dados_email