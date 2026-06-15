import logging
import os
import secrets
import string
import uuid
import calendar
from datetime import datetime, timedelta
from html import unescape as _unescape

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models import Count, Q, Prefetch
from django.http import JsonResponse
from django.core.mail import get_connection, EmailMessage
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt
from .models import Cliente, Projeto, Chamado, ConfigurarEmail, PerfilUsuario, Sistema, Anexo, Resposta
from .forms import ClienteForm, ProjetoForm, ChamadoForm, UserRegisterForm, UsuarioEditForm, ConfigurarEmailForm, SistemaForm

logger = logging.getLogger(__name__)


_HORA_INICIO_UTIL = 8   # 08:00
_HORA_FIM_UTIL    = 18  # 18:00


def _role(user):
    return PerfilUsuario.role_for(user)


def _horas_uteis(dt_inicio, dt_fim):
    """Soma apenas os segundos que caem em seg–sex, 08h–18h (horário local)."""
    if dt_fim <= dt_inicio:
        return 0.0
    inicio = timezone.localtime(dt_inicio)
    fim    = timezone.localtime(dt_fim)
    total  = 0.0
    atual  = inicio
    while atual < fim:
        prox = (atual + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        trecho_fim = min(prox, fim)
        if atual.weekday() < 5:                          # seg=0 … sex=4
            j_ini = atual.replace(hour=_HORA_INICIO_UTIL, minute=0, second=0, microsecond=0)
            j_fim = atual.replace(hour=_HORA_FIM_UTIL,    minute=0, second=0, microsecond=0)
            ov_ini = max(atual, j_ini)
            ov_fim = min(trecho_fim, j_fim)
            if ov_fim > ov_ini:
                total += (ov_fim - ov_ini).total_seconds()
        atual = prox
    return total / 3600


def _horas_extra(dt_inicio, dt_fim):
    """Soma o tempo total decorrido em sábados e domingos no intervalo."""
    if dt_fim <= dt_inicio:
        return 0.0
    inicio = timezone.localtime(dt_inicio)
    fim    = timezone.localtime(dt_fim)
    total  = 0.0
    atual  = inicio
    while atual < fim:
        prox = (atual + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        trecho_fim = min(prox, fim)
        if atual.weekday() >= 5:                         # sáb=5, dom=6
            total += (trecho_fim - atual).total_seconds()
        atual = prox
    return total / 3600


def _strip_html(texto):
    """Remove tags HTML do CKEditor e decodifica entidades para texto simples."""
    if not texto:
        return ''
    return _unescape(strip_tags(texto)).strip()


def _registrar_fechamento(chamado, status_anterior=None):
    if chamado.status == 'fechado' and not chamado.fechado_em:
        chamado.fechado_em = timezone.now()
    elif status_anterior == 'fechado' and chamado.status != 'fechado':
        chamado.fechado_em = None


def _build_destinatarios(chamado, extras=None):
    """Monta lista de e-mails únicos dos usuários do sistema ligados ao chamado.
    Não inclui o e-mail do cliente cadastrado — apenas usuários com login no sistema."""
    candidatos = []
    if chamado.criado_por and chamado.criado_por.email:
        candidatos.append(chamado.criado_por.email)
    if chamado.responsavel and chamado.responsavel.email:
        candidatos.append(chamado.responsavel.email)
    for obs in chamado.observadores.all():
        if obs.email:
            candidatos.append(obs.email)
    if extras:
        candidatos.extend(e for e in extras if e)
    vistos = set()
    resultado = []
    for email in candidatos:
        if email not in vistos:
            vistos.add(email)
            resultado.append(email)
    return resultado


def _build_link(request, path):
    """Retorna URL absoluta usando SITE_URL do settings quando configurado."""
    from django.conf import settings as _s
    base = getattr(_s, 'SITE_URL', '').rstrip('/')
    if base:
        return base + path
    return request.build_absolute_uri(path)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Bem-vindo de volta, {username}!")
                return redirect('dashboard')
        else:
            messages.error(request, "Usuário ou senha inválidos.")
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "Você saiu do sistema.")
    return redirect('login')


@login_required(login_url='login')
def cadastro_view(request):
    if _role(request.user) != 'admin':
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()

            _alphabet = string.ascii_letters + string.digits + '!@#$'
            temp_password = ''.join(secrets.choice(_alphabet) for _ in range(12))
            user.set_password(temp_password)
            user.save()

            nome_completo = user.get_full_name() or user.username
            link_sistema = _build_link(request, '/')
            ok_email, erro_email = disparar_email(
                f"[Digiana] Bem-vindo, {nome_completo}! Seu acesso foi criado.",
                (
                    f"Olá, {nome_completo}!\n\n"
                    f"Seu acesso ao sistema Digiana foi criado.\n\n"
                    f"Login:            {user.username}\n"
                    f"Senha temporária: {temp_password}\n\n"
                    f"Acesse o sistema pelo link abaixo e altere sua senha no primeiro login:\n"
                    f"{link_sistema}\n\n"
                    f"Esta é uma mensagem automática — não responda a este e-mail."
                ),
                [user.email],
            ) if user.email else (False, "E-mail não informado para este usuário.")

            if not ok_email:
                user.perfil.email_verificar = True
                user.perfil.save()
                messages.warning(
                    request,
                    f"Usuário '{user.username}' cadastrado. "
                    f"E-mail de boas-vindas não enviado — {erro_email} "
                    f"O usuário foi marcado como 'E-mail a verificar'.",
                )
            else:
                messages.success(request, f"Usuário '{user.username}' cadastrado e e-mail de boas-vindas enviado!")

            return redirect('usuarios_list')
    else:
        form = UserRegisterForm()
    return render(request, 'core/cadastro.html', {'form': form})


@login_required(login_url='login')
def dashboard(request):
    role = _role(request.user)

    if role == 'usuario':
        chamados = Chamado.objects.filter(
            Q(criado_por=request.user) | Q(observadores=request.user),
            excluido=False,
        ).distinct().order_by('-criado_em')
    else:
        chamados = Chamado.objects.filter(excluido=False).order_by('-criado_em')

    total_chamados = chamados.count()
    abertos = chamados.filter(status='aberto').count()
    em_progresso = chamados.filter(status='em_progresso').count()
    pendentes = chamados.filter(status='pendente').count()
    resolvidos = chamados.filter(status='resolvido').count()
    fechados = chamados.filter(status='fechado').count()

    paginator = Paginator(chamados, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'chamados':        page_obj,
        'page_obj':        page_obj,
        'total_chamados':  total_chamados,
        'abertos':         abertos,
        'em_progresso':    em_progresso,
        'pendentes':       pendentes,
        'resolvidos':      resolvidos,
        'fechados':        fechados,
        'user_role':       _role(request.user),
    }
    return render(request, 'core/dashboard.html', context)


@login_required(login_url='login')
def dashboard_stats(request):
    role = _role(request.user)
    qs = (
        Chamado.objects.filter(
            Q(criado_por=request.user) | Q(observadores=request.user),
            excluido=False,
        ).distinct()
        if role == 'usuario'
        else Chamado.objects.filter(excluido=False)
    )
    return JsonResponse({
        'total':        qs.count(),
        'abertos':      qs.filter(status='aberto').count(),
        'em_progresso': qs.filter(status='em_progresso').count(),
        'pendentes':    qs.filter(status='pendente').count(),
        'resolvidos':   qs.filter(status='resolvido').count(),
    })


@login_required(login_url='login')
def relatorios_view(request):
    if _role(request.user) != 'admin':
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')

    hoje = timezone.localdate()
    modo = request.GET.get('modo', 'mensal')
    if modo not in ('mensal', 'anual'):
        modo = 'mensal'

    try:
        ano = int(request.GET.get('ano', hoje.year))
    except (TypeError, ValueError):
        ano = hoje.year

    try:
        mes = int(request.GET.get('mes', hoje.month))
    except (TypeError, ValueError):
        mes = hoje.month
    mes = min(max(mes, 1), 12)

    anos = range(hoje.year - 4, hoje.year + 1)
    meses = [
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
        (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
        (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro'),
    ]
    periodo_fechado = ano < hoje.year or (modo == 'mensal' and ano == hoje.year and mes < hoje.month)
    if modo == 'anual':
        inicio = timezone.make_aware(datetime(ano, 1, 1))
        fim = timezone.make_aware(datetime(ano + 1, 1, 1))
        periodo_label = str(ano)
    else:
        ultimo_dia = calendar.monthrange(ano, mes)[1]
        inicio = timezone.make_aware(datetime(ano, mes, 1))
        fim = timezone.make_aware(datetime(ano, mes, ultimo_dia, 23, 59, 59, 999999)) + timedelta(microseconds=1)
        periodo_label = f"{dict(meses)[mes]} de {ano}"

    criados_qs = Chamado.objects.filter(criado_em__gte=inicio, criado_em__lt=fim)
    fechados_qs = Chamado.objects.filter(
        excluido=False,
        status='fechado',
        fechado_em__gte=inicio,
        fechado_em__lt=fim,
    )
    excluidos_qs = Chamado.objects.filter(
        excluido=True,
        excluido_em__gte=inicio,
        excluido_em__lt=fim,
    )
    operacionais_qs = Chamado.objects.filter(excluido=False)

    total_criados = criados_qs.count()
    total_fechados = fechados_qs.count()
    total_excluidos = excluidos_qs.count()
    taxa_fechamento = round((total_fechados / total_criados) * 100, 1) if total_criados else 0

    status_operacional = {
        'abertos': operacionais_qs.filter(status='aberto').count(),
        'em_progresso': operacionais_qs.filter(status='em_progresso').count(),
        'pendentes': operacionais_qs.filter(status='pendente').count(),
        'resolvidos': operacionais_qs.filter(status='resolvido').count(),
        'fechados': operacionais_qs.filter(status='fechado').count(),
    }
    chart_points = []
    if modo == 'anual':
        periodos = []
        for mes_ref in range(1, 13):
            periodo_inicio = timezone.make_aware(datetime(ano, mes_ref, 1))
            if mes_ref == 12:
                periodo_fim = timezone.make_aware(datetime(ano + 1, 1, 1))
            else:
                periodo_fim = timezone.make_aware(datetime(ano, mes_ref + 1, 1))
            periodos.append((dict(meses)[mes_ref][:3], periodo_inicio, periodo_fim))
    else:
        periodos = []
        for dia in range(1, calendar.monthrange(ano, mes)[1] + 1):
            periodo_inicio = timezone.make_aware(datetime(ano, mes, dia))
            periodo_fim = periodo_inicio + timedelta(days=1)
            periodos.append((str(dia), periodo_inicio, periodo_fim))

    max_chart_value = 1
    for label, periodo_inicio, periodo_fim in periodos:
        fechados_count = Chamado.objects.filter(
            excluido=False,
            status='fechado',
            fechado_em__gte=periodo_inicio,
            fechado_em__lt=periodo_fim,
        ).count()
        excluidos_count = Chamado.objects.filter(
            excluido=True,
            excluido_em__gte=periodo_inicio,
            excluido_em__lt=periodo_fim,
        ).count()
        max_chart_value = max(max_chart_value, fechados_count, excluidos_count)
        chart_points.append({
            'label': label,
            'fechados': fechados_count,
            'excluidos': excluidos_count,
        })

    for point in chart_points:
        point['fechados_pct'] = max(4, round((point['fechados'] / max_chart_value) * 100)) if point['fechados'] else 0
        point['excluidos_pct'] = max(4, round((point['excluidos'] / max_chart_value) * 100)) if point['excluidos'] else 0

    return render(request, 'core/relatorios.html', {
        'modo': modo,
        'ano': ano,
        'mes': mes,
        'anos': anos,
        'meses': meses,
        'periodo_fechado': periodo_fechado,
        'periodo_label': periodo_label,
        'total_criados': total_criados,
        'total_fechados': total_fechados,
        'total_excluidos': total_excluidos,
        'taxa_fechamento': taxa_fechamento,
        'status_operacional': status_operacional,
        'chart_points': chart_points,
    })


@login_required(login_url='login')
def clientes_list(request):
    if _role(request.user) == 'usuario':
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
    qs = Cliente.objects.all().annotate(num_projetos=Count('projetos')).order_by('nome')
    paginator = Paginator(qs, 20)
    page_obj  = paginator.get_page(request.GET.get('page'))
    return render(request, 'core/clientes_list.html', {
        'clientes':  page_obj,
        'page_obj':  page_obj,
        'total':     qs.count(),
        'user_role': _role(request.user),
    })


@login_required(login_url='login')
def cliente_create(request):
    if _role(request.user) == 'usuario':
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente cadastrado com sucesso!")
            return redirect('clientes_list')
    else:
        form = ClienteForm()
    return render(request, 'core/cliente_form.html', {'form': form, 'title': 'Cadastrar Cliente'})


@login_required(login_url='login')
def cliente_update(request, pk):
    if _role(request.user) == 'usuario':
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, f"Cliente '{cliente.nome}' atualizado com sucesso!")
            return redirect('clientes_list')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'core/cliente_form.html', {
        'form': form,
        'title': f'Editar Cliente — {cliente.nome}',
    })


@login_required(login_url='login')
def cliente_delete(request, pk):
    if _role(request.user) != 'admin':
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
    if request.method != 'POST':
        return redirect('clientes_list')
    cliente = get_object_or_404(Cliente, pk=pk)
    nome = cliente.nome
    cliente.delete()
    messages.success(request, f"Cliente '{nome}' e todos os seus projetos/chamados foram excluídos.")
    return redirect('clientes_list')


@login_required(login_url='login')
def projetos_list(request):
    if _role(request.user) == 'usuario':
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
    qs = Projeto.objects.select_related('cliente').annotate(
        num_chamados_abertos=Count('chamados', filter=Q(chamados__status='aberto', chamados__excluido=False))
    ).order_by('cliente__nome', 'nome')
    paginator = Paginator(qs, 20)
    page_obj  = paginator.get_page(request.GET.get('page'))
    return render(request, 'core/projetos_list.html', {
        'projetos':  page_obj,
        'page_obj':  page_obj,
        'total':     qs.count(),
        'user_role': _role(request.user),
    })


@login_required(login_url='login')
def projeto_create(request):
    if _role(request.user) == 'usuario':
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
    if request.method == 'POST':
        form = ProjetoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Projeto cadastrado com sucesso!")
            return redirect('projetos_list')
    else:
        form = ProjetoForm()
    return render(request, 'core/projeto_form.html', {'form': form, 'title': 'Cadastrar Projeto'})


@login_required(login_url='login')
def projeto_update(request, pk):
    if _role(request.user) == 'usuario':
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
    projeto = get_object_or_404(Projeto, pk=pk)
    if request.method == 'POST':
        form = ProjetoForm(request.POST, instance=projeto)
        if form.is_valid():
            form.save()
            messages.success(request, f"Projeto '{projeto.nome}' atualizado com sucesso!")
            return redirect('projetos_list')
    else:
        form = ProjetoForm(instance=projeto)
    return render(request, 'core/projeto_form.html', {
        'form':  form,
        'title': f'Editar Projeto — {projeto.nome}',
    })


@login_required(login_url='login')
def projeto_delete(request, pk):
    if _role(request.user) != 'admin':
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
    if request.method != 'POST':
        return redirect('projetos_list')
    projeto = get_object_or_404(Projeto, pk=pk)
    nome = projeto.nome
    projeto.delete()
    messages.success(request, f"Projeto '{nome}' e todos os seus chamados foram excluídos.")
    return redirect('projetos_list')


def disparar_email(assunto, mensagem, destinatarios):
    """Envia e-mail via API HTTP ou SMTP. Retorna (True, '') ou (False, mensagem_erro)."""
    import requests as _req
    config = ConfigurarEmail.objects.filter(ativo=True).first()
    if not config:
        return False, "Nenhuma configuração de e-mail ativa. Acesse Configuração de E-mail e ative uma."
    if not config.senha:
        return False, "Senha / chave de API não configurada. Acesse Configuração de E-mail."

    if config.usar_api:
        try:
            api_key = (config.senha or '').strip()
            remetente = (config.remetente or config.usuario or '').strip()
            payload = {
                'sender': {'email': remetente, 'name': 'Digiana'},
                'to': [{'email': e} for e in destinatarios],
                'subject': assunto,
                'textContent': mensagem,
            }
            resp = _req.post(
                'https://api.brevo.com/v3/smtp/email',
                json=payload,
                headers={
                    'accept': 'application/json',
                    'api-key': api_key,
                    'content-type': 'application/json',
                },
                timeout=15,
            )
            if resp.status_code == 201:
                return True, ''
            erro = f"API Brevo: HTTP {resp.status_code} — {resp.text[:300]}"
            logger.error("Falha API Brevo para %s — %s", destinatarios, erro)
            return False, erro
        except Exception as e:
            erro = str(e) or f'{type(e).__name__} (sem mensagem)'
            logger.error("Falha API Brevo para %s — %s", destinatarios, erro)
            return False, erro

    try:
        connection = get_connection(
            backend='core.email_backend.Py312SMTPEmailBackend',
            host=config.servidor_smtp,
            port=config.porta,
            username=config.usuario,
            password=config.senha,
            use_tls=config.use_tls,
            use_ssl=config.use_ssl,
            fail_silently=False,
            timeout=15,
        )
        from_email = config.remetente or config.usuario
        email = EmailMessage(
            subject=assunto,
            body=mensagem,
            from_email=from_email,
            to=destinatarios,
            connection=connection,
        )
        email.send()
        return True, ''
    except Exception as e:
        erro = str(e) or f'{type(e).__name__} (sem mensagem)'
        logger.error("Falha SMTP para %s — %s", destinatarios, erro)
        return False, erro


@login_required(login_url='login')
def chamados_list(request):
    role = _role(request.user)
    qs = (
        Chamado.objects.filter(
            Q(criado_por=request.user) | Q(observadores=request.user),
            excluido=False,
        ).distinct()
        if role == 'usuario'
        else Chamado.objects.filter(excluido=False)
    )

    status_f    = request.GET.get('status', '')
    prioridade_f = request.GET.get('prioridade', '')
    q           = request.GET.get('q', '').strip()

    if status_f:
        qs = qs.filter(status=status_f)
    if prioridade_f:
        qs = qs.filter(prioridade=prioridade_f)
    if q:
        qs = qs.filter(Q(titulo__icontains=q) | Q(projeto__nome__icontains=q) | Q(projeto__cliente__nome__icontains=q))

    qs = qs.select_related('projeto__cliente', 'responsavel', 'sistema').order_by('-criado_em')

    total = qs.count()
    paginator = Paginator(qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/chamados_list.html', {
        'chamados':          page_obj,
        'page_obj':          page_obj,
        'user_role':         role,
        'status_filter':     status_f,
        'prioridade_filter': prioridade_f,
        'q':                 q,
        'status_choices':    Chamado.STATUS_CHOICES,
        'prioridade_choices': Chamado.PRIORIDADE_CHOICES,
        'total':             total,
    })


