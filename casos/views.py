from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, DetailView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.conf import settings
from configuracoes.models import LogoConfig
import openpyxl
import json
from django.utils import timezone
import os
from weasyprint import HTML
from openpyxl.styles import Font,Alignment
from io import BytesIO
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q 
from notificacoes.servicos import enviar_notificacao
from .microsoft_graph_service import (
    criar_pasta_caso, criar_subpastas, listar_arquivos_e_pastas, 
    upload_arquivo, deletar_item, criar_nova_pasta, obter_url_preview
)
from .microsoft_graph_service import enviar_email as enviar_email_service
from .models import (
    Caso, Produto, Campo, ValorCampoCaso, FluxoInterno, Tarefa, Timesheet, 
    TipoTarefa, FaseWorkflow, Advogado, Status, Analista, Cliente, Workflow, 
    AndamentoCaso, EmailTemplate, UserSignature, EmailCaso
)
from .forms import (
    CasoCreateForm, CasoUpdateForm, 
    FluxoInternoForm, TarefaForm, TimesheetForm, TarefaConclusaoForm, AndamentoCasoForm,
    EnviarEmailForm
)
from .tasks import buscar_detalhes_email_enviado, processar_email_webhook

Usuario = get_user_model()


@login_required
def get_campos_for_produto_ajax(request):
    produto_id = request.GET.get('produto_id')
    caso_id = request.GET.get('caso_id')
    if not produto_id:
        return JsonResponse([], safe=False)
    campos_data = []
    campos = Campo.objects.filter(produtos__id=produto_id).order_by('nome_label')
    for campo in campos:
        valor_existente = ''
        if caso_id:
            try:
                valor_obj = ValorCampoCaso.objects.get(caso_id=caso_id, campo=campo)
                valor_existente = valor_obj.valor
            except ValorCampoCaso.DoesNotExist:
                pass
        campos_data.append({'nome_label': campo.nome_label, 'nome_tecnico': campo.nome_tecnico, 'tipo_campo': campo.tipo_campo, 'valor': valor_existente})
    return JsonResponse(campos_data, safe=False)

class CasoListView(LoginRequiredMixin, ListView):
    model = Caso
    template_name = 'casos/caso_list.html'
    context_object_name = 'casos'
    paginate_by = 15
    def get_queryset(self):
        return get_casos_filtrados(self.request)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        context['querystring'] = query_params.urlencode()
        context['clientes_list'] = Cliente.objects.all().order_by('nome_razao_social')
        context['status_list'] = Status.objects.all().order_by('nome')
        context['fases_list'] = FaseWorkflow.objects.all().order_by('workflow__nome', 'ordem')
        context['produtos_list'] = Produto.objects.all().order_by('nome')
        return context

class CasoCreateView(LoginRequiredMixin, CreateView):
    model = Caso
    form_class = CasoCreateForm
    template_name = 'casos/caso_form_create.html'
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        
        # --- LÓGICA DO SHAREPOINT (continua igual) ---
        try:
            nome_base_pasta = f"{self.object.id}"
            caracteres_invalidos = r'<>:"/\|?*'
            nome_pasta_sanitizado = nome_base_pasta
            for char in caracteres_invalidos:
                nome_pasta_sanitizado = nome_pasta_sanitizado.replace(char, '-')
            
            pasta_criada_json = criar_pasta_caso(nome_pasta_sanitizado)
            
            if pasta_criada_json:
                self.object.sharepoint_folder_id = pasta_criada_json['id']
                self.object.sharepoint_folder_url = pasta_criada_json['webUrl']
                self.object.save(update_fields=['sharepoint_folder_id', 'sharepoint_folder_url'])
                id_pasta_pai = pasta_criada_json['id']
                subpastas = [p.nome_pasta for p in self.object.produto.estrutura_pastas.all()]
                if subpastas:
                    subpastas_sanitizadas = []
                    for nome_sub in subpastas:
                        nome_limpo = nome_sub
                        for char in caracteres_invalidos:
                            nome_limpo = nome_limpo.replace(char, '-')
                        subpastas_sanitizadas.append(nome_limpo)
                    criar_subpastas(id_pasta_pai, subpastas_sanitizadas)
                messages.success(self.request, "Caso criado e pasta gerada no SharePoint com sucesso.")
            else:
                 messages.warning(self.request, "O caso foi criado, mas não foi possível criar a pasta no SharePoint.")
        except Exception as e:
            print(f"ERRO CRÍTICO NA INTEGRAÇÃO COM SHAREPOINT (VIEW): {e}")
            messages.error(self.request, f"O caso foi criado, mas falhou ao criar a pasta no SharePoint: {e}")
        
        # --- NOVA LÓGICA DE NOTIFICAÇÃO ---
        try:
            # Prepara o contexto com as informações necessárias para o template do e-mail
            contexto_notificacao = {
                'caso': self.object,
                'usuario_acao': self.request.user  # Passa o usuário logado como remetente
            }
            
            # Chama o nosso serviço de notificação para o evento 'novo-caso-criado'
            sucesso, mensagem = enviar_notificacao(
                slug_evento='novo-caso-criado', 
                contexto=contexto_notificacao
            )
            
            # Adiciona uma mensagem de feedback para o usuário sobre a notificação
            if sucesso:
                messages.info(self.request, "Notificações de novo caso foram enviadas.")
            else:
                # O 'mensagem' aqui vem do retorno da função enviar_notificacao
                messages.warning(self.request, f"Não foi possível enviar as notificações: {mensagem}")

        except Exception as e:
            print(f"ERRO CRÍTICO AO ENVIAR NOTIFICAÇÃO DE NOVO CASO: {e}")
            messages.error(self.request, f"Ocorreu um erro inesperado ao tentar enviar as notificações: {e}")

        # Redireciona para a página de edição do caso, como antes
        return redirect(self.get_success_url())

