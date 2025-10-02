# clientes/forms.py

from django import forms
from .models import Cliente

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        # Inclui todos os campos do nosso novo modelo
        fields = '__all__'
        
        # Define os widgets e classes do Bootstrap para cada campo
        widgets = {
            # Comuns
            'tipo_pessoa': forms.Select(attrs={'class': 'form-select'}),
            'nome_razao_social': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),

            # Pessoa Jurídica (PJ)
            'cnpj': forms.TextInput(attrs={'class': 'form-control'}),
            'inscricao_estadual': forms.TextInput(attrs={'class': 'form-control'}),

            # Pessoa Física (PF)
            'cpf': forms.TextInput(attrs={'class': 'form-control'}),
            'rg': forms.TextInput(attrs={'class': 'form-control'}),
            'nacionalidade': forms.Select(attrs={'class': 'form-select'}),
            'estado_civil': forms.Select(attrs={'class': 'form-select'}),
            'profissao': forms.Select(attrs={'class': 'form-select'}),

            # Endereço (API)
            'cep': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite o CEP e aguarde'}),
            'logradouro': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'complemento': forms.TextInput(attrs={'class': 'form-control'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'uf': forms.TextInput(attrs={'class': 'form-control'}),

            # Campos ocultos do mapa
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

        # Melhora os nomes (labels) que aparecem para o usuário
        labels = {
            'nome_razao_social': 'Nome / Razão Social',
            'numero': 'Número',
            'uf': 'Estado (UF)',
        }