@login_required(login_url='login')
def chamado_create(request):
    role = _role(request.user)
    if request.method == 'POST':
        form = ChamadoForm(request.POST)
        _aplicar_restricoes_usuario(form, request.user)
        if form.is_valid():
            chamado = form.save(commit=False)
            chamado.criado_por = request.user
            if role == 'usuario':
                chamado.status = 'aberto'
            elif not _status_permitido(chamado.status, request.user, chamado):
                chamado.status = 'aberto'
            _registrar_fechamento(chamado)
            chamado.save()
            form.save_m2m()
            _salvar_anexos(request, chamado)

            destinatarios = _build_destinatarios(chamado)
            if destinatarios:
                responsavel_nome = (
                    chamado.responsavel.get_full_name() or chamado.responsavel.username
                    if chamado.responsavel else 'Não atribuído'
                )
                link = _build_link(request, f'/chamados/{chamado.id}/')
                assunto = f"[Digiana] Chamado #{chamado.id} Registrado: {chamado.titulo}"
                mensagem = (
                    f"Olá,\n\n"
                    f"O chamado abaixo foi registrado no sistema Digiana.\n\n"
                    f"Chamado:     #{chamado.id} — {chamado.titulo}\n"
                    f"Projeto:     {chamado.projeto.nome}\n"
                    f"Sistema:     {chamado.sistema or '—'}\n"
                    f"Prioridade:  {chamado.get_prioridade_display()}\n"
                    f"Aberto por:  {chamado.criado_por.get_full_name() or chamado.criado_por.username}\n"
                    f"Responsável: {responsavel_nome}\n\n"
                    f"Descrição:\n{_strip_html(chamado.descricao)}\n\n"
                    f"Acesse o chamado: {link}"
                )
                ok_notif, erro_notif = disparar_email(assunto, mensagem, destinatarios)
                if not ok_notif:
                    messages.warning(request, f"Chamado salvo. E-mail de notificação não enviado — {erro_notif}")
            else:
                messages.info(request, "Chamado salvo. Nenhum destinatário encontrado — criador e responsável não têm e-mail cadastrado.")

            messages.success(request, "Chamado aberto com sucesso!")
            return redirect('dashboard')
    else:
        form = ChamadoForm()
        _aplicar_restricoes_usuario(form, request.user)
    return render(request, 'core/chamado_form.html', {'form': form, 'title': 'Abrir Chamado', 'is_responsavel': False})


