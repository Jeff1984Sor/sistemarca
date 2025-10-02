# equipamentos/forms.py
from django import forms
from .models import Equipamento

class EquipamentoForm(forms.ModelForm):
    class Meta:
        model = Equipamento
        fields = '__all__'  # Inclui todos os campos do modelo no formulário

        # Adiciona classes do Bootstrap para deixar o formulário bonito
        widgets = {
            'numero_item': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_item': forms.Select(attrs={'class': 'form-select'}),
            'categoria_item': forms.Select(attrs={'class': 'form-select'}),
            'marca': forms.Select(attrs={'class': 'form-select'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'data_compra': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'local_compra': forms.TextInput(attrs={'class': 'form-control'}),
            'valor_pago': forms.NumberInput(attrs={'class': 'form-control'}),
            'pago_por': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone_usuario': forms.TextInput(attrs={'class': 'form-control'}),
            'status_item': forms.Select(attrs={'class': 'form-select'}),
            'posse_status': forms.Select(attrs={'class': 'form-select'}),
            'posse_usuario': forms.Select(attrs={'class': 'form-select'}),
        }