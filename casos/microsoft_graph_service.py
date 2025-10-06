# casos/sharepoint_service.py

import requests
import os
import json
import msal
from django.conf import settings
from django.contrib.auth import get_user_model

def get_access_token():
    """Obtém um token de acesso de aplicativo do Azure AD."""
    try:
        client_id = settings.AUTH_ADFS.get('CLIENT_ID')
        client_secret = settings.AUTH_ADFS.get('CLIENT_SECRET')
        tenant_id = settings.AUTH_ADFS.get('TENANT_ID')

        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        payload = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials',
            'scope': 'https://graph.microsoft.com/.default'
        }

        response = requests.post(token_url, data=payload)
        response.raise_for_status()
        
        print("--- SUCESSO! Token de acesso adquirido via MS Graph. ---")
        return response.json().get('access_token')

    except requests.exceptions.HTTPError as e:
        print("\n" + "="*80)
        print(">>> ERRO DE AUTENTICAÇÃO DETALHADO DA MICROSOFT <<<")
        print(f"RESPOSTA: {e.response.text}")
        print("="*80 + "\n")
        return None
    except Exception as e:
        print(f"Falha ao obter token (Erro Genérico): {repr(e)}")
        return None

def criar_pasta_caso(nome_pasta_caso):
    """Cria uma pasta na raiz da Biblioteca de Documentos usando a API MS Graph."""
    token = get_access_token()
    if not token:
        return None

    try:
        drive_id = settings.SHAREPOINT_DRIVE_ID
        if not drive_id:
            print("ERRO: SHAREPOINT_DRIVE_ID não definido no .env")
            return None

        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "name": nome_pasta_caso,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "rename"
        }

        print(f"Tentando criar a pasta '{nome_pasta_caso}' via MS Graph...")
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        if response.status_code == 201:
            folder_data = response.json()
            print(f"Pasta '{folder_data['name']}' criada com sucesso! ID: {folder_data['id']}")
            return folder_data
        else:
            print(f"ERRO ao criar pasta via MS Graph. Status: {response.status_code}")
            print(f"Resposta: {response.text}")
            return None

    except Exception as e:
        print(f"ERRO ao criar a pasta no SharePoint: {repr(e)}")
        return None

def criar_subpastas(id_pasta_pai, lista_subpastas):
    """Cria subpastas dentro de uma pasta pai usando a API MS Graph."""
    token = get_access_token()
    if not token:
        return False

    try:
        drive_id = settings.SHAREPOINT_DRIVE_ID
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        
        url_base = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{id_pasta_pai}/children"

        for nome_subpasta in lista_subpastas:
            payload = {"name": nome_subpasta, "folder": {}, "@microsoft.graph.conflictBehavior": "rename"}
            print(f"Tentando criar a subpasta '{nome_subpasta}'...")
            response = requests.post(url_base, headers=headers, data=json.dumps(payload))
            if response.status_code != 201:
                print(f"Falha ao criar subpasta '{nome_subpasta}'. Status: {response.status_code}, Resposta: {response.text}")
        
        print(f"Criação de subpastas finalizada para a pasta pai ID: {id_pasta_pai}")
        return True

    except Exception as e:
        print(f"ERRO ao criar subpastas no SharePoint: {repr(e)}")
        return False

def listar_arquivos_e_pastas(folder_id):
    """Lista os arquivos e subpastas de uma pasta específica no SharePoint."""
    token = get_access_token()
    if not token or not folder_id:
        return []

    try:
        drive_id = settings.SHAREPOINT_DRIVE_ID
        
        # Endpoint da API Graph para listar os filhos de um item (a pasta)
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{folder_id}/children"

        headers = {
            'Authorization': f'Bearer {token}',
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status() # Lança erro se a requisição falhar

        # Retorna a lista de itens encontrados
        return response.json().get('value', [])

    except Exception as e:
        print(f"ERRO ao listar conteúdo do SharePoint: {repr(e)}")
        return []

def criar_nova_pasta(id_pasta_pai, nome_nova_pasta):
    """Cria uma nova subpasta dentro de uma pasta pai existente."""
    token = get_access_token()
    if not token:
        return None

    try:
        drive_id = settings.SHAREPOINT_DRIVE_ID
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        
        # Endpoint para criar filhos de um item (a pasta pai)
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{id_pasta_pai}/children"

        payload = {
            "name": nome_nova_pasta,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "rename"
        }

        print(f"Tentando criar a nova pasta '{nome_nova_pasta}' dentro do pai {id_pasta_pai}...")
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        if response.status_code == 201:
            folder_data = response.json()
            print(f"Nova pasta '{folder_data['name']}' criada com sucesso!")
            return folder_data
        else:
            print(f"ERRO ao criar nova pasta. Status: {response.status_code}, Resposta: {response.text}")
            return None

    except Exception as e:
        print(f"ERRO ao criar nova pasta: {repr(e)}")
        return None


def upload_arquivo(id_pasta_pai, nome_arquivo, conteudo_arquivo):
    """Faz upload de um arquivo para uma pasta específica no SharePoint."""
    token = get_access_token()
    if not token:
        return None

    try:
        drive_id = settings.SHAREPOINT_DRIVE_ID

        # Endpoint da API Graph para upload de arquivos (até 4MB)
        # O formato é: /items/{id_da_pasta_pai}:/{nome_do_novo_arquivo}:/content
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{id_pasta_pai}:/{nome_arquivo}:/content"

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/octet-stream' # Tipo de conteúdo para dados binários
        }

        print(f"Fazendo upload do arquivo '{nome_arquivo}' para a pasta {id_pasta_pai}...")
        response = requests.put(url, headers=headers, data=conteudo_arquivo)
        
        if response.status_code in [200, 201]: # 201 para novo, 200 para sobrescrever
            file_data = response.json()
            print(f"Upload do arquivo '{file_data['name']}' concluído com sucesso!")
            return file_data
        else:
            print(f"ERRO ao fazer upload. Status: {response.status_code}, Resposta: {response.text}")
            return None

    except Exception as e:
        print(f"ERRO ao fazer upload do arquivo: {repr(e)}")
        return None
    