@login_required(login_url='login')
def chamado_detail(request, pk):
    chamado = get_object_or_404(
        Chamado.objects.prefetch_related(
            Prefetch('observadores', queryset=User.objects.select_related('perfil'))
        ).filter(excluido=False),
        pk=pk
    )
    role = _role(request.user)
    is_observador = chamado.observadores.filter(pk=request.user.pk).exists()
    if role == 'usuario' and chamado.criado_por != request.user and not is_observador:
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')

    is_responsavel = chamado.responsavel_id == request.user.pk
    can_edit = (
        role in ('admin', 'dev')
        or chamado.criado_por == request.user
        or is_responsavel
    )

    # ── POST: salvar alterações ─────────────────────────────────────────────
    if request.method == 'POST' and can_edit:
        status_anterior_codigo = chamado.status
        status_anterior      = chamado.get_status_display()
        responsavel_anterior = chamado.responsavel

        form = ChamadoForm(request.POST, instance=chamado)
        _aplicar_restricoes_usuario(form, request.user, chamado)
        if form.is_valid():
            obj = form.save(commit=False)
            if not _status_permitido(obj.status, request.user, chamado):
                obj.status = chamado.status
            chamado = obj
            _registrar_fechamento(chamado, status_anterior=status_anterior_codigo)
            chamado.save()
            form.save_m2m()
            _salvar_anexos(request, chamado)

            novo_responsavel = chamado.responsavel
            email_atribuicao_enviado = False
            if novo_responsavel and novo_responsavel != responsavel_anterior and novo_responsavel.email:
                atribuido_por = request.user.get_full_name() or request.user.username
                ok_atr, erro_atr = disparar_email(
                    f"[Digiana] Chamado #{chamado.id} Atribuído a Você: {chamado.titulo}",
                    (
                        f"Olá, {novo_responsavel.get_full_name() or novo_responsavel.username},\n\n"
                        f"O chamado abaixo foi atribuído a você.\n\n"
                        f"Chamado:       #{chamado.id} — {chamado.titulo}\n"
                        f"Projeto:       {chamado.projeto.nome}\n"
                        f"Prioridade:    {chamado.get_prioridade_display()}\n"
                        f"Status:        {chamado.get_status_display()}\n"
                        f"Atribuído por: {atribuido_por}\n\n"
                        f"Acesse o chamado: {_build_link(request, f'/chamados/{chamado.id}/')}"
                    ),
                    [novo_responsavel.email],
                )
                if ok_atr:
                    email_atribuicao_enviado = True
                else:
                    messages.warning(request, f"Chamado salvo. E-mail de atribuição não enviado — {erro_atr}")

            destinatarios = _build_destinatarios(chamado)
            if email_atribuicao_enviado and novo_responsavel and novo_responsavel.email:
                destinatarios = [e for e in destinatarios if e != novo_responsavel.email]
            if destinatarios:
                responsavel_nome = (
                    chamado.responsavel.get_full_name() or chamado.responsavel.username
                    if chamado.responsavel else 'Não atribuído'
                )
                link = _build_link(request, f'/chamados/{chamado.id}/')
                cabecalho = (
                    f"Chamado:     #{chamado.id} — {chamado.titulo}\n"
                    f"Projeto:     {chamado.projeto.nome}\n"
                    f"Prioridade:  {chamado.get_prioridade_display()}\n"
                    f"Responsável: {responsavel_nome}\n"
                    f"Transição:   {status_anterior} → {chamado.get_status_display()}\n"
                )
                novo_status = chamado.status
                if novo_status == 'em_progresso':
                    assunto  = f"[Digiana] Chamado #{chamado.id} em Atendimento: {chamado.titulo}"
                    mensagem = f"Olá,\n\nO chamado abaixo está sendo atendido.\n\n{cabecalho}\nAcesse: {link}"
                elif novo_status == 'pendente':
                    assunto  = f"[Digiana] Ação Necessária — Chamado #{chamado.id}: {chamado.titulo}"
                    mensagem = f"Olá,\n\nO chamado abaixo está pendente e aguarda informações.\n\n{cabecalho}\nAcesse: {link}"
                elif novo_status == 'resolvido':
                    assunto  = f"[Digiana] Chamado #{chamado.id} Resolvido — Confirme: {chamado.titulo}"
                    mensagem = f"Olá,\n\nO chamado foi marcado como resolvido. Confirme ou reabra se necessário.\n\n{cabecalho}\nAcesse: {link}"
                elif novo_status == 'fechado':
                    assunto  = f"[Digiana] Chamado #{chamado.id} Encerrado: {chamado.titulo}"
                    mensagem = f"Olá,\n\nO chamado foi encerrado formalmente.\n\n{cabecalho}\nHistórico: {link}"
                else:
                    assunto  = f"[Digiana] Chamado #{chamado.id} Atualizado: {chamado.titulo}"
                    mensagem = f"Olá,\n\nO chamado abaixo foi atualizado.\n\n{cabecalho}\nAcesse: {link}"
                ok_notif, erro_notif = disparar_email(assunto, mensagem, destinatarios)
                if not ok_notif:
                    messages.warning(request, f"Chamado salvo. E-mail de notificação não enviado — {erro_notif}")
            elif not email_atribuicao_enviado:
                messages.info(request, "Chamado salvo. Nenhum destinatário encontrado — criador e responsável não têm e-mail cadastrado.")

            messages.success(request, "Chamado atualizado com sucesso!")
            return redirect('chamado_detail', pk=chamado.pk)
        # form inválido — renderiza com erros
    else:
        form = ChamadoForm(instance=chamado)
        _aplicar_restricoes_usuario(form, request.user, chamado)

    # ── Barra de tempo ──────────────────────────────────────────────────────
    encerrado = chamado.status in ('fechado', 'resolvido')
    dt_fim    = chamado.atualizado_em if encerrado else timezone.now()

    horas_u   = _horas_uteis(chamado.criado_em, dt_fim)
    minutos_u = int(horas_u * 60)
    h_int     = int(horas_u)
    min_rest  = minutos_u % 60
    dias_u    = h_int // 10
    h_resto   = h_int % 10

    progresso_pct = max(2, min(100, round(horas_u / 240 * 100)))

    if horas_u < 10:
        cor_barra = 'bg-emerald-500'
    elif horas_u < 30:
        cor_barra = 'bg-blue-500'
    elif horas_u < 70:
        cor_barra = 'bg-amber-500'
    else:
        cor_barra = 'bg-rose-500'

    if minutos_u < 60:
        tempo_decorrido = f"{minutos_u} min"
    elif h_int < 10:
        tempo_decorrido = f"{h_int}h {min_rest}min" if min_rest else f"{h_int}h"
    elif dias_u == 1:
        tempo_decorrido = "1 dia útil" + (f" e {h_resto}h" if h_resto else "")
    else:
        tempo_decorrido = f"{dias_u} dias úteis" + (f" e {h_resto}h" if h_resto else "")

    horas_extra = _horas_extra(chamado.criado_em, dt_fim)
    he_int      = int(horas_extra)
    he_min      = int((horas_extra - he_int) * 60)
    dias_extra  = he_int // 24
    he_resto    = he_int % 24
    if dias_extra >= 2:
        tempo_extra = f"{dias_extra} dias" + (f" e {he_resto}h" if he_resto else "")
    elif dias_extra == 1:
        tempo_extra = "1 dia" + (f" e {he_resto}h" if he_resto else "")
    elif he_int > 0:
        tempo_extra = f"{he_int}h" + (f" {he_min}min" if he_min else "")
    elif he_min > 0:
        tempo_extra = f"{he_min} min"
    else:
        tempo_extra = ""

    respostas = (
        chamado.respostas
        .select_related('autor', 'autor__perfil', 'resposta_pai', 'resposta_pai__autor')
        .prefetch_related('anexos')
    )
    chamado_anexos = chamado.anexos.filter(resposta__isnull=True).select_related('criado_por')

    return render(request, 'core/chamado_detail.html', {
        'chamado':         chamado,
        'form':            form,
        'can_edit':        can_edit,
        'progresso_pct':   progresso_pct,
        'cor_barra':       cor_barra,
        'tempo_decorrido': tempo_decorrido,
        'encerrado':       encerrado,
        'horas_extra':     horas_extra,
        'tempo_extra':     tempo_extra,
        'user_role':       role,
        'is_observador':   is_observador,
        'is_responsavel':  is_responsavel,
        'respostas':       respostas,
        'chamado_anexos':  chamado_anexos,
    })