class CasoUpdateView(LoginRequiredMixin, UpdateView):
    model = Caso
    form_class = CasoUpdateForm
    template_name = 'casos/caso_form_update.html'
    def get_success_url(self):
        return reverse_lazy('casos:caso_detail', kwargs={'pk': self.object.pk})

class CasoDetailView(LoginRequiredMixin, DetailView):
    model = Caso
    template_name = 'casos/caso_detail.html'
    context_object_name = 'caso'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        caso = self.get_object()

        # ---- Lógica para a aba de Anexos do SharePoint ----
        context['arquivos_sharepoint'] = []
        if caso.sharepoint_folder_id:
            context['arquivos_sharepoint'] = listar_arquivos_e_pastas(caso.sharepoint_folder_id)
        
        # ---- Lógica para a nova aba de E-mail ----
        email_form = EnviarEmailForm()
        
        # Carrega os modelos e assinaturas para os dropdowns
        templates = EmailTemplate.objects.all()
        assinaturas = UserSignature.objects.filter(usuario=self.request.user)
        
        # Popula os choices dos campos do formulário
        email_form.fields['modelo_id'].choices = [('', '---------')] + [(t.id, t.nome) for t in templates]
        email_form.fields['assinatura_id'].choices = [('', 'Nenhuma')] + [(a.id, a.nome) for a in assinaturas]
        
        context['email_form'] = email_form
        
        # Envia os dados dos templates e assinaturas como JSON para o JavaScript
        context['email_templates_json'] = json.dumps({t.id: {'assunto': t.assunto, 'corpo': t.corpo} for t in templates})
        context['user_signatures_json'] = json.dumps({a.id: a.corpo_html for a in assinaturas})

        # Carrega os e-mails já associados a este caso
        context['emails_do_caso'] = EmailCaso.objects.filter(caso=caso)

        # ---- Formulários para as outras abas ----
        context['fluxo_interno_form'] = FluxoInternoForm()
        context['tarefa_form'] = TarefaForm()
        context['timesheet_form'] = TimesheetForm()
        context['conclusao_form'] = TarefaConclusaoForm()
        context['andamento_caso_form'] = AndamentoCasoForm()
        
        return context

@login_required
def add_andamento_caso(request, caso_pk):
    caso = get_object_or_404(Caso, pk=caso_pk)
    if request.method == 'POST':
        form = AndamentoCasoForm(request.POST)
        if form.is_valid():
            andamento = form.save(commit=False)
            andamento.caso = caso
            andamento.usuario_criacao = request.user
            andamento.save()
            messages.success(request, "Andamento adicionado com sucesso.")
    return redirect(reverse('casos:caso_detail', kwargs={'pk': caso_pk}) + '#andamento-caso-tab-pane')