def obter_url_preview(item_id):
    """Obtém uma URL de pré-visualização de curta duração para um arquivo."""
    token = get_access_token()
    if not token or not item_id:
        return None

    try:
        drive_id = settings.SHAREPOINT_DRIVE_ID
        
        # Endpoint da API Graph para criar um link de preview
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/preview"

        headers = {'Authorization': f'Bearer {token}'}

        # Para o preview, a requisição é um POST vazio
        response = requests.post(url, headers=headers)
        response.raise_for_status()

        # A URL de preview vem na chave 'getUrl'
        preview_url = response.json().get('getUrl')
        print(f"--- URL de Preview obtida para o item {item_id} ---")
        return preview_url

    except Exception as e:
        print(f"ERRO ao obter URL de preview: {repr(e)}")
        return None
    

def deletar_item(item_id):
    """Deleta um item (arquivo ou pasta) do SharePoint pelo seu ID."""
    token = get_access_token()
    if not token or not item_id:
        return False

    try:
        drive_id = settings.SHAREPOINT_DRIVE_ID
        
        # Endpoint da API Graph para deletar um item de um Drive
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}"

        headers = {'Authorization': f'Bearer {token}'}

        print(f"--- Tentando deletar o item ID: {item_id} ---")
        response = requests.delete(url, headers=headers)
        
        # 204 No Content é a resposta de sucesso para delete
        if response.status_code == 204:
            print("--- Item deletado com sucesso. ---")
            return True
        else:
            print(f"ERRO ao deletar item. Status: {response.status_code}, Resposta: {response.text}")
            return False

    except Exception as e:
        print(f"ERRO ao deletar item: {repr(e)}")
        return False
    
def get_user_access_token(request):
    """Obtém o token de acesso DELEGADO do usuário logado na sessão."""
    # A django-auth-adfs salva o token aqui
    return request.session.get('adfs_access_token')

def enviar_email(remetente_email, para, assunto, corpo, salvar_em_enviados=True):
    """Envia um e-mail em nome de um usuário específico usando o token de aplicativo."""
    token = get_access_token()
    if not token:
        return False

    url = f"https://graph.microsoft.com/v1.0/users/{remetente_email}/sendMail"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    email_data = {
        "message": {
            "subject": assunto,
            "body": {"contentType": "HTML", "content": corpo},
            "toRecipients": [
                {"emailAddress": {"address": email.strip()}} for email in para.split(',') if email.strip()
            ]
        },
        "saveToSentItems": "true" if salvar_em_enviados else "false"
    }

    try:
        print(f"--- Tentando enviar e-mail de {remetente_email} para {para} ---")
        response = requests.post(url, headers=headers, json=email_data)
        
        # --- A VERDADE ESTÁ AQUI ---
        # Lança uma exceção HTTPError se o status não for de sucesso (ex: 200, 202)
        response.raise_for_status()

        print(f"--- SUCESSO! Resposta da Microsoft: {response.status_code} ---")
        return True

    except requests.exceptions.HTTPError as e:
        # Se a Microsoft retornar um erro, ele será capturado aqui.
        print("\n" + "="*80)
        print(">>> ERRO DETALHADO DA MICROSOFT AO ENVIAR E-MAIL <<<")
        print(f"URL DA REQUISIÇÃO: {e.request.url}")
        print(f"CÓDIGO DE STATUS: {e.response.status_code}")
        print("RESPOSTA COMPLETA (JSON):")
        print(e.response.text)
        print("="*80 + "\n")
        return False
    except Exception as e:
        print(f"ERRO INESPERADO ao enviar e-mail: {repr(e)}")
        return False
    

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

            # --- LÓGICA APRIMORADA DE NOMES ---
            first_name = user_data.get('givenName')
            last_name = user_data.get('surname')
            display_name = user_data.get('displayName')

            # Se não houver nome e sobrenome, tenta usar o "Nome de Exibição"
            if not first_name and not last_name and display_name:
                parts = display_name.split(' ')
                first_name = parts[0]
                if len(parts) > 1:
                    last_name = ' '.join(parts[1:])

            # Se o primeiro nome ainda estiver vazio, usa a parte do e-mail antes do @
            if not first_name:
                first_name = email.split('@')[0]
            
            # Se o sobrenome ainda estiver vazio, usa um placeholder para não dar erro
            if not last_name:
                last_name = "(sobrenome não informado)" # Um placeholder claro
            
            user, created = User.objects.update_or_create(
                username=email.lower(),
                defaults={
                    'email': email.lower(),
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_active': True
                }
            )
            # ------------------------------------
            
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