@login_required(login_url='login')
def chamado_update(request, pk):
    chamado = get_object_or_404(Chamado, pk=pk, excluido=False)
    role = _role(request.user)

    is_responsavel = chamado.responsavel_id == request.user.pk
    # admin e dev podem editar qualquer chamado; gestor e usuario só se forem criador ou responsável
    if role not in ('admin', 'dev') and chamado.criado_por != request.user and not is_responsavel:
        messages.error(request, "Acesso negado.")
        return redirect('chamado_detail', pk=pk)

    status_anterior_codigo = chamado.status
    status_anterior      = chamado.get_status_display()
    responsavel_anterior = chamado.responsavel

    if request.method == 'POST':
        form = ChamadoForm(request.POST, instance=chamado)
        _aplicar_restricoes_usuario(form, request.user, chamado)
        if form.is_valid():
            obj = form.save(commit=False)
            if not _status_permitido(obj.status, request.user, chamado):
                obj.status = chamado.status
            chamado = obj
            _registrar_fechamento(chamado, status_anterior=status_anterior_codigo)
            chamado.save()
            form.save_m2m()
            _salvar_anexos(request, chamado)

            # ── Notificação de atribuição (enviada só ao novo responsável) ──
            novo_responsavel = chamado.responsavel
            email_atribuicao_enviado = False
            if (novo_responsavel
                    and novo_responsavel != responsavel_anterior
                    and novo_responsavel.email):
                atribuido_por = request.user.get_full_name() or request.user.username
                ok_atribuicao, erro_atr = disparar_email(
                    f"[Digiana] Chamado #{chamado.id} Atribuído a Você: {chamado.titulo}",
                    (
                        f"Olá, {novo_responsavel.get_full_name() or novo_responsavel.username},\n\n"
                        f"O chamado abaixo foi atribuído a você.\n\n"
                        f"Chamado:       #{chamado.id} — {chamado.titulo}\n"
                        f"Projeto:       {chamado.projeto.nome}\n"
                        f"Sistema:       {chamado.sistema or '—'}\n"
                        f"Prioridade:    {chamado.get_prioridade_display()}\n"
                        f"Status:        {chamado.get_status_display()}\n"
                        f"Atribuído por: {atribuido_por}\n\n"
                        f"Descrição:\n{_strip_html(chamado.descricao)}\n\n"
                        f"Acesse o chamado: "
                        f"{_build_link(request, f'/chamados/{chamado.id}/')}"
                    ),
                    [novo_responsavel.email],
                )
                if ok_atribuicao:
                    email_atribuicao_enviado = True
                else:
                    messages.warning(request, f"Chamado salvo. E-mail de atribuição não enviado — {erro_atr}")

            # ── Notificação de status para todos os stakeholders ──
            # Remove o novo responsável se já foi notificado pelo e-mail de atribuição
            destinatarios = _build_destinatarios(chamado)
            if email_atribuicao_enviado and novo_responsavel and novo_responsavel.email:
                destinatarios = [e for e in destinatarios if e != novo_responsavel.email]
            if destinatarios:
                responsavel_nome = (
                    chamado.responsavel.get_full_name() or chamado.responsavel.username
                    if chamado.responsavel else 'Não atribuído'
                )
                link = _build_link(request, f'/chamados/{chamado.id}/')
                cabecalho = (
                    f"Chamado:     #{chamado.id} — {chamado.titulo}\n"
                    f"Projeto:     {chamado.projeto.nome}\n"
                    f"Prioridade:  {chamado.get_prioridade_display()}\n"
                    f"Responsável: {responsavel_nome}\n"
                    f"Transição:   {status_anterior} → {chamado.get_status_display()}\n"
                )
                novo_status = chamado.status
                if novo_status == 'em_progresso':
                    assunto = f"[Digiana] Chamado #{chamado.id} em Atendimento: {chamado.titulo}"
                    mensagem = (
                        f"Olá,\n\n"
                        f"O chamado abaixo está sendo atendido.\n\n"
                        f"{cabecalho}\n"
                        f"Acesse o chamado: {link}"
                    )
                elif novo_status == 'pendente':
                    assunto = f"[Digiana] Ação Necessária — Chamado #{chamado.id}: {chamado.titulo}"
                    mensagem = (
                        f"Olá,\n\n"
                        f"O chamado abaixo está pendente e aguarda informações ou ação da sua parte.\n"
                        f"Por favor, acesse o sistema e forneça as informações solicitadas.\n\n"
                        f"{cabecalho}\n"
                        f"Acesse o chamado: {link}"
                    )
                elif novo_status == 'resolvido':
                    assunto = f"[Digiana] Chamado #{chamado.id} Resolvido — Confirme: {chamado.titulo}"
                    mensagem = (
                        f"Olá,\n\n"
                        f"O chamado abaixo foi marcado como resolvido.\n"
                        f"Por favor, confirme se o problema foi solucionado. "
                        f"Caso contrário, o chamado pode ser reaberto.\n\n"
                        f"{cabecalho}\n"
                        f"Confirme ou reabra o chamado: {link}"
                    )
                elif novo_status == 'fechado':
                    assunto = f"[Digiana] Chamado #{chamado.id} Encerrado: {chamado.titulo}"
                    mensagem = (
                        f"Olá,\n\n"
                        f"O chamado abaixo foi encerrado formalmente.\n\n"
                        f"{cabecalho}\n"
                        f"Histórico completo: {link}"
                    )
                else:
                    assunto = f"[Digiana] Chamado #{chamado.id} Atualizado: {chamado.titulo}"
                    mensagem = (
                        f"Olá,\n\n"
                        f"O chamado abaixo foi atualizado.\n\n"
                        f"{cabecalho}\n"
                        f"Acesse os detalhes: {link}"
                    )
                ok_notif, erro_notif = disparar_email(assunto, mensagem, destinatarios)
                if not ok_notif:
                    messages.warning(request, f"Chamado salvo. E-mail de notificação não enviado — {erro_notif}")
            elif not email_atribuicao_enviado:
                messages.info(request, "Chamado salvo. Nenhum destinatário encontrado — criador e responsável não têm e-mail cadastrado.")

            messages.success(request, "Chamado atualizado com sucesso!")
            return redirect('chamado_detail', pk=chamado.pk)
    else:
        form = ChamadoForm(instance=chamado)
        _aplicar_restricoes_usuario(form, request.user, chamado)
    return render(request, 'core/chamado_form.html', {
        'form': form,
        'title': 'Editar Chamado',
        'is_responsavel': is_responsavel,
    })