@login_required
def exportar_andamentos_excel(request, caso_pk):
    caso = get_object_or_404(Caso, pk=caso_pk)
    andamentos = caso.andamentos_caso.all()
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="andamentos_caso_{caso.id}.xlsx"'
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Andamentos'
    sheet.merge_cells('A1:C1')
    titulo_cell = sheet['A1']
    titulo_cell.value = f"Relatório de Andamentos - Caso: {caso.titulo_caso}"
    titulo_cell.font = Font(bold=True, size=14)
    titulo_cell.alignment = Alignment(horizontal='center')
    sheet.append([])
    headers = ['Data', 'Usuário', 'Descrição']
    sheet.append(headers)
    for cell in sheet[3]:
        cell.font = Font(bold=True)
    for andamento in andamentos:
        sheet.append([andamento.data_andamento.strftime("%d/%m/%Y %H:%M"), str(andamento.usuario_criacao) if andamento.usuario_criacao else "Sistema", andamento.descricao])
    workbook.save(response)
    return response

@login_required
def exportar_andamentos_pdf(request, caso_pk):
    caso = get_object_or_404(Caso, pk=caso_pk)
    andamentos = caso.andamentos_caso.all()
    logo_url = None
    try:
        logo_config = LogoConfig.objects.get(ativo=True)
        if logo_config.logo:
            logo_url = request.build_absolute_uri(logo_config.logo.url)
    except LogoConfig.DoesNotExist:
        pass
    context = {'caso': caso, 'andamentos': andamentos, 'logo_url': logo_url}
    html_string = render_to_string('casos/pdf/andamento_pdf_template.html', context)
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf = html.write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="andamentos_caso_{caso.id}.pdf"'
    return response

@login_required
def add_fluxo_interno(request, caso_pk):
    caso = get_object_or_404(Caso, pk=caso_pk)
    if request.method == 'POST':
        form = FluxoInternoForm(request.POST)
        if form.is_valid():
            fluxo = form.save(commit=False)
            fluxo.caso = caso
            fluxo.usuario_criacao = request.user
            fluxo.save()
            messages.success(request, "Registro adicionado ao Fluxo Interno com sucesso.")
    return redirect(reverse('casos:caso_detail', kwargs={'pk': caso_pk}) + '#fluxo-interno-tab-pane')

@login_required
def add_tarefa(request, caso_pk):
    caso = get_object_or_404(Caso, pk=caso_pk)
    if request.method == 'POST':
        form = TarefaForm(request.POST)
        if form.is_valid():
            tarefa = form.save(commit=False)
            tarefa.caso = caso
            prazo_custom = form.cleaned_data.get('prazo_final_customizado')
            if prazo_custom:
                tarefa.prazo_final = prazo_custom
            tarefa.save()
            messages.success(request, "Tarefa adicionada com sucesso.")
    return redirect(reverse('casos:caso_detail', kwargs={'pk': caso_pk}) + '#tarefas-tab-pane')

@login_required
def concluir_tarefa(request, tarefa_pk):
    tarefa = get_object_or_404(Tarefa, pk=tarefa_pk)
    if request.method == 'POST':
        form = TarefaConclusaoForm(request.POST, instance=tarefa)
        if form.is_valid():
            tarefa_concluida = form.save(commit=False)
            tarefa_concluida.status = 'C'
            tarefa_concluida.data_conclusao = timezone.now()
            tarefa_concluida.save()
            FluxoInterno.objects.create(caso=tarefa.caso, data_fluxo=timezone.now().date(), usuario_criacao=request.user, descricao=f"Tarefa Concluída: {tarefa.tipo_tarefa.nome}\nDescrição: {tarefa_concluida.descricao_conclusao}")
    return redirect(reverse('casos:caso_detail', kwargs={'pk': tarefa.caso.pk}) + '#tarefas-tab-pane')

@login_required
def reabrir_tarefa(request, tarefa_pk):
    tarefa = get_object_or_404(Tarefa, pk=tarefa_pk)
    if request.method == 'POST':
        tarefa.status = 'P'
        tarefa.data_conclusao = None
        tarefa.save()
    return redirect(reverse('casos:caso_detail', kwargs={'pk': tarefa.caso.pk}) + '#tarefas-tab-pane')

@login_required
def deletar_tarefa(request, tarefa_pk):
    tarefa = get_object_or_404(Tarefa, pk=tarefa_pk)
    caso_pk = tarefa.caso.pk
    if request.method == 'POST':
        tarefa.delete()
    return redirect(reverse('casos:caso_detail', kwargs={'pk': caso_pk}) + '#tarefas-tab-pane')

