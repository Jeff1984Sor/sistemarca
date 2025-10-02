from django.db import models

# Create your models here.
# contas/models.py
from django.db import models
from django.contrib.auth.models import User

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    foto = models.ImageField(
        upload_to='fotos_perfil/', 
        default='fotos_perfil/default.png', 
        verbose_name="Foto de Perfil"
    )

    def __str__(self):
        return f'Perfil de {self.user.username}'