def _salvar_anexos(request, chamado):
    MAX = 20 * 1024 * 1024  # 20 MB
    for arquivo in request.FILES.getlist('anexos'):
        if arquivo.size > MAX:
            messages.warning(request, f"Arquivo '{arquivo.name}' ignorado: excede 20 MB.")
            continue
        Anexo.objects.create(
            chamado=chamado,
            arquivo=arquivo,
            nome_original=arquivo.name,
            tipo_mime=arquivo.content_type or '',
            criado_por=request.user,
        )


def _salvar_anexos_resposta(request, chamado, resposta):
    MAX = 20 * 1024 * 1024
    for arquivo in request.FILES.getlist('anexos'):
        if arquivo.size > MAX:
            messages.warning(request, f"Arquivo '{arquivo.name}' ignorado: excede 20 MB.")
            continue
        Anexo.objects.create(
            chamado=chamado,
            resposta=resposta,
            arquivo=arquivo,
            nome_original=arquivo.name,
            tipo_mime=arquivo.content_type or '',
            criado_por=request.user,
        )


def _aplicar_restricoes_usuario(form, user, chamado=None):
    role = _role(user)
    if role in ('usuario', 'gestor'):
        form.fields.pop('status', None)
        form.fields.pop('responsavel', None)
    if 'status' in form.fields:
        is_responsavel = chamado is not None and chamado.responsavel_id == user.pk
        if role != 'admin' and not is_responsavel:
            form.fields['status'].choices = [
                c for c in form.fields['status'].choices if c[0] != 'fechado'
            ]