@login_required
def add_timesheet(request, caso_pk):
    caso = get_object_or_404(Caso, pk=caso_pk)
    if request.method == 'POST':
        form = TimesheetForm(request.POST)
        if form.is_valid():
            timesheet = form.save(commit=False)
            timesheet.caso = caso
            tempo_str = form.cleaned_data['tempo_str']
            horas, minutos = map(int, tempo_str.split(':'))
            timesheet.tempo = timedelta(hours=horas, minutes=minutos)
            timesheet.save()
    return redirect(reverse('casos:caso_detail', kwargs={'pk': caso_pk}) + '#timesheet-tab-pane')

@login_required
def delete_timesheet(request, ts_pk):
    timesheet = get_object_or_404(Timesheet, pk=ts_pk)
    caso_pk = timesheet.caso.pk
    if request.method == 'POST':
        timesheet.delete()
    return redirect(reverse('casos:caso_detail', kwargs={'pk': caso_pk}) + '#timesheet-tab-pane')

class TarefaListView(LoginRequiredMixin, ListView):
    model = Tarefa
    template_name = 'casos/tarefa_list.html'
    context_object_name = 'tarefas'
    paginate_by = 20
    def get_queryset(self):
        queryset = Tarefa.objects.select_related('caso', 'tipo_tarefa', 'responsavel').order_by('-data_criacao')
        responsavel_id = self.request.GET.get('responsavel')
        if responsavel_id:
            queryset = queryset.filter(responsavel_id=responsavel_id)
        return queryset
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['responsaveis'] = Usuario.objects.filter(is_staff=True).order_by('username')
        context['status_choices'] = Tarefa.STATUS_TAREFA_CHOICES
        context['conclusao_form'] = TarefaConclusaoForm()
        return context

def get_casos_filtrados(request):
    queryset = Caso.objects.select_related('cliente', 'produto', 'status', 'fase_atual_workflow', 'advogado_responsavel__user').order_by('-id')
    
    titulo = request.GET.get('titulo', '')
    cliente_id = request.GET.get('cliente', '')
    produto_id = request.GET.get('produto', '')
    status_id = request.GET.get('status', '')
    fase_id = request.GET.get('fase', '')

    if titulo:
        # --- CORREÇÃO DO PONTO 1 (INÍCIO) ---
        # Cria uma query base para os campos de texto
        query_texto = (
            Q(titulo_caso__icontains=titulo) |
            Q(valores_dinamicos__valor__icontains=titulo, valores_dinamicos__campo__nome_tecnico='aviso') |
            Q(valores_dinamicos__valor__icontains=titulo, valores_dinamicos__campo__nome_tecnico='segurado')
        )
        
        # Se o texto digitado for um número, adiciona a busca por ID à query
        if titulo.isdigit():
            query_final = query_texto | Q(id=titulo)
        else:
            query_final = query_texto
            
        queryset = queryset.filter(query_final).distinct()
        # --- CORREÇÃO DO PONTO 1 (FIM) ---
    
    if cliente_id:
        queryset = queryset.filter(cliente_id=cliente_id)
    if produto_id:
        queryset = queryset.filter(produto_id=produto_id)
    if status_id:
        queryset = queryset.filter(status_id=status_id)
    if fase_id:
        queryset = queryset.filter(fase_atual_workflow_id=fase_id)

    return queryset

class CasoPesquisaView(LoginRequiredMixin, ListView):
    model = Caso
    template_name = 'casos/caso_pesquisa.html'
    context_object_name = 'casos'
    paginate_by = 25
    def get_queryset(self):
        return get_casos_filtrados(self.request)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = "Pesquisa Avançada de Casos"
        context['clientes'] = Cliente.objects.all()
        context['advogados'] = Advogado.objects.all()
        context['status_list'] = Status.objects.all()
        context['analistas'] = Analista.objects.all()
        return context

