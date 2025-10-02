from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
from django.urls import reverse
from datetime import datetime, timedelta
from django.utils import timezone  # <<< LINHA ADICIONADA AQUI
import requests
import json
from casos.models import GraphWebhookSubscription

User = get_user_model()

class Command(BaseCommand):
    help = 'Cria ou renova as assinaturas de webhook do Microsoft Graph para novos e-mails.'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando gerenciamento de webhooks...")
        
        users_to_subscribe = User.objects.filter(is_active=True)

        for user in users_to_subscribe:
            self.stdout.write(f"Verificando assinatura para: {user.username}")
            
            try:
                subscription = GraphWebhookSubscription.objects.get(user=user)
                if subscription.expiration_datetime < (timezone.now() + timedelta(hours=24)):
                    self.renew_subscription(subscription)
                else:
                    self.stdout.write(self.style.SUCCESS(f"Assinatura para {user.username} ainda é válida."))
            except GraphWebhookSubscription.DoesNotExist:
                self.create_subscription(user)

        self.stdout.write(self.style.SUCCESS("Gerenciamento de webhooks concluído."))

    def get_app_token(self):
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

    def create_subscription(self, user):
        token = self.get_app_token()
        if not token:
            self.stderr.write(f"Falha ao obter token para criar assinatura para {user.username}")
            return

        if not settings.WEBHOOK_BASE_URL:
            self.stderr.write("ERRO: WEBHOOK_BASE_URL não está definido no seu .env. Não é possível criar webhooks.")
            return
        
        url = "https://graph.microsoft.com/v1.0/subscriptions"
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        
        notification_url = f"{settings.WEBHOOK_BASE_URL}{reverse('casos:microsoft_graph_webhook')}"

        payload = {
           "changeType": "created",
           "notificationUrl": notification_url,
           "resource": f"/users/{user.email}/mailFolders('inbox')/messages",
           "expirationDateTime": (datetime.utcnow() + timedelta(days=2)).isoformat() + "Z",
           "clientState": "AureonSecretClientState"
        }

        self.stdout.write(f"Criando nova assinatura para {user.username}...")
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        if response.status_code == 201:
            data = response.json()
            GraphWebhookSubscription.objects.create(
                user=user,
                subscription_id=data['id'],
                expiration_datetime=data['expirationDateTime']
            )
            self.stdout.write(self.style.SUCCESS(f"Assinatura criada com sucesso para {user.username} (ID: {data['id']})"))
        else:
            self.stderr.write(f"Falha ao criar assinatura para {user.username}: {response.text}")

    def renew_subscription(self, subscription):
        self.stdout.write(f"Lógica de renovação para {subscription.user.username} a ser implementada.")