def _status_permitido(status_novo, user, chamado=None):
    """Retorna False se o usuário tentar setar um status que não tem permissão."""
    role = _role(user)
    if status_novo == 'pendente' and role not in ('admin', 'dev'):
        return False
    if status_novo == 'fechado':
        if role == 'admin':
            return True
        if chamado is not None and chamado.responsavel_id == user.pk:
            return True
        return False
    return True


@login_required(login_url='login')
def chamado_responder(request, pk):
    chamado = get_object_or_404(Chamado, pk=pk, excluido=False)
    role = _role(request.user)
    is_observador = chamado.observadores.filter(pk=request.user.pk).exists()

    if role == 'usuario' and chamado.criado_por != request.user and not is_observador:
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')

    if request.method != 'POST':
        return redirect('chamado_detail', pk=pk)

    conteudo = request.POST.get('conteudo', '').strip()
    vazios = {'', '<p></p>', '<p><br></p>', '<p><br data-cke-filler="true"></p>'}
    if conteudo in vazios:
        messages.error(request, "A resposta não pode estar vazia.")
        return redirect('chamado_detail', pk=pk)

    resposta_pai = None
    pai_id = request.POST.get('resposta_pai_id', '').strip()
    if pai_id:
        try:
            resposta_pai = Resposta.objects.get(pk=int(pai_id), chamado=chamado)
        except (Resposta.DoesNotExist, ValueError):
            pass

    resposta = Resposta.objects.create(
        chamado=chamado,
        autor=request.user,
        conteudo=conteudo,
        resposta_pai=resposta_pai,
    )

    _salvar_anexos_resposta(request, chamado, resposta)

    # Regra: pendente + interação do solicitante → em_progresso
    if chamado.status == 'pendente' and chamado.criado_por == request.user:
        chamado.status = 'em_progresso'
        chamado.save()
        messages.info(request, "Status alterado para Em Progresso — interação do solicitante.")

    # Notificação e-mail aos stakeholders (exceto o autor da resposta)
    destinatarios = _build_destinatarios(chamado)
    if request.user.email:
        destinatarios = [e for e in destinatarios if e != request.user.email]
    if destinatarios:
        autor_nome = request.user.get_full_name() or request.user.username
        link = _build_link(request, f'/chamados/{chamado.pk}/')
        preview = _strip_html(conteudo)[:200]
        ok_resp, erro_resp = disparar_email(
            f"[Digiana] Nova Resposta — Chamado #{chamado.id}: {chamado.titulo}",
            (
                f"Olá,\n\n"
                f"{autor_nome} adicionou uma resposta ao chamado abaixo.\n\n"
                f"Chamado: #{chamado.id} — {chamado.titulo}\n"
                f"Projeto: {chamado.projeto.nome}\n\n"
                f"Resposta:\n{preview}\n\n"
                f"Acesse o chamado: {link}"
            ),
            destinatarios,
        )
        if not ok_resp:
            messages.warning(request, f"Resposta salva. E-mail de notificação não enviado — {erro_resp}")

    messages.success(request, "Resposta enviada com sucesso!")
    return redirect('chamado_detail', pk=pk)


@login_required(login_url='login')
def chamado_reopen(request, pk):
    chamado = get_object_or_404(Chamado, pk=pk, excluido=False)
    role = _role(request.user)

    if role == 'usuario' and chamado.criado_por != request.user:
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')

    if request.method == 'POST' and chamado.status in ('resolvido', 'fechado'):
        status_anterior = chamado.status
        chamado.status = 'aberto'
        _registrar_fechamento(chamado, status_anterior=status_anterior)
        chamado.save()

        destinatarios = _build_destinatarios(chamado)
        if destinatarios:
            reaberto_por = request.user.get_full_name() or request.user.username
            responsavel_nome = (
                chamado.responsavel.get_full_name() or chamado.responsavel.username
                if chamado.responsavel else 'Não atribuído'
            )
            ok_reab, erro_reab = disparar_email(
                f"[Digiana] Chamado #{chamado.id} Reaberto: {chamado.titulo}",
                (
                    f"Olá,\n\n"
                    f"O chamado abaixo foi reaberto e está aguardando atendimento.\n\n"
                    f"Chamado:      #{chamado.id} — {chamado.titulo}\n"
                    f"Projeto:      {chamado.projeto.nome}\n"
                    f"Prioridade:   {chamado.get_prioridade_display()}\n"
                    f"Reaberto por: {reaberto_por}\n"
                    f"Responsável:  {responsavel_nome}\n\n"
                    f"Acesse o chamado: {_build_link(request, f'/chamados/{chamado.id}/')}"
                ),
                destinatarios,
            )
            if not ok_reab:
                messages.warning(request, f"Chamado reaberto. E-mail de notificação não enviado — {erro_reab}")
        messages.success(request, "Chamado reaberto com sucesso!")

    return redirect('chamado_detail', pk=pk)


