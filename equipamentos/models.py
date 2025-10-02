# equipamentos/models.py
from django.db import models
from django.conf import settings

class TipoItem(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.nome

class CategoriaItem(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.nome
    class Meta:
        verbose_name_plural = "Categorias de Itens"

class Marca(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.nome

class StatusItem(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.nome
    class Meta:
        verbose_name_plural = "Status de Itens"

class Equipamento(models.Model):
    POSSE_STATUS_CHOICES = (
        ('EM_USO', 'Em Uso'),
        ('VENDER', 'Para Vender'),
        ('LIVRE', 'Livre (Em Estoque)'),
    )
    numero_item = models.CharField(max_length=50, verbose_name="Nº do Item / Etiqueta")
    tipo_item = models.ForeignKey(TipoItem, on_delete=models.PROTECT, verbose_name="Tipo do Item")
    categoria_item = models.ForeignKey(CategoriaItem, on_delete=models.PROTECT, verbose_name="Categoria do Item")
    marca = models.ForeignKey(Marca, on_delete=models.PROTECT)
    modelo = models.CharField(max_length=100)
    data_compra = models.DateField(verbose_name="Data da Compra")
    local_compra = models.CharField(max_length=150, blank=True, verbose_name="Local da Compra / Loja")
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Pago (R$)")
    pago_por = models.CharField(max_length=100, blank=True, verbose_name="Pago Por")
    telefone_usuario = models.CharField(max_length=20, blank=True, verbose_name="Telefone do Usuário (Contato)")
    status_item = models.ForeignKey(StatusItem, on_delete=models.PROTECT, verbose_name="Status do Item")
    posse_status = models.CharField(max_length=10, choices=POSSE_STATUS_CHOICES, default='LIVRE', verbose_name="Posse Atual")
    posse_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Em posse do Usuário"
    )
    
    def __str__(self):
        return f"{self.tipo_item.nome} {self.marca.nome} {self.modelo} ({self.numero_item})"