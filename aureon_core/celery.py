# aureon_core/celery.py
import os
from celery import Celery

# Define o módulo de configurações do Django para o Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aureon_core.settings')

# Cria a instância do aplicativo Celery
app = Celery('aureon_core')

# Carrega a configuração a partir do settings.py do Django
# O namespace='CELERY' significa que todas as configs do Celery devem começar com CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descobre automaticamente as tarefas (procurando por arquivos tasks.py nos apps)
app.autodiscover_tasks()