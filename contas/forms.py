# contas/forms.py
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User # Usa o User padrão do Django
from django import forms
from django.contrib.auth.models import User
from .models import Perfil
from django import forms
from django.contrib.auth.models import User
from .models import Perfil

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User # Aponta para o User padrão
        # Adiciona os campos de email e nome ao formulário de cadastro
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adiciona a classe do Bootstrap a todos os campos
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

class UserUpdateForm(forms.ModelForm):
    # O email no Django User pode ser editado, mas não é o 'username'
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class PerfilUpdateForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['foto']
        widgets = {
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
        }