@login_required
def exportar_casos_excel(request):
    casos_filtrados = get_casos_filtrados(request)
    cabecalhos_fixos = ['ID do Caso', 'Título do Caso', 'Cliente', 'Produto', 'Status', 'Fase do Workflow', 'Responsável', 'Data de Entrada']
    campos_personalizados_ids = ValorCampoCaso.objects.filter(caso__in=casos_filtrados).values_list('campo_id', flat=True).distinct()
    campos_personalizados = Campo.objects.filter(pk__in=campos_personalizados_ids).order_by('nome_label')
    cabecalhos_personalizados = [cp.nome_label for cp in campos_personalizados]
    cabecalho_final = cabecalhos_fixos + cabecalhos_personalizados
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="relatorio_casos.xlsx"'
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Relatório de Casos'
    sheet.append(cabecalho_final)
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for caso in casos_filtrados:
        valores_personalizados_dict = {vc.campo.nome_label: vc.valor for vc in caso.valores_dinamicos.all()}
        linha = [caso.id, caso.titulo_caso, str(caso.cliente), str(caso.produto), str(caso.status), caso.fase_atual_workflow.nome if caso.fase_atual_workflow else "-", str(caso.advogado_responsavel) if caso.advogado_responsavel else "-", caso.data_entrada_rca.strftime("%d/%m/%Y") if caso.data_entrada_rca else "-"]
        for cabecalho_pers in cabecalhos_personalizados:
            valor = valores_personalizados_dict.get(cabecalho_pers, "-")
            linha.append(valor)
        sheet.append(linha)
    workbook.save(response)
    return response

@login_required
def exportar_timesheet_excel(request, caso_pk):
    caso = get_object_or_404(Caso, pk=caso_pk)
    timesheets = caso.timesheets.all().order_by('data_execucao')
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="timesheet_caso_{caso.id}.xlsx"'
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Lançamentos de Horas'
    sheet.merge_cells('A1:D1')
    titulo_cell = sheet['A1']
    titulo_cell.value = f"Relatório de Horas - Caso: {caso.titulo_caso}"
    titulo_cell.font = Font(bold=True, size=14)
    titulo_cell.alignment = Alignment(horizontal='center')
    sheet.row_dimensions[1].height = 20
    headers = ['Data de Execução', 'Profissional', 'Tempo Gasto (HH:MM)', 'Descrição da Atividade']
    sheet.append([])
    sheet.append(headers)
    for cell in sheet[3]:
        cell.font = Font(bold=True)
    sheet.column_dimensions['A'].width, sheet.column_dimensions['B'].width, sheet.column_dimensions['C'].width, sheet.column_dimensions['D'].width = 18, 30, 20, 60
    for ts in timesheets:
        data_formatada = ts.data_execucao.strftime("%d/%m/%Y")
        horas, minutos = ts.tempo.seconds // 3600, (ts.tempo.seconds % 3600) // 60
        tempo_formatado = f"{horas:02d}:{minutos:02d}"
        sheet.append([data_formatada, ts.profissional.get_full_name() or ts.profissional.username, tempo_formatado, ts.descricao])
    if timesheets:
        proxima_linha = sheet.max_row + 1
        total_label_cell = sheet.cell(row=proxima_linha, column=2)
        total_label_cell.value, total_label_cell.font, total_label_cell.alignment = "Total de Horas:", Font(bold=True), Alignment(horizontal='right')
        total_value_cell = sheet.cell(row=proxima_linha, column=3)
        total_value_cell.value, total_value_cell.font = caso.total_horas_trabalhadas, Font(bold=True)
    workbook.save(response)
    return response

@login_required
def exportar_timesheet_pdf(request, caso_pk):
    caso, timesheets = get_object_or_404(Caso, pk=caso_pk), caso.timesheets.all().order_by('data_execucao')
    logo_url_completa = None
    try:
        logo_config = LogoConfig.objects.get(ativo=True)
        if logo_config.logo:
            logo_url_completa = request.build_absolute_uri(logo_config.logo.url)
    except LogoConfig.DoesNotExist:
        pass
    context = {'caso': caso, 'timesheets': timesheets, 'total_horas': caso.total_horas_trabalhadas, 'logo_url': logo_url_completa}
    html_string = render_to_string('casos/pdf/timesheet_pdf_template.html', context)
    base_url = request.build_absolute_uri('/')
    html = HTML(string=html_string, base_url=base_url)
    pdf = html.write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="timesheet_caso_{caso.id}.pdf"'
    return response

@login_required
def gerar_caso_pdf(request, caso_pk):
    caso = get_object_or_404(Caso, pk=caso_pk)
    html_string = render_to_string('casos/caso_pdf_template.html', {'caso': caso})
    html = HTML(string=html_string)
    pdf = html.write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="caso_{caso_pk}.pdf"'
    return response