@login_required(login_url='login')
def chamado_delete(request, pk):
    chamado = get_object_or_404(Chamado, pk=pk)
    role = _role(request.user)
    is_responsavel = chamado.responsavel_id == request.user.pk
    if role != 'admin' and not is_responsavel:
        messages.error(request, "Acesso negado. Somente o responsável ou o administrador pode excluir este chamado.")
        return redirect('chamado_detail', pk=pk)
    if request.method != 'POST':
        return redirect('chamado_detail', pk=pk)
    if chamado.excluido:
        messages.info(request, "Este chamado já foi excluído.")
        return redirect('dashboard')

    motivo = request.POST.get('motivo', '').strip()
    if not motivo:
        messages.error(request, "Informe o motivo da exclusão.")
        return redirect('chamado_detail', pk=pk)

    chamado_id       = chamado.id
    titulo           = chamado.titulo
    projeto_nome     = chamado.projeto.nome
    criado_por_nome  = chamado.criado_por.get_full_name() or chamado.criado_por.username
    responsavel_nome = (
        chamado.responsavel.get_full_name() or chamado.responsavel.username
        if chamado.responsavel else 'Não atribuído'
    )
    excluido_por  = request.user.get_full_name() or request.user.username
    destinatarios = _build_destinatarios(chamado)

    chamado.excluido = True
    chamado.excluido_em = timezone.now()
    chamado.excluido_por = request.user
    chamado.motivo_exclusao = motivo
    chamado.save(update_fields=['excluido', 'excluido_em', 'excluido_por', 'motivo_exclusao', 'atualizado_em'])

    if destinatarios:
        ok_del, erro_del = disparar_email(
            f"[Digiana] Chamado #{chamado_id} Excluído: {titulo}",
            (
                f"Olá,\n\n"
                f"O chamado abaixo foi excluído do sistema Digiana.\n\n"
                f"Chamado:      #{chamado_id} — {titulo}\n"
                f"Projeto:      {projeto_nome}\n"
                f"Aberto por:   {criado_por_nome}\n"
                f"Responsável:  {responsavel_nome}\n"
                f"Excluído por: {excluido_por}\n\n"
                f"Motivo:\n{motivo}"
            ),
            destinatarios,
        )
        if not ok_del:
            messages.warning(request, f"Chamado excluído, mas e-mail de notificação não enviado — {erro_del}")

    messages.success(request, f"Chamado '{titulo}' excluído com sucesso.")
    return redirect('dashboard')


@login_required(login_url='login')
def alterar_senha_view(request):
    try:
        must_change = request.user.perfil.must_change_password
    except Exception:
        must_change = False

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            try:
                request.user.perfil.must_change_password = False
                request.user.perfil.save()
            except Exception:
                pass
            messages.success(request, "Senha alterada com sucesso!")
            return redirect('dashboard')
        else:
            messages.error(request, "Por favor, corrija os erros abaixo.")
    else:
        form = PasswordChangeForm(request.user)

    _cls = 'w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 transition'
    for field in form.fields.values():
        field.widget.attrs.update({'class': _cls})

    return render(request, 'core/alterar_senha.html', {'form': form, 'must_change': must_change})


@login_required(login_url='login')
def usuarios_list(request):
    if _role(request.user) != 'admin':
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
    qs = User.objects.select_related('perfil', 'perfil__cliente').order_by('first_name', 'username')
    paginator = Paginator(qs, 20)
    page_obj  = paginator.get_page(request.GET.get('page'))
    return render(request, 'core/usuarios_list.html', {
        'usuarios': page_obj,
        'page_obj': page_obj,
        'total':    qs.count(),
    })


@login_required(login_url='login')
def usuario_edit(request, pk):
    if _role(request.user) != 'admin':
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
    usuario = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UsuarioEditForm(request.POST, request.FILES, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f"Usuário '{usuario.username}' atualizado com sucesso!")
            return redirect('usuarios_list')
    else:
        form = UsuarioEditForm(instance=usuario)
    return render(request, 'core/usuario_edit.html', {'form': form, 'usuario': usuario})


@login_required(login_url='login')
def usuario_delete(request, pk):
    if _role(request.user) != 'admin':
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
    if request.method != 'POST':
        return redirect('usuarios_list')
    usuario = get_object_or_404(User, pk=pk)
    if usuario == request.user:
        messages.error(request, "Você não pode excluir sua própria conta.")
        return redirect('usuarios_list')
    if usuario.is_superuser:
        messages.error(request, "Não é possível excluir um superusuário.")
        return redirect('usuarios_list')
    nome = usuario.get_full_name() or usuario.username
    usuario.delete()
    messages.success(request, f"Usuário '{nome}' excluído com sucesso.")
    return redirect('usuarios_list')


@login_required(login_url='login')
def usuario_reset_senha(request, pk):
    if _role(request.user) != 'admin':
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
    if request.method != 'POST':
        return redirect('usuarios_list')
    usuario = get_object_or_404(User, pk=pk)
    if usuario == request.user:
        messages.error(request, "Use 'Alterar Senha' para redefinir sua própria senha.")
        return redirect('usuarios_list')
    if usuario.is_superuser:
        messages.error(request, "Não é possível redefinir a senha de um superusuário.")
        return redirect('usuarios_list')

    _alphabet = string.ascii_letters + string.digits + '!@#$'
    temp_password = ''.join(secrets.choice(_alphabet) for _ in range(12))
    usuario.set_password(temp_password)
    usuario.save()

    try:
        perfil = usuario.perfil
        perfil.must_change_password = True
        perfil.save()
    except PerfilUsuario.DoesNotExist:
        pass

    nome_completo = usuario.get_full_name() or usuario.username
    resetado_por  = request.user.get_full_name() or request.user.username

    ok_email, erro_email = disparar_email(
        f"[Digiana] Sua senha foi redefinida — {nome_completo}",
        (
            f"Olá, {nome_completo}!\n\n"
            f"Sua senha de acesso ao sistema Digiana foi redefinida pelo administrador {resetado_por}.\n\n"
            f"Login:            {usuario.username}\n"
            f"Senha temporária: {temp_password}\n\n"
            f"Acesse o sistema e altere sua senha no próximo login. "
            f"A troca de senha será exigida automaticamente.\n\n"
            f"Esta é uma mensagem automática — não responda a este e-mail."
        ),
        [usuario.email],
    ) if usuario.email else (False, "Usuário sem e-mail cadastrado.")

    if not ok_email:
        try:
            usuario.perfil.email_verificar = True
            usuario.perfil.save()
        except Exception:
            pass
        messages.warning(
            request,
            f"Senha de '{usuario.username}' redefinida. "
            f"E-mail não enviado — {erro_email} "
            f"Informe a nova senha manualmente ao usuário.",
        )
    else:
        messages.success(
            request,
            f"Senha de '{usuario.username}' redefinida e e-mail enviado para {usuario.email}.",
        )

    return redirect('usuarios_list')


@login_required(login_url='login')
def sistemas_list(request):
    if _role(request.user) != 'admin':
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
    qs = Sistema.objects.all().order_by('nome')
    paginator = Paginator(qs, 20)
    page_obj  = paginator.get_page(request.GET.get('page'))
    return render(request, 'core/sistemas_list.html', {
        'sistemas': page_obj,
        'page_obj': page_obj,
        'total':    qs.count(),
    })


@login_required(login_url='login')
def sistema_create(request):
    if _role(request.user) != 'admin':
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
    if request.method == 'POST':
        form = SistemaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Sistema cadastrado com sucesso!")
            return redirect('sistemas_list')
    else:
        form = SistemaForm()
    return render(request, 'core/sistema_form.html', {'form': form, 'title': 'Cadastrar Sistema'})


