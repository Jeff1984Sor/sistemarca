# clientes/models.py
from django.db import models

# --- NOVOS MODELOS DE APOIO PARA AS LISTAS ---
class Nacionalidade(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.nome
    class Meta:
        ordering = ['nome']
        verbose_name_plural = "Nacionalidades"

class EstadoCivil(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.nome
    class Meta:
        ordering = ['nome']
        verbose_name = "Estado Civil"
        verbose_name_plural = "Estados Civis"

class Profissao(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.nome
    class Meta:
        ordering = ['nome']
        verbose_name = "Profissão"
        verbose_name_plural = "Profissões"

# --- O NOVO E PODEROSO MODELO CLIENTE ---
class Cliente(models.Model):
    TIPO_PESSOA_CHOICES = (
        ('PJ', 'Pessoa Jurídica'),
        ('PF', 'Pessoa Física'),
    )
    tipo_pessoa = models.CharField(max_length=2, choices=TIPO_PESSOA_CHOICES, default='PJ', verbose_name="Tipo de Pessoa")

    # Campos Comuns (PF e PJ)
    nome_razao_social = models.CharField(max_length=150, verbose_name="Nome / Razão Social")
    email = models.EmailField(max_length=100, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True)

    # Campos de Pessoa Jurídica (PJ)
    cnpj = models.CharField(max_length=18, blank=True, null=True, verbose_name="CNPJ")
    inscricao_estadual = models.CharField(max_length=20, blank=True, verbose_name="Inscrição Estadual")

    # Campos de Pessoa Física (PF)
    cpf = models.CharField(max_length=14, blank=True, null=True, verbose_name="CPF")
    rg = models.CharField(max_length=20, blank=True, verbose_name="RG")
    nacionalidade = models.ForeignKey(Nacionalidade, on_delete=models.SET_NULL, blank=True, null=True)
    estado_civil = models.ForeignKey(EstadoCivil, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Estado Civil")
    profissao = models.ForeignKey(Profissao, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Profissão")

    # Campos de Endereço (Comuns, preenchidos pela API)
    cep = models.CharField(max_length=9, blank=True, verbose_name="CEP")
    logradouro = models.CharField(max_length=255, blank=True)
    numero = models.CharField(max_length=20, blank=True, verbose_name="Número")
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    uf = models.CharField(max_length=2, blank=True, verbose_name="Estado (UF)")
    
    # Campos para o Mapa
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    def __str__(self):
        return self.nome_razao_social