@login_required
def enviar_timesheet_email(request, caso_pk):
    caso = get_object_or_404(Caso, pk=caso_pk)
    timesheets = caso.timesheets.all().order_by('data_execucao')
    output = BytesIO()
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Lançamentos'
    sheet.merge_cells('A1:D1')
    titulo_cell = sheet['A1']
    titulo_cell.value, titulo_cell.font, titulo_cell.alignment = f"Relatório de Horas - Caso: {caso.titulo_caso}", Font(bold=True, size=14), Alignment(horizontal='center')
    sheet.row_dimensions[1].height = 20
    headers = ['Data de Execução', 'Profissional', 'Tempo Gasto (HH:MM)', 'Descrição da Atividade']
    sheet.append([])
    sheet.append(headers)
    for cell in sheet[3]:
        cell.font = Font(bold=True)
    for ts in timesheets:
        data_formatada, horas, minutos = ts.data_execucao.strftime("%d/%m/%Y"), ts.tempo.seconds // 3600, (ts.tempo.seconds % 3600) // 60
        tempo_formatado = f"{horas:02d}:{minutos:02d}"
        sheet.append([data_formatada, ts.profissional.get_full_name() or ts.profissional.username, tempo_formatado, ts.descricao])
    if timesheets:
        proxima_linha = sheet.max_row + 1
        sheet.cell(row=proxima_linha, column=3).value, sheet.cell(row=proxima_linha, column=3).font, sheet.cell(row=proxima_linha, column=3).alignment = "Total de Horas:", Font(bold=True), Alignment(horizontal='right')
        sheet.cell(row=proxima_linha, column=4).value, sheet.cell(row=proxima_linha, column=4).font = caso.total_horas_trabalhadas, Font(bold=True)
    workbook.save(output)
    contexto = {'caso': caso, 'usuario_acao': request.user}
    nome_anexo = f'timesheet_caso_{caso.id}.xlsx'
    sucesso, mensagem = enviar_notificacao(slug_evento='envio_relatorio_timesheet', contexto=contexto, anexo_buffer=output, nome_anexo=nome_anexo, content_type_anexo='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    if sucesso: messages.success(request, mensagem)
    else: messages.error(request, mensagem)
    return redirect(reverse('casos:caso_detail', kwargs={'pk': caso_pk}) + '#timesheet-tab-pane')

class TimesheetUpdateView(LoginRequiredMixin, UpdateView):
    model = Timesheet
    form_class = TimesheetForm
    template_name = 'casos/timesheet_form.html'
    def get_success_url(self):
        return reverse_lazy('casos:caso_detail', kwargs={'pk': self.object.caso.pk}) + '#timesheet-tab-pane'
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.object.tempo:
            total_seconds = int(self.object.tempo.total_seconds())
            horas, minutos = total_seconds // 3600, (total_seconds % 3600) // 60
            form.fields['tempo_str'].initial = f"{horas:02d}:{minutos:02d}"
        return form

class KanbanView(LoginRequiredMixin, TemplateView):
    template_name = 'casos/kanban_board.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = "Kanban de Casos por Fase"
        workflow_principal = Workflow.objects.first()
        if not workflow_principal:
            context['kanban_columns'] = {}
            return context
        profissional_id, status_id = self.request.GET.get('profissional'), self.request.GET.get('status')
        casos_filtrados = Caso.objects.filter(fase_atual_workflow__workflow=workflow_principal)
        if profissional_id: casos_filtrados = casos_filtrados.filter(advogado_responsavel__user__id=profissional_id)
        if status_id: casos_filtrados = casos_filtrados.filter(status__id=status_id)
        kanban_columns = {}
        fases_do_workflow = workflow_principal.fases.order_by('ordem')
        for fase in fases_do_workflow:
            kanban_columns[fase] = list(casos_filtrados.filter(fase_atual_workflow=fase))
        context['kanban_columns'] = kanban_columns
        context['profissionais'] = Usuario.objects.filter(is_staff=True)
        context['status_list'] = Status.objects.all()
        return context

@login_required
def update_caso_fase_ajax(request):
    if request.method == 'POST':
        try:
            caso_id, nova_fase_id = request.POST.get('caso_id'), request.POST.get('nova_fase_id')
            caso, nova_fase = get_object_or_404(Caso, pk=caso_id), get_object_or_404(FaseWorkflow, pk=nova_fase_id)
            caso.fase_atual_workflow = nova_fase
            if nova_fase.atualiza_status_para:
                caso.status = nova_fase.atualiza_status_para
            caso.save()
            return JsonResponse({'status': 'success', 'message': f'Caso #{caso_id} movido para {nova_fase.nome}.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)

class TimesheetListView(LoginRequiredMixin, ListView):
    model = Timesheet
    template_name = 'casos/timesheet_list.html'
    context_object_name = 'timesheets'
    paginate_by = 20
    def get_queryset(self):
        queryset = Timesheet.objects.select_related('caso', 'profissional').order_by('-data_execucao')
        profissional_id = self.request.GET.get('profissional')
        if profissional_id: queryset = queryset.filter(profissional_id=profissional_id)
        data_de = self.request.GET.get('data_de')
        if data_de: queryset = queryset.filter(data_execucao__gte=data_de)
        data_ate = self.request.GET.get('data_ate')
        if data_ate: queryset = queryset.filter(data_execucao__lte=data_ate)
        return queryset
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = "Visão Geral de Timesheet"
        context['profissionais'] = get_user_model().objects.filter(is_staff=True)
        return context

class CasoPesquisaView(LoginRequiredMixin, ListView):
    model = Caso
    template_name = 'casos/caso_pesquisa.html'
    context_object_name = 'casos'
    paginate_by = 25
    def get_queryset(self):
        return get_casos_filtrados(self.request)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = "Pesquisa Avançada de Casos"
        context['clientes'] = Cliente.objects.all()
        context['advogados'] = Advogado.objects.all()
        context['status_list'] = Status.objects.all()
        context['analistas'] = Analista.objects.all()
        return context

@login_required
def criar_pasta_anexo_view(request, caso_pk):
    if request.method == 'POST':
        caso = get_object_or_404(Caso, pk=caso_pk)
        nome_nova_pasta = request.POST.get('nome_pasta')
        if nome_nova_pasta and caso.sharepoint_folder_id:
            caracteres_invalidos = r'<>:"/\|?*'
            for char in caracteres_invalidos:
                nome_nova_pasta = nome_nova_pasta.replace(char, '-')
            resultado = criar_nova_pasta(caso.sharepoint_folder_id, nome_nova_pasta)
            if resultado:
                messages.success(request, f"Pasta '{nome_nova_pasta}' criada com sucesso.")
            else:
                messages.error(request, "Falha ao criar a nova pasta no SharePoint.")
    return redirect(reverse('casos:caso_detail', kwargs={'pk': caso_pk}) + '#anexos-sharepoint-tab-pane')

@login_required
def upload_arquivo_anexo_view(request, caso_pk):
    if request.method == 'POST':
        caso = get_object_or_404(Caso, pk=caso_pk)
        arquivos_upload = request.FILES.getlist('arquivo')
        id_pasta_pai = request.POST.get('parent_folder_id', caso.sharepoint_folder_id)
        if not arquivos_upload:
            messages.warning(request, "Nenhum arquivo foi selecionado.")
        if arquivos_upload and id_pasta_pai:
            sucessos, falhas = 0, 0
            for arquivo in arquivos_upload:
                nome_arquivo, conteudo_arquivo = arquivo.name, arquivo.read()
                resultado = upload_arquivo(id_pasta_pai, nome_arquivo, conteudo_arquivo)
                if resultado: 
                    sucessos += 1
                else:
                    falhas += 1
                    messages.error(request, f"Falha ao enviar o arquivo: {nome_arquivo}")
            if sucessos > 0: 
                messages.success(request, f"{sucessos} arquivo(s) enviado(s) com sucesso.")
            if falhas == 0 and sucessos == 0: 
                messages.error(request, "Falha ao enviar os arquivos para o SharePoint.")
    return redirect(reverse('casos:caso_detail', kwargs={'pk': caso_pk}) + '#anexos-sharepoint-tab-pane')

@login_required
def listar_subpasta_ajax(request, folder_id):
    if request.method == 'GET':
        return JsonResponse(listar_arquivos_e_pastas(folder_id), safe=False)
    return JsonResponse([], safe=False)

@login_required
def preview_arquivo_view(request, item_id):
    preview_url = obter_url_preview(item_id)
    if preview_url:
        return redirect(preview_url)
    messages.error(request, "Não foi possível gerar o link de visualização para este arquivo.")
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def deletar_item_view(request, caso_pk, item_id):
    if request.method == 'POST':
        if deletar_item(item_id):
            messages.success(request, "Item deletado com sucesso.")
        else:
            messages.error(request, "Falha ao deletar o item no SharePoint.")
    return redirect(reverse('casos:caso_detail', kwargs={'pk': caso_pk}) + '#anexos-sharepoint-tab-pane')

def add_generic_ajax(request, model_class):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        if nome:
            obj, created = model_class.objects.get_or_create(nome=nome)
            return JsonResponse({'id': obj.id, 'nome': obj.nome})
    return JsonResponse({'error': 'Requisição inválida'}, status=400)

@login_required
def add_status_ajax(request):
    from .models import Status
    return add_generic_ajax(request, Status)

@login_required
def add_analista_ajax(request):
    from .models import Analista
    return add_generic_ajax(request, Analista)

@login_required
def add_produto_ajax(request):
    from .models import Produto
    return add_generic_ajax(request, Produto)

@csrf_exempt
def microsoft_graph_webhook(request):
    """
    Esta view é o endpoint que recebe as notificações do Microsoft Graph.
    Ela não é para ser acessada por usuários, apenas pela Microsoft.
    """
    # --- PARTE 1: VALIDAÇÃO DA ASSINATURA ---
    # Quando criamos o webhook, a Microsoft envia uma requisição GET
    # com um 'validationToken' para garantir que nosso endpoint é real.
    if 'validationToken' in request.GET:
        validation_token = request.GET['validationToken']
        print(f"--- Recebida validação de Webhook da Microsoft: {validation_token} ---")
        # Responde com o token E com o status 200 OK
        return HttpResponse(validation_token, content_type='text/plain', status=200)

    # --- PARTE 2: RECEBIMENTO DAS NOTIFICAÇÕES ---
    # Depois de validado, a Microsoft enviará requisições POST com as notificações.
    if request.method == 'POST':
        try:
            notification_data = json.loads(request.body)
            print("--- Notificação de Webhook recebida! ---")
            
            for notification in notification_data.get('value', []):
                # A notificação nos diz QUAL recurso mudou (o ID do e-mail)
                # e o ID do usuário a quem pertence.
                user_id = notification['subscriptionId'] # Usaremos isso para encontrar o usuário
                resource_id = notification['resourceData']['id']
                
                print(f"Novo e-mail/mudança para a assinatura {user_id}. Recurso ID: {resource_id}")
                
                #
                # AQUI É ONDE A MÁGICA DO CELERY ENTRARÁ
                # processar_email_webhook.delay(user_id, resource_id)
                #
                
            # Respondemos IMEDIATAMENTE com status 202 para a Microsoft.
            # Se demorarmos, ela acha que deu erro e tenta de novo.
            return HttpResponse(status=202)

        except Exception as e:
            print(f"ERRO ao processar notificação de webhook: {e}")
            return HttpResponse(status=400) # Bad Request
    
    # Se alguém tentar acessar a URL com um método que não seja GET ou POST
    return HttpResponse("Endpoint de Webhook. Acesso inválido.", status=405)

@login_required
def enviar_email_view(request, caso_pk):
    caso = get_object_or_404(Caso, pk=caso_pk)
    if request.method == 'POST':
        form = EnviarEmailForm(request.POST)
        
        # Popula os choices para a validação
        templates = EmailTemplate.objects.all()
        assinaturas = UserSignature.objects.filter(usuario=request.user)
        form.fields['modelo_id'].choices = [('', '---------')] + [(t.id, t.nome) for t in templates]
        form.fields['assinatura_id'].choices = [('', 'Nenhuma')] + [(a.id, a.nome) for a in assinaturas]

        if form.is_valid():
            para = form.cleaned_data['para']
            assunto = form.cleaned_data['assunto']
            corpo = form.cleaned_data['corpo']
            remetente_email = request.user.email

            sucesso = enviar_email_service(remetente_email, para, assunto, corpo)

            if sucesso:
                # Criamos o objeto e o guardamos em uma variável
                email_caso_obj = EmailCaso.objects.create(
                    caso=caso,
                    microsoft_message_id=f"enviado_{timezone.now().timestamp()}",
                    de=remetente_email,
                    para=para,
                    assunto=assunto,
                    preview=corpo[:255],
                    corpo_html=corpo,
                    data_envio=timezone.now(),
                    is_sent=True
                )
                messages.success(request, "E-mail enviado e registrado com sucesso!")
                
                # --- CORREÇÃO APLICADA AQUI ---
                # Agora usamos 'email_caso_obj' que é o nome correto da variável
                buscar_detalhes_email_enviado.delay(remetente_email, email_caso_obj.id, para, assunto)
            else:
                messages.error(request, "Falha ao enviar o e-mail. Verifique o console para mais detalhes.")
        else:
            messages.error(request, f"Formulário inválido: {form.errors.as_text()}")
    
    return redirect(reverse('casos:caso_detail', kwargs={'pk': caso_pk}) + '#email-tab-pane')