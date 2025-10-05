# contas/signals.py (CORRIGIDO E ROBUSTO)
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Perfil # Certifique-se de que o modelo Perfil está em contas/models.py

User = get_user_model()

@receiver(post_save, sender=User)
def criar_ou_atualizar_perfil_usuario(sender, instance, created, **kwargs):
    """
    Garante que todo User tenha um Perfil.
    Cria um Perfil se o usuário for novo, ou se um usuário antigo não tiver um.
    """
    # A maneira mais segura é usar hasattr() para verificar se o perfil existe
    if not hasattr(instance, 'perfil'):
        # Se não tem o atributo 'perfil', significa que o registro no banco não existe.
        # Então, criamos um.
        Perfil.objects.create(usuario=instance)
    else:
        # Se já tem, apenas salvamos para garantir consistência (opcional, mas seguro).
        instance.perfil.save()