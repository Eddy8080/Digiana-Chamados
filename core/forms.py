import re

from django import forms
from django.contrib.auth.models import User
from .models import Cliente, Projeto, Chamado, ConfigurarEmail, PerfilUsuario, Sistema

_REG = 'w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 transition'

_FONE_ATTRS = {'class': _REG, 'placeholder': '(00) 00000-0000'}
_FIXO_ATTRS = {'class': _REG, 'placeholder': '(00) 0000-0000'}


class UserRegisterForm(forms.ModelForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': _REG}))
    first_name = forms.CharField(required=True, label="Nome", widget=forms.TextInput(attrs={'class': _REG}))
    last_name = forms.CharField(required=True, label="Sobrenome", widget=forms.TextInput(attrs={'class': _REG}))
    role = forms.ChoiceField(
        choices=PerfilUsuario.ROLE_CHOICES,
        initial='usr',
        label="Perfil de acesso",
        widget=forms.Select(attrs={'class': _REG}),
    )
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all().order_by('nome'),
        required=False,
        label="Cliente",
        empty_label="— Nenhum (usuário interno) —",
        widget=forms.Select(attrs={'class': _REG}),
    )
    celular = forms.CharField(
        required=False, label="Celular",
        widget=forms.TextInput(attrs=_FONE_ATTRS),
    )
    whatsapp = forms.CharField(
        required=False, label="WhatsApp",
        widget=forms.TextInput(attrs=_FONE_ATTRS),
    )
    telefone_fixo = forms.CharField(
        required=False, label="Telefone Fixo",
        widget=forms.TextInput(attrs=_FIXO_ATTRS),
    )
    foto = forms.ImageField(
        required=False, label="Foto de perfil",
        widget=forms.FileInput(attrs={'class': 'sr-only', 'id': 'id_foto', 'accept': 'image/*'}),
    )

    field_order = [
        'username', 'email', 'first_name', 'last_name', 'role', 'cliente',
        'celular', 'whatsapp', 'telefone_fixo', 'foto',
    ]

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        skip = {'email', 'first_name', 'last_name', 'role', 'celular', 'whatsapp', 'telefone_fixo', 'foto'}
        for field in self.fields:
            if field not in skip:
                self.fields[field].widget.attrs.update({'class': _REG})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_unusable_password()
        role = self.cleaned_data.get('role', 'usr')
        if role in PerfilUsuario._ADMIN_ROLES:
            user.is_staff = True
        if commit:
            user.save()
            perfil = PerfilUsuario.objects.create(
                user=user,
                role=role,
                cliente=self.cleaned_data.get('cliente'),
                celular=self.cleaned_data.get('celular') or None,
                whatsapp=self.cleaned_data.get('whatsapp') or None,
                telefone_fixo=self.cleaned_data.get('telefone_fixo') or None,
            )
            foto = self.cleaned_data.get('foto')
            if foto:
                perfil.foto = foto
                perfil.save()
        return user


class UsuarioEditForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=PerfilUsuario.ROLE_CHOICES,
        label="Perfil de acesso",
        widget=forms.Select(attrs={'class': _REG}),
    )
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all().order_by('nome'),
        required=False,
        label="Cliente",
        empty_label="— Nenhum (usuário interno) —",
        widget=forms.Select(attrs={'class': _REG}),
    )
    celular = forms.CharField(
        required=False, label="Celular",
        widget=forms.TextInput(attrs=_FONE_ATTRS),
    )
    whatsapp = forms.CharField(
        required=False, label="WhatsApp",
        widget=forms.TextInput(attrs=_FONE_ATTRS),
    )
    telefone_fixo = forms.CharField(
        required=False, label="Telefone Fixo",
        widget=forms.TextInput(attrs=_FIXO_ATTRS),
    )
    email_verificar = forms.BooleanField(
        required=False,
        label="E-mail a verificar",
        widget=forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded border-slate-300 text-orange-500 focus:ring-orange-400'}),
    )
    foto = forms.ImageField(
        required=False, label="Foto de perfil",
        widget=forms.FileInput(attrs={'class': 'sr-only', 'id': 'id_foto', 'accept': 'image/*'}),
    )

    field_order = ['first_name', 'last_name', 'email', 'role', 'cliente', 'celular', 'whatsapp', 'telefone_fixo', 'email_verificar', 'foto']

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {'first_name': 'Nome', 'last_name': 'Sobrenome'}
        widgets = {
            'first_name': forms.TextInput(attrs={'class': _REG}),
            'last_name':  forms.TextInput(attrs={'class': _REG}),
            'email':      forms.EmailInput(attrs={'class': _REG}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            try:
                p = self.instance.perfil
                self.fields['role'].initial            = p.role
                self.fields['cliente'].initial         = p.cliente_id
                self.fields['celular'].initial         = p.celular or ''
                self.fields['whatsapp'].initial        = p.whatsapp or ''
                self.fields['telefone_fixo'].initial   = p.telefone_fixo or ''
                self.fields['email_verificar'].initial = p.email_verificar
            except PerfilUsuario.DoesNotExist:
                pass

    def save(self, commit=True):
        user = super().save(commit=False)
        role = self.cleaned_data.get('role', 'usr')
        user.is_staff = role in PerfilUsuario._ADMIN_ROLES
        if commit:
            user.save()
            try:
                perfil = user.perfil
            except PerfilUsuario.DoesNotExist:
                perfil = PerfilUsuario(user=user)
            perfil.role            = role
            perfil.cliente         = self.cleaned_data.get('cliente')
            perfil.celular         = self.cleaned_data.get('celular') or None
            perfil.whatsapp        = self.cleaned_data.get('whatsapp') or None
            perfil.telefone_fixo   = self.cleaned_data.get('telefone_fixo') or None
            perfil.email_verificar = self.cleaned_data.get('email_verificar', False)
            foto = self.cleaned_data.get('foto')
            if foto:
                perfil.foto = foto
            perfil.save()
        return user


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'cpf_cnpj', 'email', 'telefone']
        labels = {'cpf_cnpj': 'CPF / CNPJ'}
        _W = 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300'
        widgets = {
            'nome':     forms.TextInput(attrs={'class': _W}),
            'cpf_cnpj': forms.TextInput(attrs={'class': _W, 'placeholder': '000.000.000-00  ou  00.000.000/0000-00'}),
            'email':    forms.EmailInput(attrs={'class': _W}),
            'telefone': forms.TextInput(attrs={'class': _W, 'placeholder': '(00) 00000-0000'}),
        }

    def clean_cpf_cnpj(self):
        valor = self.cleaned_data.get('cpf_cnpj') or ''
        digitos = re.sub(r'\D', '', valor)
        if not digitos:
            return None
        if len(digitos) == 11:
            return f'{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}'
        if len(digitos) == 14:
            return f'{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:]}'
        raise forms.ValidationError('Informe um CPF válido (11 dígitos) ou CNPJ válido (14 dígitos).')

class ProjetoForm(forms.ModelForm):
    class Meta:
        model = Projeto
        fields = ['cliente', 'nome', 'descricao']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300'}),
            'nome': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300'}),
            'descricao': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300', 'rows': 4}),
        }

_ROLE_LABEL = {
    'diretor_ti':  'Dir. TI',
    'diretor':     'Diretor',
    'coordenador': 'Coord.',
    'dev':         'Dev',
    'analista':    'System',
    'usr':         'Usuário',
}

def _label_usuario(obj):
    nome = obj.get_full_name() or obj.username
    try:
        role_label = _ROLE_LABEL.get(obj.perfil.role, '—')
        empresa = obj.perfil.cliente.nome if obj.perfil.cliente else ''
    except Exception:
        role_label = '—'
        empresa = ''
    if empresa:
        return f"{nome} — {role_label} — {empresa}"
    return f"{nome} — {role_label}"


class ResponsavelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return _label_usuario(obj)


class ObservadorChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return _label_usuario(obj)


_W_SELECT = 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300'


