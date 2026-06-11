from django.db import models
from django.contrib.auth.models import User


class Sistema(models.Model):
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sistema"
        verbose_name_plural = "Sistemas"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Cliente(models.Model):
    nome = models.CharField(max_length=150)
    cpf_cnpj = models.CharField(max_length=18, blank=True, null=True, unique=True, verbose_name='CPF / CNPJ')
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

class Projeto(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='projetos')
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} ({self.cliente.nome})"

class Chamado(models.Model):
    STATUS_CHOICES = [
        ('aberto', 'Aberto'),
        ('em_progresso', 'Em Progresso'),
        ('pendente', 'Pendente'),
        ('resolvido', 'Resolvido'),
        ('fechado', 'Fechado'),
    ]

    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
    ]

    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='chamados')
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aberto')
    prioridade = models.CharField(max_length=20, choices=PRIORIDADE_CHOICES, default='media')
    sistema = models.ForeignKey('Sistema', on_delete=models.SET_NULL, null=True, blank=True, related_name='chamados')
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='chamados_atribuidos')
    observadores = models.ManyToManyField(User, blank=True, related_name='chamados_observados', verbose_name='Observadores')
    criado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chamados_criados')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"#{self.id} - {self.titulo} ({self.projeto.nome})"

class PerfilUsuario(models.Model):
    ROLE_CHOICES = [
        ('diretor_ti',   'Diretor de Tecnologia'),
        ('diretor',      'Diretor'),
        ('coordenador',  'Coordenador'),
        ('dev',          'Analista e Desenvolvedor de Sistemas'),
        ('analista',     'Analista de Sistema'),
        ('usr',          'Usuário'),
    ]

    # Mapeamento de cargo → nível de acesso interno
    _ADMIN_ROLES  = {'diretor_ti'}
    _GESTOR_ROLES = {'diretor', 'coordenador'}
    _DEV_ROLES    = {'dev', 'analista'}
    # usr → nível 'usuario'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='usr')
    must_change_password = models.BooleanField(default=True)
    cliente       = models.ForeignKey('Cliente', on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios', verbose_name='Cliente')
    celular         = models.CharField(max_length=20, blank=True, null=True)
    whatsapp        = models.CharField(max_length=20, blank=True, null=True)
    telefone_fixo   = models.CharField(max_length=20, blank=True, null=True)
    email_verificar = models.BooleanField(default=False, verbose_name='E-mail a verificar')
    foto            = models.ImageField(upload_to='avatares/', blank=True, null=True, verbose_name='Foto de perfil')

    class Meta:
        verbose_name = "Perfil de Usuário"
        verbose_name_plural = "Perfis de Usuários"

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @classmethod
    def role_for(cls, user):
        """Retorna 'admin', 'gestor', 'dev' ou 'usuario' com base no cargo."""
        if user.is_superuser:
            return 'admin'
        try:
            role = user.perfil.role
        except cls.DoesNotExist:
            return 'admin' if user.is_staff else 'usuario'
        if role in cls._ADMIN_ROLES:
            return 'admin'
        if role in cls._GESTOR_ROLES:
            return 'gestor'
        if role in cls._DEV_ROLES:
            return 'dev'
        return 'usuario'


class ConfigurarEmail(models.Model):
    nome = models.CharField(max_length=100, default='Principal', verbose_name='Nome')
    ativo = models.BooleanField(default=False, verbose_name='Ativo')
    servidor_smtp = models.CharField(max_length=200, default='smtp.zoho.com')
    porta = models.IntegerField(default=465)
    usuario = models.EmailField(default='dev@anagma.com.br', verbose_name='Usuário / Login SMTP')
    remetente = models.EmailField(blank=True, null=True, verbose_name='E-mail remetente', help_text='Aparece no "De:" das notificações. Se vazio, usa o Usuário.')
    senha = models.CharField(max_length=200, blank=True, null=True, help_text="Senha ou senha de aplicativo")
    use_tls = models.BooleanField(default=False, help_text="STARTTLS — porta 587")
    use_ssl = models.BooleanField(default=True, help_text="SSL direto — porta 465 (recomendado Zoho)")
    usar_api = models.BooleanField(default=False, verbose_name='Usar API HTTP', help_text='Envia via API HTTP (ignora SMTP). Use quando a porta SMTP estiver bloqueada pelo provedor.')
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuração de Email"
        verbose_name_plural = "Configurações de Email"

    def __str__(self):
        return f"Configuração SMTP ({self.usuario})"


class Resposta(models.Model):
    chamado      = models.ForeignKey(Chamado, on_delete=models.CASCADE,  related_name='respostas')
    autor        = models.ForeignKey(User,    on_delete=models.SET_NULL,  null=True, blank=True, related_name='respostas')
    conteudo     = models.TextField()
    criado_em    = models.DateTimeField(auto_now_add=True)
    resposta_pai = models.ForeignKey('self',  on_delete=models.SET_NULL,  null=True, blank=True, related_name='filhas')

    class Meta:
        ordering = ['criado_em']
        verbose_name = "Resposta"
        verbose_name_plural = "Respostas"

    def __str__(self):
        return f"Resposta #{self.pk} em chamado #{self.chamado_id}"


def _anexo_upload_path(instance, filename):
    return f'chamados/{instance.chamado_id}/anexos/{filename}'


class Anexo(models.Model):
    chamado   = models.ForeignKey(Chamado,  on_delete=models.CASCADE,  related_name='anexos')
    resposta  = models.ForeignKey(Resposta, on_delete=models.CASCADE,  null=True, blank=True, related_name='anexos')
    arquivo   = models.FileField(upload_to=_anexo_upload_path)
    nome_original = models.CharField(max_length=255)
    tipo_mime = models.CharField(max_length=100, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='anexos_criados')

    class Meta:
        verbose_name = "Anexo"
        verbose_name_plural = "Anexos"
        ordering = ['criado_em']

    def __str__(self):
        return self.nome_original
