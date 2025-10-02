# casos/management/commands/sync_azure_users.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
import requests

User = get_user_model()

def get_app_token():
    # Esta função busca um token de aplicativo para o MS Graph
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
    return response.json().get('access_token')

class Command(BaseCommand):
    help = 'Sincroniza os usuários do Azure AD com a base de dados do Django.'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando sincronização de usuários do Azure AD...")
        
        token = get_app_token()
        if not token:
            self.stderr.write(self.style.ERROR("Falha ao obter token de acesso."))
            return

        headers = {'Authorization': f'Bearer {token}'}
        # O $select garante que estamos pedindo apenas os campos que precisamos
        # O $filter=accountEnabled eq true garante que pegamos apenas usuários ativos
        url = "https://graph.microsoft.com/v1.0/users?$select=id,userPrincipalName,givenName,surname,mail,accountEnabled&$filter=accountEnabled eq true"
        
        created_count = 0
        updated_count = 0

        while url:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            for user_data in data.get('value', []):
                username = user_data.get('userPrincipalName')
                email = user_data.get('mail') or username # Usa o UPN se o campo 'mail' for nulo

                if not username:
                    continue
                
                user, created = User.objects.update_or_create(
                    username=username.lower(), # Salva em minúsculas para consistência
                    defaults={
                        'email': email.lower(),
                        'first_name': user_data.get('givenName', ''),
                        'last_name': user_data.get('surname', ''),
                        'is_active': True,
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(f"  -> Criado: {user.username}")
                else:
                    updated_count += 1
            
            # A API do Graph usa paginação, o '@odata.nextLink' nos dá a próxima página
            url = data.get('@odata.nextLink')

        self.stdout.write(self.style.SUCCESS(f"Sincronização concluída!"))
        self.stdout.write(f"Usuários criados: {created_count}")
        self.stdout.write(f"Usuários atualizados: {updated_count}")