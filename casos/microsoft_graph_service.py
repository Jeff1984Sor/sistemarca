# casos/microsoft_graph_service.py (COMPLETO E ATUALIZADO)

import os
import requests
import msal
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from allauth.socialaccount.models import SocialToken

# --- CONFIGURAÇÕES GLOBAIS ---
# (Mantive suas variáveis de ambiente e configurações existentes)
TENANT_ID = os.environ.get('SHAREPOINT_TENANT_ID')
CLIENT_ID = os.environ.get('SHAREPOINT_CLIENT_ID')
CLIENT_SECRET = os.environ.get('SHAREPOINT_CLIENT_SECRET')
DRIVE_ID = os.environ.get('SHAREPOINT_DRIVE_ID')

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["https://graph.microsoft.com/.default"]

# --- FUNÇÕES DE TOKEN (Aprimoradas) ---

def get_app_graph_token():
    """Obtém um token de acesso para a APLICAÇÃO (não para um usuário específico)."""
    app = msal.ConfidentialClientApplication(CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET)
    result = app.acquire_token_for_client(scopes=SCOPES)
    if "access_token" in result:
        return result['access_token']
    raise Exception(f"Não foi possível obter o token de acesso da aplicação: {result.get('error_description')}")

def get_user_graph_token(user):
    """
    Busca o token de acesso do Microsoft Graph para um usuário específico.
    Tenta usar o token salvo e, se expirado, o renova.
    """
    try:
        social_token = SocialToken.objects.get(account__user=user, account__provider='microsoft')
        
        if social_token.expires_at <= timezone.now():
            print(f"Token para {user.username} expirado. Renovando...")
            app = msal.ConfidentialClientApplication(
                CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
            )
            
            result = app.acquire_token_by_refresh_token(
                social_token.token_secret, # O refresh_token é salvo em token_secret pelo allauth
                scopes=settings.SOCIALACCOUNT_PROVIDERS['microsoft']['SCOPE']
            )

            if "access_token" in result:
                social_token.token = result['access_token']
                social_token.token_secret = result.get('refresh_token', social_token.token_secret)
                social_token.expires_at = timezone.now() + timedelta(seconds=result.get('expires_in', 3600))
                social_token.save()
                print(f"Token para {user.username} renovado com sucesso.")
            else:
                print(f"Falha ao renovar token para {user.username}: {result.get('error_description')}")
                return None
        
        return social_token.token
    
    except SocialToken.DoesNotExist:
        print(f"Token do Microsoft Graph não encontrado para o usuário {user.username}. O usuário precisa logar via Microsoft.")
        return None
    except Exception as e:
        print(f"Erro inesperado ao obter/renovar token do Graph para {user.username}: {e}")
        return None

# --- FUNÇÕES DO SHAREPOINT (Seu código original, mantido) ---

def criar_pasta_caso(nome_pasta):
    access_token = get_app_graph_token()
    headers = {'Authorization': 'Bearer ' + access_token, 'Content-Type': 'application/json'}
    url = f"https://graph.microsoft.com/v1.0/drives/{DRIVE_ID}/root/children"
    payload = {"name": nome_pasta, "folder": {}}
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        return response.json()
    return None

def criar_subpastas(id_pasta_pai, nomes_subpastas):
    access_token = get_app_graph_token()
    headers = {'Authorization': 'Bearer ' + access_token, 'Content-Type': 'application/json'}
    for nome in nomes_subpastas:
        url = f"https://graph.microsoft.com/v1.0/drives/{DRIVE_ID}/items/{id_pasta_pai}/children"
        payload = {"name": nome, "folder": {}}
        requests.post(url, headers=headers, json=payload)

def listar_arquivos_e_pastas(folder_id):
    access_token = get_app_graph_token()
    headers = {'Authorization': 'Bearer ' + access_token}
    url = f"https://graph.microsoft.com/v1.0/drives/{DRIVE_ID}/items/{folder_id}/children"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('value', [])
    return []

def upload_arquivo(parent_folder_id, nome_arquivo, conteudo_arquivo):
    access_token = get_app_graph_token()
    headers = {'Authorization': 'Bearer ' + access_token, 'Content-Type': 'application/octet-stream'}
    url = f"https://graph.microsoft.com/v1.0/drives/{DRIVE_ID}/items/{parent_folder_id}:/{nome_arquivo}:/content"
    response = requests.put(url, headers=headers, data=conteudo_arquivo)
    return response.status_code == 201

def deletar_item(item_id):
    access_token = get_app_graph_token()
    headers = {'Authorization': 'Bearer ' + access_token}
    url = f"https://graph.microsoft.com/v1.0/drives/{DRIVE_ID}/items/{item_id}"
    response = requests.delete(url, headers=headers)
    return response.status_code == 204

