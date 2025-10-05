# contas/signals.py (VERSÃO MAIS ROBUSTA AINDA)

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Perfil

User = get_user_model()

# A mudança está aqui: adicionamos o dispatch_uid
@receiver(post_save, sender=User, dispatch_uid="criar_perfil_usuario_unico")
def criar_ou_atualizar_perfil_usuario(sender, instance, created, **kwargs):
    """
    Garante que todo User tenha um Perfil.
    Usa hasattr para ser seguro contra usuários existentes sem perfil.
    Usa dispatch_uid para garantir que o sinal seja registrado apenas uma vez.
    """
    if not hasattr(instance, 'perfil'):
        # O código correto que já tínhamos:
        Perfil.objects.create(user=instance)
    else:
        instance.perfil.save()