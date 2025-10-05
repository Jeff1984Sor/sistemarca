# contas/models.py (ATUALIZADO E ROBUSTO)

from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

# Boa prática: Usar get_user_model() para referenciar o modelo de usuário
User = get_user_model()

class Perfil(models.Model):
    # O seu campo 'user' já estava correto
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    
    foto = models.ImageField(
        upload_to='fotos_perfil/', 
        default='fotos_perfil/default.png', 
        verbose_name="Foto de Perfil"
    )

    def __str__(self):
        # Versão segura que não quebra se o usuário não existir
        try:
            return f'Perfil de {self.user.username}'
        except User.DoesNotExist:
            return f'Perfil órfão (ID: {self.id})'