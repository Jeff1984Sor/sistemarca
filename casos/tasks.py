# casos/tasks.py (CORRIGIDO)

import time
from celery import shared_task
from django.contrib.auth import get_user_model
import requests

# Importa os modelos necessários
from .models import GraphWebhookSubscription, EmailCaso, Caso

# --- A CORREÇÃO PRINCIPAL ESTÁ AQUI ---
# Importa a função correta para obter o token da APLICAÇÃO
from .microsoft_graph_service import get_app_graph_token, criar_pasta_caso, criar_subpastas

User = get_user_model()


@shared_task
def processar_email_webhook(subscription_id, resource_id):
    print(f"CELERY TASK: Processando e-mail para subscription {subscription_id}, resource {resource_id}")
    try:
        try:
            subscription = GraphWebhookSubscription.objects.get(subscription_id=subscription_id)
            user = subscription.user
        except GraphWebhookSubscription.DoesNotExist:
            print(f"CELERY TASK: Assinatura de webhook {subscription_id} não encontrada. Ignorando.")
            return

        # Usa a nova função de token
        token = get_app_graph_token()
        if not token:
            print("CELERY TASK: Falha ao obter token de aplicativo.")
            return

        url = f"https://graph.microsoft.com/v1.0/users/{user.email}/messages/{resource_id}"
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        email_data = response.json()

        thread_id = email_data.get('conversationId')
        if not thread_id:
            print("CELERY TASK: E-mail recebido não tem ID de conversação. Ignorando.")
            return

        email_anterior = EmailCaso.objects.filter(thread_id=thread_id).first()
        if not email_anterior:
            print(f"CELERY TASK: Nenhuma conversa anterior encontrada para a thread {thread_id}. Ignorando.")
            return
        
        caso = email_anterior.caso

        EmailCaso.objects.update_or_create(
            microsoft_message_id=email_data['id'],
            defaults={
                'caso': caso,
                'de': email_data['from']['emailAddress']['address'],
                'para': ", ".join([rcp['emailAddress']['address'] for rcp in email_data.get('toRecipients', [])]),
                'assunto': email_data.get('subject', ''),
                'preview': email_data.get('bodyPreview', ''),
                'corpo_html': email_data.get('body', {}).get('content', ''),
                'data_envio': email_data.get('receivedDateTime'),
                'is_sent': False,
                'thread_id': thread_id,
            }
        )
        print(f"CELERY TASK: E-mail de resposta salvo com sucesso para o Caso #{caso.id}!")
    except Exception as e:
        print(f"CELERY TASK: Erro inesperado ao processar e-mail: {repr(e)}")


@shared_task
def buscar_detalhes_email_enviado(user_email, email_caso_id, para, assunto):
    time.sleep(10) 
    print(f"CELERY TASK: Buscando detalhes do e-mail enviado de '{user_email}' para '{para}'")
    
    # Usa a nova função de token
    token = get_app_graph_token()
    if not token:
        print("CELERY TASK: Falha ao obter token para buscar detalhes.")
        return
        
    try:
        primeiro_destinatario = para.split(',')[0].strip()
        url = (
            f"https://graph.microsoft.com/v1.0/users/{user_email}/mailFolders('sentitems')/messages?"
            f"$filter=subject eq '{assunto}' and toRecipients/any(r: r/emailAddress/address eq '{primeiro_destinatario}')"
            "&$orderby=sentDateTime desc&$top=1"
        )
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        emails = response.json().get('value', [])
        if emails:
            email_data = emails[0]
            email_obj = EmailCaso.objects.get(id=email_caso_id)
            email_obj.microsoft_message_id = email_data['id']
            email_obj.thread_id = email_data.get('conversationId')
            email_obj.save(update_fields=['microsoft_message_id', 'thread_id'])
            print(f"CELERY TASK: Detalhes do e-mail (ID: {email_obj.id}) atualizados com thread_id: {email_obj.thread_id}!")
        else:
            print(f"CELERY TASK: E-mail enviado com assunto '{assunto}' não encontrado em 'Itens Enviados'.")
    except Exception as e:
        print(f"CELERY TASK: Erro ao buscar detalhes do e-mail enviado: {repr(e)}")


@shared_task
def criar_estrutura_sharepoint_async(caso_id):
    try:
        caso = Caso.objects.get(id=caso_id)
        if not caso.produto: return

        nome_pasta_sanitizado = str(caso.id)
        pasta_criada_json = criar_pasta_caso(nome_pasta_sanitizado)

        if pasta_criada_json:
            caso.sharepoint_folder_id = pasta_criada_json['id']
            caso.sharepoint_folder_url = pasta_criada_json['webUrl']
            caso.save(update_fields=['sharepoint_folder_id', 'sharepoint_folder_url'])
            
            id_pasta_pai = pasta_criada_json['id']
            subpastas = [p.nome_pasta for p in caso.produto.estrutura_pastas.all()]
            if subpastas:
                subpastas_sanitizadas = ["".join(c if c not in r'<>:"/\|?*' else '-' for c in nome_sub) for nome_sub in subpastas]
                criar_subpastas(id_pasta_pai, subpastas_sanitizadas)
            print(f"Estrutura do SharePoint criada para o Caso #{caso_id}")
        else:
            print(f"Falha ao criar pasta principal no SharePoint para o Caso #{caso_id}")
    except Exception as e:
        print(f"Erro na tarefa de criação de pasta do SharePoint: {e}")