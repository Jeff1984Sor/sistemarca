# contas/models.py

from django.db import models
from django.conf import settings # Boa prática importar settings
from django.contrib.auth import get_user_model

User = get_user_model()

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    foto = models.ImageField(
        upload_to='fotos_perfil/', 
        default='fotos_perfil/default.png', 
        verbose_name="Foto de Perfil"
    )

    def __str__(self):
        try:
            return f'Perfil de {self.user.username}'
        except User.DoesNotExist:
            return f'Perfil órfão (ID: {self.id})'