def criar_nova_pasta(parent_folder_id, nome_nova_pasta):
    access_token = get_app_graph_token()
    headers = {'Authorization': 'Bearer ' + access_token, 'Content-Type': 'application/json'}
    url = f"https://graph.microsoft.com/v1.0/drives/{DRIVE_ID}/items/{parent_folder_id}/children"
    payload = {"name": nome_nova_pasta, "folder": {}}
    response = requests.post(url, headers=headers, json=payload)
    return response.status_code == 201

def obter_url_preview(item_id):
    access_token = get_app_graph_token()
    headers = {'Authorization': 'Bearer ' + access_token, 'Content-Type': 'application/json'}
    url = f"https://graph.microsoft.com/v1.0/drives/{DRIVE_ID}/items/{item_id}/preview"
    response = requests.post(url, headers=headers, json={})
    if response.status_code == 200:
        return response.json().get('getUrl')
    return None

# ==============================================================================
# NOVA FUNÇÃO DE ENVIO DE E-MAIL (PELO USUÁRIO)
# ==============================================================================

def enviar_email_graph(usuario_remetente, destinatarios, assunto, corpo_html):
    """
    Envia um e-mail usando a conta do Microsoft Graph do usuário logado.
    """
    access_token = get_user_graph_token(usuario_remetente)
    if not access_token:
        print(f"Falha no envio de e-mail: não foi possível obter o token para {usuario_remetente.username}")
        return False, "Não foi possível obter o token de autenticação do usuário."

    headers = {
        'Authorization': 'Bearer ' + access_token,
        'Content-Type': 'application/json'
    }
    
    to_recipients = [{'emailAddress': {'address': email.strip()}} for email in destinatarios]

    email_data = {
        'message': {
            'subject': assunto,
            'body': {
                'contentType': 'HTML',
                'content': corpo_html
            },
            'toRecipients': to_recipients
        },
        'saveToSentItems': 'true'
    }
    
    url = "https://graph.microsoft.com/v1.0/me/sendMail"
    
    try:
        response = requests.post(url, headers=headers, json=email_data)
        response.raise_for_status()
        print(f"E-mail enviado com sucesso de {usuario_remetente.email} para {destinatarios}")
        return True, "E-mail enviado com sucesso."
    except requests.exceptions.RequestException as e:
        error_text = e.response.text if e.response else 'N/A'
        print(f"Erro ao enviar e-mail via Microsoft Graph: {e}")
        print(f"Resposta da API: {error_text}")
        return False, f"Falha ao enviar e-mail via Microsoft: {error_text}"

# ==============================================================================
# SUA FUNÇÃO DE SINCRONIZAÇÃO (Mantida e completa)
# ==============================================================================

def sincronizar_usuarios_azure():
    User = get_user_model()
    
    tenant_id = os.environ.get('SHAREPOINT_TENANT_ID')
    client_id = os.environ.get('SHAREPOINT_CLIENT_ID')
    client_secret = os.environ.get('SHAREPOINT_CLIENT_SECRET')
    
    if not all([tenant_id, client_id, client_secret]):
        raise ValueError("Variáveis de ambiente (TENANT_ID, CLIENT_ID, CLIENT_SECRET) não configuradas.")
            
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    
    if "access_token" not in result:
        error_details = result.get('error_description', 'Nenhum detalhe adicional.')
        raise ConnectionError(f"Não foi possível obter o token de acesso da Microsoft. Detalhes: {error_details}")

    access_token = result['access_token']
    headers = {'Authorization': 'Bearer ' + access_token}
    
    url = "https://graph.microsoft.com/v1.0/users?$filter=accountEnabled eq true&$select=id,displayName,givenName,surname,mail,userPrincipalName"
    
    usuarios_criados = 0
    usuarios_atualizados = 0
    total_azure = 0
    
    while url:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        lista_usuarios_azure = data.get('value', [])
        total_azure += len(lista_usuarios_azure)
        
        for user_data in lista_usuarios_azure:
            email = user_data.get('mail') or user_data.get('userPrincipalName')
            if not email:
                continue

            first_name = user_data.get('givenName')
            last_name = user_data.get('surname')
            display_name = user_data.get('displayName')

            if not first_name and not last_name and display_name:
                parts = display_name.split(' ')
                first_name = parts[0]
                if len(parts) > 1:
                    last_name = ' '.join(parts[1:])

            if not first_name:
                first_name = email.split('@')[0]
            
            if not last_name:
                last_name = "(sobrenome não informado)"
            
            user, created = User.objects.update_or_create(
                username=email.lower(),
                defaults={
                    'email': email.lower(),
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_active': True
                }
            )
            
            if created:
                usuarios_criados += 1
                user.set_unusable_password() 
                user.save()
            else:
                usuarios_atualizados += 1
        
        url = data.get('@odata.nextLink')
        
    return (
        f"Sincronização concluída! "
        f"{total_azure} usuários encontrados no Azure AD. "
        f"Usuários criados no sistema: {usuarios_criados}. "
        f"Usuários atualizados: {usuarios_atualizados}."
    )