@login_required(login_url='login')
def sistema_update(request, pk):
    if _role(request.user) != 'admin':
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
    sistema = get_object_or_404(Sistema, pk=pk)
    if request.method == 'POST':
        form = SistemaForm(request.POST, instance=sistema)
        if form.is_valid():
            form.save()
            messages.success(request, "Sistema atualizado com sucesso!")
            return redirect('sistemas_list')
    else:
        form = SistemaForm(instance=sistema)
    return render(request, 'core/sistema_form.html', {'form': form, 'title': 'Editar Sistema'})


@login_required(login_url='login')
def perfil_foto_view(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=405)
    foto = request.FILES.get('foto')
    if not foto:
        return JsonResponse({'ok': False, 'erro': 'Nenhum arquivo enviado.'}, status=400)
    try:
        perfil = request.user.perfil
    except PerfilUsuario.DoesNotExist:
        return JsonResponse({'ok': False, 'erro': 'Perfil não encontrado.'}, status=400)
    try:
        perfil.foto = foto
        perfil.save()
        return JsonResponse({'ok': True, 'url': perfil.foto.url})
    except Exception as e:
        logger.error("Erro ao salvar foto do perfil (user=%s): %s", request.user.username, e)
        return JsonResponse({'ok': False, 'erro': 'Falha ao salvar a foto. Tente novamente.'}, status=500)


@csrf_exempt
@login_required(login_url='login')
def upload_imagem_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': {'message': 'Método não permitido.'}}, status=405)

    upload = request.FILES.get('upload')
    if not upload:
        return JsonResponse({'error': {'message': 'Nenhum arquivo recebido.'}}, status=400)

    TIPOS_PERMITIDOS = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
    if upload.content_type not in TIPOS_PERMITIDOS:
        return JsonResponse({'error': {'message': 'Tipo não permitido. Use JPEG, PNG, GIF ou WebP.'}}, status=400)

    TAMANHO_MAX = 10 * 1024 * 1024  # 10 MB
    if upload.size > TAMANHO_MAX:
        return JsonResponse({'error': {'message': 'Arquivo muito grande. Máximo: 10 MB.'}}, status=400)

    ext = os.path.splitext(upload.name)[1].lower() or '.jpg'
    agora = timezone.now()
    caminho = f'ckeditor/{agora.year}/{agora.month:02d}/{uuid.uuid4().hex}{ext}'
    caminho_salvo = default_storage.save(caminho, ContentFile(upload.read()))
    url = request.build_absolute_uri(default_storage.url(caminho_salvo))

    return JsonResponse({'url': url})


@login_required(login_url='login')
def testar_email_view(request):
    """Envia um e-mail de teste para o usuário logado e retorna JSON com diagnóstico."""
    if _role(request.user) != 'admin':
        return JsonResponse({'ok': False, 'erro': 'Acesso negado.'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'erro': 'Método não permitido.'}, status=405)

    destinatario = request.POST.get('destinatario', '').strip() or request.user.email
    if not destinatario:
        return JsonResponse({'ok': False, 'erro': 'Informe um e-mail de destino para o teste.'})

    config = ConfigurarEmail.objects.filter(ativo=True).first()
    if not config:
        return JsonResponse({'ok': False, 'erro': 'Nenhuma configuração SMTP ativa. Ative uma na lista de configurações.'})

    _senha = (config.senha or '').strip()
    diagnostico = {
        'modo': 'API HTTP (Brevo)' if config.usar_api else 'SMTP',
        'servidor': config.servidor_smtp,
        'porta': config.porta,
        'usuario': config.usuario,
        'remetente': config.remetente or config.usuario,
        'ssl': config.use_ssl,
        'tls': config.use_tls,
        'senha_configurada': bool(_senha),
        'chave_prefixo': (_senha[:12] + '...') if len(_senha) > 12 else ('(vazia)' if not _senha else _senha),
    }

    ok, erro = disparar_email(
        '[Digiana] Teste de Configuração SMTP',
        (
            f'Olá,\n\n'
            f'Este é um e-mail de teste enviado pelo sistema Digiana para confirmar que\n'
            f'a configuração SMTP está funcionando corretamente.\n\n'
            f'Servidor: {config.servidor_smtp}:{config.porta}\n'
            f'Remetente: {config.usuario}\n'
            f'SSL: {"Sim" if config.use_ssl else "Não"}  |  TLS: {"Sim" if config.use_tls else "Não"}\n\n'
            f'Se você recebeu este e-mail, o envio automático de notificações está configurado.\n\n'
            f'— Sistema Digiana'
        ),
        [destinatario],
    )
    if ok:
        return JsonResponse({'ok': True, 'destinatario': destinatario, 'diagnostico': diagnostico})
    return JsonResponse({'ok': False, 'erro': erro, 'diagnostico': diagnostico})


@login_required(login_url='login')
def configurar_email_view(request):
    if _role(request.user) != 'admin':
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
    configs = ConfigurarEmail.objects.all().order_by('-ativo', 'nome')
    return render(request, 'core/configurar_email.html', {'configs': configs})


@login_required(login_url='login')
def configurar_email_create(request):
    if _role(request.user) != 'admin':
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
    if request.method == 'POST':
        form = ConfigurarEmailForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Configuração criada com sucesso!")
            return redirect('configurar_email')
    else:
        form = ConfigurarEmailForm()
    return render(request, 'core/configurar_email_form.html', {
        'form': form,
        'title': 'Nova Configuração SMTP',
    })


@login_required(login_url='login')
def configurar_email_update(request, pk):
    if _role(request.user) != 'admin':
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
    config = get_object_or_404(ConfigurarEmail, pk=pk)
    if request.method == 'POST':
        form = ConfigurarEmailForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, f"Configuração '{config.nome}' atualizada com sucesso!")
            return redirect('configurar_email')
    else:
        form = ConfigurarEmailForm(instance=config)
    return render(request, 'core/configurar_email_form.html', {
        'form': form,
        'title': f'Editar — {config.nome}',
        'config': config,
    })


@login_required(login_url='login')
def configurar_email_ativar(request, pk):
    if _role(request.user) != 'admin':
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
    if request.method != 'POST':
        return redirect('configurar_email')
    config = get_object_or_404(ConfigurarEmail, pk=pk)
    ConfigurarEmail.objects.all().update(ativo=False)
    config.ativo = True
    config.save()
    messages.success(request, f"'{config.nome}' ativada como configuração SMTP principal.")
    return redirect('configurar_email')


@login_required(login_url='login')
def configurar_email_toggle(request, pk):
    if _role(request.user) != 'admin':
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
    if request.method != 'POST':
        return redirect('configurar_email')
    config = get_object_or_404(ConfigurarEmail, pk=pk)
    if config.ativo:
        config.ativo = False
        config.save()
        messages.info(request, f"'{config.nome}' desativada. Nenhum servidor SMTP ativo no momento.")
    else:
        ConfigurarEmail.objects.all().update(ativo=False)
        config.ativo = True
        config.save()
        messages.success(request, f"'{config.nome}' ativada como configuração SMTP principal.")
    return redirect('configurar_email')


@login_required(login_url='login')
def configurar_email_delete(request, pk):
    if _role(request.user) != 'admin':
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
    if request.method != 'POST':
        return redirect('configurar_email')
    config = get_object_or_404(ConfigurarEmail, pk=pk)
    nome = config.nome
    config.delete()
    messages.success(request, f"Configuração '{nome}' excluída.")
    return redirect('configurar_email')