class ChamadoForm(forms.ModelForm):
    sistema = forms.ModelChoiceField(
        queryset=Sistema.objects.filter(ativo=True).order_by('nome'),
        required=False,
        empty_label='— Nenhum sistema —',
        label='Sistema',
        widget=forms.Select(attrs={'class': _W_SELECT}),
    )
    responsavel = ResponsavelChoiceField(
        queryset=User.objects.filter(
            is_superuser=False,
            perfil__role__in=['dev', 'analista'],
        ).select_related('perfil__cliente').order_by('first_name', 'username'),
        required=False,
        empty_label='— Não atribuído —',
        label='Responsável',
        widget=forms.Select(attrs={'class': _W_SELECT}),
    )
    observadores = ObservadorChoiceField(
        queryset=User.objects.filter(
            is_superuser=False,
            perfil__role__in=['diretor_ti', 'diretor', 'coordenador', 'dev', 'analista', 'usr'],
        ).select_related('perfil__cliente').order_by('first_name', 'username'),
        required=False,
        label='Observadores',
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'obs-checkbox w-4 h-4 rounded border-slate-300 accent-blue-600 cursor-pointer'
        }),
    )

    class Meta:
        model = Chamado
        fields = ['projeto', 'sistema', 'titulo', 'descricao', 'status', 'prioridade', 'responsavel', 'observadores']
        widgets = {
            'projeto':   forms.Select(attrs={'class': _W_SELECT}),
            'sistema':   forms.Select(attrs={'class': _W_SELECT}),
            'titulo':    forms.TextInput(attrs={'class': _W_SELECT}),
            'descricao': forms.Textarea(attrs={'class': _W_SELECT, 'rows': 4}),
            'status':    forms.Select(attrs={'class': _W_SELECT}),
            'prioridade':forms.Select(attrs={'class': _W_SELECT}),
        }


class SistemaForm(forms.ModelForm):
    _W = 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300'

    class Meta:
        model = Sistema
        fields = ['nome', 'descricao', 'ativo']
        labels = {
            'nome': 'Nome do Sistema',
            'descricao': 'Descrição',
            'ativo': 'Ativo',
        }
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300', 'placeholder': 'Ex: ERP Fiscal, Portal do Cliente...'}),
            'descricao': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300', 'rows': 3}),
            'ativo': forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded border-slate-300 text-blue-600 focus:ring-blue-500'}),
        }

_INPUT = 'w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 transition'

class ConfigurarEmailForm(forms.ModelForm):
    senha = forms.CharField(
        required=False,
        label="Senha / Token de API",
        widget=forms.PasswordInput(attrs={'class': _INPUT, 'autocomplete': 'new-password', 'placeholder': 'Deixe em branco para manter a atual'}),
    )

    class Meta:
        model = ConfigurarEmail
        fields = ['nome', 'usar_api', 'servidor_smtp', 'porta', 'usuario', 'remetente', 'senha', 'use_ssl', 'use_tls']
        labels = {
            'nome': 'Nome da configuração',
            'usar_api': 'Usar API HTTP (Brevo)',
            'servidor_smtp': 'Servidor SMTP',
            'porta': 'Porta',
            'usuario': 'Usuário / Login SMTP',
            'remetente': 'E-mail remetente',
            'use_ssl': 'Usar SSL — porta 465',
            'use_tls': 'Usar TLS/STARTTLS — porta 587',
        }
        widgets = {
            'nome': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Ex: Zoho Mail, Brevo Produção…'}),
            'usar_api': forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded border-slate-300 text-purple-600 focus:ring-purple-500'}),
            'servidor_smtp': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'smtp.zoho.com'}),
            'porta': forms.NumberInput(attrs={'class': _INPUT, 'placeholder': '465'}),
            'usuario': forms.EmailInput(attrs={'class': _INPUT, 'placeholder': 'ae6030001@smtp-brevo.com'}),
            'remetente': forms.EmailInput(attrs={'class': _INPUT, 'placeholder': 'Ex: notificacoes@anagma.com.br (opcional)'}),
            'use_ssl': forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded border-slate-300 text-blue-600 focus:ring-blue-500'}),
            'use_tls': forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded border-slate-300 text-blue-600 focus:ring-blue-500'}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('use_ssl') and cleaned.get('use_tls'):
            raise forms.ValidationError("SSL e TLS não podem ser ativados ao mesmo tempo. Escolha apenas um.")
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        senha = self.cleaned_data.get('senha')
        if senha:
            instance.senha = senha
        if commit:
            instance.save()
        return instance
