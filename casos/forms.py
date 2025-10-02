# casos/forms.py

from django import forms
from django.template import Template, Context
from .models import (
    Caso, Campo, ValorCampoCaso, FluxoInterno, Tarefa, Timesheet, 
    OpcaoCampo, RegraCampo, AndamentoCaso
)

# ==============================================================================
# FORMULÁRIO 1: SIMPLES, PARA A CRIAÇÃO DE UM NOVO CASO
# ==============================================================================
class CasoCreateForm(forms.ModelForm):
    class Meta:
        model = Caso
        
        # --- ORDEM DOS CAMPOS ATUALIZADA AQUI ---
        fields = [
            'titulo_caso',
            'cliente', 
            'produto', 
            'status', 
            'data_entrada_rca',
            'advogado_responsavel'
        ]

        labels = {
            'produto': 'Produto / Objeto do Serviço',
        }
        
        widgets = {
            # --- CAMPO TÍTULO BLOQUEADO (READONLY) AQUI ---
            'titulo_caso': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            
            # --- O resto continua como estava ---
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'produto': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'advogado_responsavel': forms.Select(attrs={'class': 'form-select'}),
            'data_entrada_rca': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class EnviarEmailForm(forms.Form):
    para = forms.CharField(
        label="Para",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'email1@dominio.com, email2@dominio.com'})
    )
    assunto = forms.CharField(
        label="Assunto",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    corpo = forms.CharField(
        label="Corpo do E-mail",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 10})
    )
    # Campos opcionais para usar modelos e assinaturas
    modelo_id = forms.ChoiceField(label="Usar Modelo", required=False, choices=[('', '---------')], widget=forms.Select(attrs={'class': 'form-select'}))
    assinatura_id = forms.ChoiceField(label="Usar Assinatura", required=False, choices=[('', '---------')], widget=forms.Select(attrs={'class': 'form-select'}))
# ==============================================================================
# FORMULÁRIO 2: COMPLETO E DINÂMICO, PARA A EDIÇÃO DE UM CASO
# ==============================================================================
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

        if self.instance and self.instance.pk:
            try:
                regra = RegraCampo.objects.get(cliente=self.instance.cliente, produto=self.instance.produto)
                campos_a_mostrar = regra.campos.all().order_by('nome_label')
                
                for campo in campos_a_mostrar:
                    field_name = f'dynamic_{campo.nome_tecnico}'
                    
                    if campo.tipo_campo == 'select':
                        opcoes = OpcaoCampo.objects.filter(campo=campo).values_list('valor', 'valor')
                        choices = [('', '---------')] + list(opcoes)
                        self.fields[field_name] = forms.ChoiceField(
                            choices=choices, label=campo.nome_label, required=False,
                            widget=forms.Select(attrs={'class': 'form-select'})
                        )
                    else:
                        field_class_map = {
                            'text': forms.CharField,
                            'textarea': lambda **kw: forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), **kw),
                            'number': forms.DecimalField,
                            'integer': forms.IntegerField,
                            'date': forms.DateField(widget=forms.DateInput(attrs={'type': 'date'})),
                            'url': forms.URLField,
                        }
                        field_class = field_class_map.get(campo.tipo_campo, forms.CharField)
                        self.fields[field_name] = field_class(label=campo.nome_label, required=False)
                        self.fields[field_name].widget.attrs.update({'class': 'form-control'})

                    try:
                        valor_obj = ValorCampoCaso.objects.get(caso=self.instance, campo=campo)
                        valor_antigo = valor_obj.valor
                        if campo.tipo_campo == 'select':
                            opcoes_validas = [choice[0] for choice in self.fields[field_name].choices]
                            if valor_antigo in opcoes_validas:
                                self.fields[field_name].initial = valor_antigo
                        else:
                            self.fields[field_name].initial = valor_antigo
                    except ValorCampoCaso.DoesNotExist:
                        pass
            except RegraCampo.DoesNotExist:
                pass

    def save(self, commit=True):
        instance = super().save(commit=False)
        dados_dinamicos = {name: value for name, value in self.cleaned_data.items() if name.startswith('dynamic_')}

        formato_titulo = f"Caso #{instance.id} - {instance.cliente}"
        try:
            regra = RegraCampo.objects.get(cliente=instance.cliente, produto=instance.produto)
            if regra.formato_titulo:
                formato_titulo = regra.formato_titulo
        except RegraCampo.DoesNotExist:
            pass

        contexto_dict = {
            'id': instance.id or '',
            'cliente': str(instance.cliente),
            'produto': str(instance.produto),
            'advogado_responsavel': str(self.cleaned_data.get('advogado_responsavel', ''))
        }
        for nome_completo, valor in dados_dinamicos.items():
            nome_tecnico = nome_completo.replace('dynamic_', '', 1)
            contexto_dict[nome_tecnico] = valor or ''
        
        template = Template(formato_titulo)
        contexto = Context(contexto_dict)
        instance.titulo_caso = template.render(contexto)
        
        if commit:
            instance.save()
            self.save_m2m()

        for nome_completo, valor in dados_dinamicos.items():
            nome_tecnico = nome_completo.replace('dynamic_', '', 1)
            try:
                campo_obj = Campo.objects.get(nome_tecnico=nome_tecnico)
                ValorCampoCaso.objects.update_or_create(
                    caso=instance, campo=campo_obj,
                    defaults={'valor': valor or ''}
                )
            except Campo.DoesNotExist:
                continue
        
        return instance

    class Meta:
        model = Caso
        fields = [
            'cliente', 'produto', 'status', 'advogado_responsavel',
            'data_entrada_rca','data_encerramento', 'titulo_caso'
        ]

# ==============================================================================
# OUTROS FORMULÁRIOS
# ==============================================================================
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

class TarefaForm(forms.ModelForm):
    prazo_final = forms.DateField(
        label="Prazo (opcional, substitui o padrão)",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    class Meta:
        model = Tarefa
        fields = ['tipo_tarefa', 'responsavel', 'observacao', 'prazo_final']
        widgets = {
            'tipo_tarefa': forms.Select(attrs={'class': 'form-select'}),
            'responsavel': forms.Select(attrs={'class': 'form-select'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'prazo_final': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        labels = {
            'prazo_final': 'Prazo (se diferente do padrão)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['prazo_final'].required = False
      

class TimesheetForm(forms.ModelForm):
    tempo_str = forms.CharField(
        label="Tempo Gasto (HH:MM)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 02:30'}),
        help_text="Informe o tempo no formato horas e minutos."
    )
    class Meta:
        model = Timesheet
        fields = ['data_execucao', 'profissional', 'tempo_str', 'descricao']
        widgets = {
            'data_execucao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'profissional': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class TarefaConclusaoForm(forms.ModelForm):
    class Meta:
        model = Tarefa
        fields = ['descricao_conclusao']
        widgets = {'descricao_conclusao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'required': True})}
        labels = {'descricao_conclusao': "Descreva o que foi feito para concluir esta tarefa"}
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['descricao_conclusao'].required = True