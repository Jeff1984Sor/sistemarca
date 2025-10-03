from django import forms
from . import models
from django.template import Template, Context
from datetime import timedelta
from .models import (
    Caso, Campo, ValorCampoCaso, FluxoInterno, Timesheet, 
    OpcaoCampo, AndamentoCaso
)

class CasoCreateForm(forms.ModelForm):
    class Meta:
        model = Caso
        fields = [
            'titulo_caso', 'cliente', 'produto', 'status', 
            'data_entrada_rca', 'advogado_responsavel'
        ]
        labels = {
            'produto': 'Produto / Objeto do Serviço',
        }
        widgets = {
            'titulo_caso': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'produto': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'advogado_responsavel': forms.Select(attrs={'class': 'form-select'}),
            'data_entrada_rca': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class CasoUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not field_name.startswith('dynamic_'):
                if isinstance(field.widget, forms.Select):
                    field.widget.attrs.update({'class': 'form-select'})
                elif isinstance(field.widget, forms.DateInput):
                    field.widget.attrs.update({'type': 'date', 'class': 'form-control'})
                else:
                    field.widget.attrs.update({'class': 'form-control'})
        if 'titulo_caso' in self.fields:
            self.fields['titulo_caso'].widget.attrs.update({'readonly': True, 'style': 'background-color: #e9ecef;'})

    class Meta:
        model = Caso
        fields = [
            'cliente', 'produto', 'status', 'advogado_responsavel',
            'data_entrada_rca','data_encerramento', 'titulo_caso'
        ]
        labels = {
            'produto': 'Produto / Objeto do Serviço',
        }

class AndamentoCasoForm(forms.ModelForm):
    class Meta:
        model = AndamentoCaso
        fields = ['data_andamento', 'descricao']
        widgets = {
            'data_andamento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }

class FluxoInternoForm(forms.ModelForm):
    class Meta:
        model = FluxoInterno
        fields = ['data_fluxo', 'descricao']
        widgets = {
            'data_fluxo': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Digite a descrição...'})
        }
        labels = { 'data_fluxo': 'Data', 'descricao': 'Descrição' }


class EnviarEmailForm(forms.Form):
    para = forms.CharField(label="Para", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'email1@dominio.com, email2@dominio.com'}))
    assunto = forms.CharField(label="Assunto", widget=forms.TextInput(attrs={'class': 'form-control'}))
    corpo = forms.CharField(label="Corpo do E-mail", widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 10}))
    modelo_id = forms.ChoiceField(label="Usar Modelo", required=False, choices=[('', '---------')], widget=forms.Select(attrs={'class': 'form-select'}))
    assinatura_id = forms.ChoiceField(label="Usar Assinatura", required=False, choices=[('', '---------')], widget=forms.Select(attrs={'class': 'form-select'}))

class LancamentoHorasForm(forms.ModelForm):
    tempo_str = forms.CharField(label="Tempo Gasto (HH:MM)", required=True, widget=forms.TextInput(attrs={'class': 'form-control time-mask', 'placeholder': '02:30'}))

    class Meta:
        model = models.Timesheet
        fields = ['data_execucao', 'profissional', 'descricao']
        widgets = {
            'data_execucao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profissional': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.minutos_gastos is not None:
            horas = self.instance.minutos_gastos // 60
            minutos = self.instance.minutos_gastos % 60
            self.initial['tempo_str'] = f"{horas:02d}:{minutos:02d}"

    def clean_tempo_str(self):
        tempo_str = self.cleaned_data['tempo_str']
        try:
            horas, minutos = map(int, tempo_str.split(':'))
            if not (0 <= minutos < 60): raise forms.ValidationError("Minutos devem ser entre 00 e 59.")
            return tempo_str
        except (ValueError, IndexError): raise forms.ValidationError("Formato inválido. Use HH:MM.")

    def save(self, commit=True):
        instance = super().save(commit=False)
        tempo_str = self.cleaned_data['tempo_str']
        horas, minutos = map(int, tempo_str.split(':'))
        instance.minutos_gastos = (horas * 60) + minutos
        if commit: instance.save()
        return instance