# configuracoes/models.py
from django.db import models
from django.contrib.auth.models import Group
from colorfield.fields import ColorField

class Modulo(models.Model):
    nome = models.CharField(max_length=100)
    slug = models.SlugField(max_length=50, unique=True)
    ativo = models.BooleanField(default=True)
    
    # --- A MÁGICA ESTÁ AQUI ---
    # Um módulo pode ser acessado por vários grupos.
    # Um grupo pode ter acesso a vários módulos.
    grupos_permitidos = models.ManyToManyField(
        Group,
        blank=True,
        verbose_name="Permitido para os Grupos"
    )

    def __str__(self):
        return self.nome
    
class LogoConfig(models.Model):
    logo = models.ImageField(upload_to='logos_empresas/', help_text="Faça o upload do logo da empresa. O ideal é um PNG com fundo transparente.")
    ativo = models.BooleanField(default=True, help_text="Marque esta opção para usar este logo. Apenas um logo pode estar ativo por vez.")

    def __str__(self):
        return f"Logo ({'Ativo' if self.ativo else 'Inativo'})"
    
    def save(self, *args, **kwargs):
        # Garante que apenas um logo possa ser 'ativo' por vez.
        if self.ativo:
            # Coloca todos os outros logos como inativos
            LogoConfig.objects.filter(ativo=True).exclude(pk=self.pk).update(ativo=False)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Configuração de Logo"
        verbose_name_plural = "Configurações de Logo"

class Tema(models.Model):
    nome = models.CharField(max_length=100, unique=True, default="Tema Padrão")
    
    # Cores
    cor_primaria = ColorField(default='#0D6EFD', verbose_name="Cor Primária (botões, links principais)")
    cor_sucesso = ColorField(default='#198754', verbose_name="Cor de Sucesso (verde)")
    cor_perigo = ColorField(default='#DC3545', verbose_name="Cor de Perigo (vermelho)")
    cor_barra_nav = ColorField(default='#212529', verbose_name="Cor da Barra de Navegação Superior")

    # Fontes (usando Google Fonts)
    fonte_principal = models.CharField(
        max_length=200, 
        default='Roboto',
        help_text="Nome da fonte do Google Fonts. Ex: 'Roboto', 'Lato', 'Open Sans'"
    )
    
    ativo = models.BooleanField(default=True, help_text="Apenas um tema pode estar ativo por vez.")

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if self.ativo:
            Tema.objects.filter(ativo=True).exclude(pk=self.pk).update(ativo=False)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Tema da Aplicação"
        verbose_name_plural = "Temas da Aplicação"

class Grafico(models.Model):
    TIPO_GRAFICO_CHOICES = [
        ('bar', 'Barras'),
        ('line', 'Linhas'),
        ('pie', 'Pizza'),
        ('doughnut', 'Rosca (Doughnut)'),
        ('radar', 'Radar'),
    ]
    
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome do Gráfico")
    tipo_grafico = models.CharField(max_length=20, choices=TIPO_GRAFICO_CHOICES, default='bar', verbose_name="Tipo de Gráfico")
    
    # Este é o "link" entre a configuração no admin e a função no código Python
    fonte_dados_slug = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Fonte de Dados (Slug)",
        help_text="Identificador da função que gera os dados. Ex: 'casos_por_status', 'tarefas_por_responsavel'"
    )
        
    ativo_no_dashboard = models.BooleanField(default=True, verbose_name="Mostrar no Dashboard?")
    ordem = models.PositiveIntegerField(default=0, help_text="Ordem de exibição (menor aparece primeiro).")
    
    def __str__(self):
        return self.nome

    class Meta:
        ordering = ['ordem']
        verbose_name = "Gráfico do Dashboard"
        verbose_name_plural = "Gráficos do Dashboard"