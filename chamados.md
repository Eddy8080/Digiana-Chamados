# Digiana — Sistema de Abertura de Chamados

Documentação técnica completa do projeto: histórico de implementações, estado atual de cada arquivo e decisões de arquitetura.

---

## Visão Geral

Sistema web para registro e acompanhamento de chamados de suporte a sistemas de software desenvolvidos por uma empresa de contabilidade. Usuários de diferentes áreas (diretores, coordenadores, analistas, desenvolvedores e usuários finais) abrem chamados vinculados a projetos e clientes, que são tratados pela equipe de TI/desenvolvimento.

**Nome do sistema:** Digiana  
**Logo:** `Dig` + `IA` (com efeito glow neon ciano pulsante) + `na`

---

## Stack Tecnológica

| Camada | Tecnologia | Observação |
|---|---|---|
| Framework web | Django 3.2.25 | Projeto nomeado `setup`, app principal `core` |
| Banco de dados | SQLite (Django ORM) | Arquivo `db.sqlite3` na raiz |
| Frontend CSS | Tailwind CSS via CDN | Sem build step (sem Node/webpack) |
| Tipografia | Inter, Poppins, Montserrat | Google Fonts |
| Backend Python | Python 3.x | |
| E-mail | Zoho Mail SMTP | `smtp.zoho.com`, porta 465, SSL |

---

## Estrutura de Arquivos

```
chamados/
├── setup/
│   ├── settings.py          # Configurações Django
│   ├── urls.py              # Roteamento raiz
│   └── wsgi.py
├── core/
│   ├── models.py            # Modelos de dados
│   ├── views.py             # Views e lógica de negócio
│   ├── forms.py             # Formulários Django
│   ├── urls.py              # URLs do app core
│   ├── admin.py             # Registro no Django Admin
│   ├── middleware.py        # ForcePasswordChangeMiddleware
│   ├── context_processors.py # Injeta user_role em todos os templates
│   └── migrations/          # 13 migrações
├── templates/
│   ├── base.html            # Layout base com navbar, dark/light mode
│   └── core/
│       ├── login.html
│       ├── cadastro.html
│       ├── alterar_senha.html
│       ├── usuarios_list.html
│       ├── usuario_edit.html        # novo
│       ├── dashboard.html
│       ├── chamados_list.html       # novo
│       ├── clientes_list.html
│       ├── cliente_form.html
│       ├── projetos_list.html
│       ├── projeto_form.html
│       ├── chamado_form.html
│       ├── chamado_detail.html
│       ├── sistemas_list.html
│       ├── sistema_form.html
│       └── configurar_email.html
├── static/
├── db.sqlite3
└── manage.py
```

---

## Histórico de Implementações

### Implementação 1 — Estrutura Base e CRUD Inicial

**O que foi construído:**
- Projeto Django criado com `django-admin startproject setup`
- App `core` criado com `python manage.py startapp core`
- Modelos iniciais: `Cliente`, `Projeto`, `Chamado`
- Views básicas: login, logout, dashboard, clientes, projetos, chamados
- Template `base.html` com navbar e layout Tailwind
- Migração inicial `0001_initial.py`

**Modelos criados:**

```python
class Cliente(models.Model):
    nome = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

class Projeto(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='projetos')
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

class Chamado(models.Model):
    STATUS_CHOICES = [('aberto','Aberto'),('em_progresso','Em Progresso'),('pendente','Pendente'),('resolvido','Resolvido'),('fechado','Fechado')]
    PRIORIDADE_CHOICES = [('baixa','Baixa'),('media','Média'),('alta','Alta')]
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='chamados')
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aberto')
    prioridade = models.CharField(max_length=20, choices=PRIORIDADE_CHOICES, default='media')
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='chamados_atribuidos')
    criado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chamados_criados')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
```

**Configurações em `setup/settings.py`:**
- `LANGUAGE_CODE = 'pt-br'`
- `TIME_ZONE = 'America/Sao_Paulo'`
- `TEMPLATES.DIRS = [BASE_DIR / 'templates']`
- `STATICFILES_DIRS = [BASE_DIR / 'static']`
- `DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'`

---

### Implementação 2 — Identidade Visual Digiana e Dark Mode

**O que foi construído:**
- Logo "Digiana" com animação CSS: `Dig` + `IA` (glow neon ciano pulsante) + `na`
- Dark mode como padrão do sistema
- Light mode opcional com toggle de lâmpada na navbar
- Transição animada entre temas usando a **View Transitions API** (`document.startViewTransition`) com efeito circular ripple a partir do botão
- Fallback com `clip-path` animado para navegadores sem suporte à API

**Lógica do tema (JavaScript no `<head>` de `base.html`):**
- Tema salvo em `localStorage` com chave `digiana-theme`
- Script executa imediatamente (antes do `DOMContentLoaded`) para evitar flash de tema errado
- Toggle via `<input type="checkbox" id="theme-toggle">` + `<label>` com ícone de lâmpada SVG

**CSS do glow (em `base.html` `<style>`):**

```css
@keyframes ia-pulse {
    0%   { text-shadow: 0 0 5px rgba(0,240,255,0.2),...; color: #00f0ff; }
    50%  { text-shadow: 0 0 10px rgba(0,240,255,0.6),...; color: #7fffff; }
    100% { text-shadow: 0 0 5px rgba(0,240,255,0.2),...; color: #00f0ff; }
}
.login-logo-text .ia-glow {
    animation: ia-pulse 2.5s ease-in-out infinite;
    display: inline-block;
}
```

Variante mais suave para light mode (`ia-pulse-light`) com ciano escuro `#0090bb`.

**Dark mode como padrão:** todas as variáveis CSS de cor são sobrescritas globalmente para as classes Tailwind mais usadas (`bg-white`, `text-slate-800`, `bg-slate-50`, etc.), redirecionando para a paleta escura `#131314` / `#1e1e20`.

---

### Implementação 3 — Painel de Configuração de E-mail SMTP

**O que foi construído:**
- Modelo `ConfigurarEmail` para armazenar configuração SMTP (padrão: Zoho Mail)
- Form `ConfigurarEmailForm` com preservação de senha (campo em branco não sobrescreve)
- View `configurar_email_view` com padrão singleton (sempre edita o único registro existente)
- Template `configurar_email.html` no estilo painel de gestão (`max-w-2xl mx-auto`)
- Função `disparar_email()` em `views.py` para envio programático com a config salva
- Migrações `0002_configuraremail` e `0003_...` para os campos de SSL/TLS

**Modelo:**

```python
class ConfigurarEmail(models.Model):
    servidor_smtp = models.CharField(max_length=200, default='smtp.zoho.com')
    porta = models.IntegerField(default=465)
    usuario = models.EmailField(default='dev@anagma.com.br')
    senha = models.CharField(max_length=200, blank=True, null=True)
    use_tls = models.BooleanField(default=False)   # STARTTLS — porta 587
    use_ssl = models.BooleanField(default=True)    # SSL direto — porta 465 (Zoho)
    atualizado_em = models.DateTimeField(auto_now=True)
```

**Validação no form:** SSL e TLS não podem estar ativos ao mesmo tempo — levanta `forms.ValidationError`.

**Função de envio:**

```python
def disparar_email(assunto, mensagem, destinatarios):
    config = ConfigurarEmail.objects.first()
    if not config or not config.senha:
        return False
    connection = get_connection(
        backend='django.core.mail.backends.smtp.EmailBackend',
        host=config.servidor_smtp, port=config.porta,
        username=config.usuario, password=config.senha,
        use_tls=config.use_tls, use_ssl=config.use_ssl,
    )
    EmailMessage(assunto, mensagem, config.usuario, destinatarios, connection=connection).send()
    return True
```

E-mails são enviados automaticamente ao:
- Abrir um chamado (para responsável e e-mail do cliente)
- Atualizar um chamado (para responsável, cliente e criador)
- Reabrir um chamado (para responsável e cliente)

---

### Implementação 4 — Controle de Acesso por Papel (RBAC)

**Problema:** O sistema precisava de níveis de acesso diferenciados pois é usado por uma empresa de contabilidade onde nem todos os usuários são desenvolvedores. Coordenadores e diretores gerenciam mas não desenvolvem. Usuários são clientes internos abrindo chamados.

**Solução:** Modelo `PerfilUsuario` com 6 cargos mapeados para 4 níveis de acesso internos.

**Migrações:** `0004_perfilusuario`, `0005_...`, `0006_...`

**Modelo:**

```python
class PerfilUsuario(models.Model):
    ROLE_CHOICES = [
        ('diretor_ti',   'Diretor de Tecnologia'),
        ('diretor',      'Diretor'),
        ('coordenador',  'Coordenador'),
        ('dev',          'Analista e Desenvolvedor de Sistemas'),
        ('analista',     'Analista de Sistema'),
        ('usr',          'Usuário'),
    ]
    _ADMIN_ROLES  = {'diretor_ti'}
    _GESTOR_ROLES = {'diretor', 'coordenador'}
    _DEV_ROLES    = {'dev', 'analista'}

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='usr')
    must_change_password = models.BooleanField(default=True)

    @classmethod
    def role_for(cls, user):
        if user.is_superuser:
            return 'admin'
        try:
            role = user.perfil.role
        except cls.DoesNotExist:
            return 'admin' if user.is_staff else 'usuario'
        if role in cls._ADMIN_ROLES:  return 'admin'
        if role in cls._GESTOR_ROLES: return 'gestor'
        if role in cls._DEV_ROLES:    return 'dev'
        return 'usuario'
```

**Matriz de permissões (atualizada até Impl. 26):**

| Funcionalidade | Admin | Gestor | Dev | Usuário |
|---|:---:|:---:|:---:|:---:|
| Dashboard completo | ✅ | ✅ | ✅ | ✅ (criados + observados) |
| Ver Clientes/Projetos | ✅ | ✅ | ✅ | ❌ |
| Abrir chamado | ✅ | ✅ | ✅ | ✅ |
| Editar chamado alheio | ✅ | ✅ se criador/responsável | ✅ | ✅ se criador/responsável |
| Fechar chamado (status `fechado`) | ✅ | ❌ | ✅ **se responsável** | ❌ |
| Excluir chamado | ✅ | ❌ | ✅ **se responsável** | ❌ |
| Atribuir responsável | ✅ | ❌ | ✅ | ❌ |
| Marcar chamado como Pendente | ✅ | ❌ | ✅ | ❌ |
| Reabrir chamado | ✅ | ✅ | ✅ | ✅ **se criador** |
| Cadastrar usuário | ✅ | ❌ | ❌ | ❌ |
| Ver lista de usuários | ✅ | ❌ | ❌ | ❌ |
| Config. e-mail SMTP | ✅ | ❌ | ❌ | ❌ |
| Cadastrar Sistemas | ✅ | ❌ | ❌ | ❌ |

**Helper de restrição em formulários:**

```python
def _aplicar_restricoes_usuario(form, user):
    if _role(user) in ('usuario', 'gestor'):
        form.fields.pop('status', None)
        form.fields.pop('responsavel', None)
```

Gestor e Usuário não veem os campos `status` e `responsavel` no formulário de chamado, o que os impede de fechar ou atribuir chamados.

---

### Implementação 5 — Cadastro de Usuário com Seleção Visual de Cargo

**O que foi construído:**
- Form `UserRegisterForm` estende `UserCreationForm` com campos extras: `email`, `first_name`, `last_name`, `role`
- `field_order` controla a sequência: `username → email → first_name → last_name → role → password1 → password2`
- `save()` cria automaticamente o `PerfilUsuario` e define `is_staff=True` para cargos admin
- Template `cadastro.html` com cards radio visuais (barra horizontal) para seleção de cargo
- Descrição de cada cargo exibida nos cards para orientar o cadastrante

**Ordem dos campos (motivo):** O campo `role` (perfil de acesso) foi inserido entre `last_name` e `password1` para que o cadastrante defina o nível de acesso antes de criar a senha.

**Método `save` do form:**

```python
def save(self, commit=True):
    user = super().save(commit=False)
    role = self.cleaned_data.get('role', 'analista')
    if role in PerfilUsuario._ADMIN_ROLES:
        user.is_staff = True
    if commit:
        user.save()
        PerfilUsuario.objects.create(user=user, role=role)
    return user
```

**View protegida:** Apenas `admin` pode acessar `/cadastro/`.

---

### Implementação 6 — Troca Obrigatória de Senha no Primeiro Login

**Problema:** Novos usuários criados pelo admin recebem uma senha temporária. É necessário forçar a troca antes de qualquer outra ação.

**Solução em três partes:**

**1. Campo no modelo (`0007_perfilusuario_must_change_password.py`):**

```python
must_change_password = models.BooleanField(default=True)
```

Todo usuário novo nasce com `must_change_password=True`.

**2. Middleware (`core/middleware.py`):**

```python
class ForcePasswordChangeMiddleware:
    _EXEMPT = ('/alterar-senha/', '/logout/', '/login/', '/admin/', '/static/')

    def __call__(self, request):
        if request.user.is_authenticated:
            if not any(request.path.startswith(p) for p in self._EXEMPT):
                try:
                    if request.user.perfil.must_change_password:
                        return redirect('alterar_senha')
                except Exception:
                    pass
        return self.get_response(request)
```

Registrado no final do `MIDDLEWARE` em `settings.py`. Intercepta todas as rotas exceto as isentas.

**3. View e template (`alterar_senha_view` / `alterar_senha.html`):**

- Usa `PasswordChangeForm` nativo do Django
- Ao salvar, chama `update_session_auth_hash` (mantém o usuário logado após troca)
- Define `must_change_password = False` no perfil
- Passa `must_change` para o template
- Template exibe banner âmbar de aviso quando `must_change=True`
- Botão "Cancelar" oculto quando a troca é obrigatória

---

### Implementação 7 — Context Processor `user_role`

**Arquivo:** `core/context_processors.py`

```python
from .models import PerfilUsuario

def role_context(request):
    if request.user.is_authenticated:
        return {'user_role': PerfilUsuario.role_for(request.user)}
    return {'user_role': ''}
```

**Registro em `settings.py`:**

```python
'context_processors': [
    ...
    'core.context_processors.role_context',
],
```

**Motivo:** Permite que qualquer template use `{{ user_role }}` e `{% if user_role == 'admin' %}` sem precisar passar o dado manualmente em cada view. Usado extensivamente em `base.html`, `chamado_detail.html` e `chamado_form.html`.

---

### Implementação 8 — Lista de Usuários (Admin Only)

**O que foi construído:**
- View `usuarios_list` protegida por `_role != 'admin'`
- Template `usuarios_list.html` com tabela estilizada
- Exibe: avatar com inicial, nome completo / username, e-mail, cargo (label do choice), nível de acesso (badge colorido), status de senha, data de cadastro

**Badges de nível:**
- Azul `bg-blue-100 text-blue-700` → Admin
- Roxo `bg-purple-100 text-purple-700` → Gestor
- Verde `bg-emerald-100 text-emerald-700` → Dev
- Cinza `bg-slate-100 text-slate-600` → Usuário

**Badge de status de senha:**
- Âmbar com ícone `⚠` → "Troca pendente"
- Verde com ícone `✓` → "OK"

---

### Implementação 9 — Reabertura de Chamados

**Problema:** Chamados resolvidos ou fechados precisavam poder ser reabertos sem permitir que qualquer usuário alterasse o status livremente pelo form de edição.

**Solução:** View dedicada `chamado_reopen` separada da edição.

```python
@login_required(login_url='login')
def chamado_reopen(request, pk):
    chamado = get_object_or_404(Chamado, pk=pk)
    role = _role(request.user)
    if role == 'usuario' and chamado.criado_por != request.user:
        return redirect('dashboard')
    if request.method == 'POST' and chamado.status in ('resolvido', 'fechado'):
        chamado.status = 'aberto'
        chamado.save()
        # envia e-mail de notificação...
    return redirect('chamado_detail', pk=pk)
```

**No template `chamado_detail.html`:** Botão "Reabrir Chamado" aparece apenas quando status é `resolvido` ou `fechado`, e apenas para quem tem permissão. Implementado como `<form method="POST">` separado para garantir que seja um POST (não acessível por URL direta via GET).

---

### Implementação 10 — Modelo Sistema e Feature de Vinculação

**Motivação:** Os chamados precisavam indicar a qual sistema de software se referem. Apenas Admin pode cadastrar sistemas; todos os demais perfis podem escolher o sistema ao abrir um chamado.

**O que foi construído:**

**Modelo `Sistema` (adicionado em `core/models.py`):**

```python
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
```

**FK em `Chamado`:**

```python
sistema = models.ForeignKey('Sistema', on_delete=models.SET_NULL, null=True, blank=True, related_name='chamados')
```

`null=True, blank=True` garante que chamados existentes não sejam afetados.

**Migração:** `0008_auto_20260608_1806.py` — cria o modelo `Sistema` e adiciona o campo ao `Chamado`.

**Views novas:**
- `sistemas_list` — lista todos os sistemas (admin only)
- `sistema_create` — cadastra novo sistema (admin only)
- `sistema_update` — edita sistema existente (admin only)

**URLs adicionadas:**
```python
path('sistemas/', views.sistemas_list, name='sistemas_list'),
path('sistemas/novo/', views.sistema_create, name='sistema_create'),
path('sistemas/<int:pk>/editar/', views.sistema_update, name='sistema_update'),
```

**Form `SistemaForm`** em `core/forms.py`:
```python
class SistemaForm(forms.ModelForm):
    class Meta:
        model = Sistema
        fields = ['nome', 'descricao', 'ativo']
```

**`ChamadoForm`** atualizado para incluir `sistema` na lista de campos:
```python
fields = ['projeto', 'sistema', 'titulo', 'descricao', 'status', 'prioridade', 'responsavel']
```

**Templates:**
- `sistemas_list.html` — tabela com nome, descrição, badge ativo/inativo, data, botão Editar
- `sistema_form.html` — formulário com checkbox "Ativo" no estilo inline com label

**Atualizações em templates existentes:**
- `chamado_form.html` — link "Gerenciar Sistemas cadastrados" visível apenas para `user_role == 'admin'`, acima do formulário
- `chamado_detail.html` — seção "Sistema" adicionada ao painel lateral de metadados
- `base.html` — link "Sistemas" na navbar (admin only), com borda tracejada verde-esmeralda, posicionado antes de "Usuários"

---

### Implementação 11 — Status Pendente e Barra de Tempo em Aberto

**Motivação:** A equipe precisava de um estado intermediário para chamados que estão aguardando retorno externo (cliente, fornecedor, dependência) sem confundir com "Em Progresso". Além disso, sem SLA configurado, era necessário um indicador visual de quanto tempo o chamado está aberto para priorização informal.

#### Status `Pendente`

**Novo valor em `STATUS_CHOICES` do modelo `Chamado`:**

```python
STATUS_CHOICES = [
    ('aberto',       'Aberto'),
    ('em_progresso', 'Em Progresso'),
    ('pendente',     'Pendente'),      # novo
    ('resolvido',    'Resolvido'),
    ('fechado',      'Fechado'),
]
```

**Permissão para setar `Pendente`:**

| Perfil | Cargo | Pode setar Pendente |
|---|---|:---:|
| Admin | Diretor de Tecnologia | ✅ |
| Gestor | Diretor / Coordenador | ❌ |
| Dev | Analista e Dev de Sistemas | ✅ |
| Dev | Analista de Sistema | ✅ |
| Usuário | Usuário | ❌ |

**Proteção em duas camadas:**

1. `_aplicar_restricoes_usuario` remove o campo `status` do form para `gestor` e `usuario` — eles não enxergam nem submetem o campo.
2. `_status_permitido(status_novo, user)` — guard server-side que verifica se o status `pendente` está sendo setado por quem não tem permissão; se sim, reverte para o status anterior (no update) ou `aberto` (na criação).

```python
def _status_permitido(status_novo, user):
    if status_novo == 'pendente' and _role(user) not in ('admin', 'dev'):
        return False
    return True
```

Essa função é chamada em `chamado_create` e `chamado_update` após `form.is_valid()`, antes de `chamado.save()`.

**Badge visual:** roxo (`bg-purple-50 text-purple-700`) — diferencia visualmente de todos os outros status.

**Migração:** `0009_alter_chamado_status.py` — `AlterField` no campo `status` do `Chamado` com os cinco choices.

---

#### Barra de Tempo em Aberto

Exibida no template `chamado_detail.html`, logo abaixo do cabeçalho do chamado, acima do conteúdo principal.

**Cálculo feito em `chamado_detail` (Python, `views.py`):**

```python
from django.utils import timezone

encerrado = chamado.status in ('fechado', 'resolvido')
delta = chamado.atualizado_em - chamado.criado_em if encerrado else timezone.now() - chamado.criado_em
total_seg = max(0, int(delta.total_seconds()))
horas = total_seg // 3600

# Referência visual: 10 dias (240 h) = 100 %
progresso_pct = max(2, min(100, round(horas / 240 * 100)))
```

**Escala de cores da barra:**

| Tempo decorrido | Cor | Tailwind |
|---|---|---|
| < 24 h | Verde | `bg-emerald-500` |
| 24 h – 3 dias | Azul | `bg-blue-500` |
| 3 – 7 dias | Âmbar | `bg-amber-500` |
| > 7 dias | Vermelho | `bg-rose-500` |

**Comportamento:**
- Chamado **aberto / em progresso / pendente**: exibe tempo decorrido desde `criado_em` até agora; título "Tempo em Aberto".
- Chamado **resolvido / fechado**: exibe duração total de `criado_em` até `atualizado_em` (proxy de encerramento); título "Duração Total".
- Barra sempre exibe no mínimo 2 % de largura (visibilidade em chamados recém-abertos).

**Contexto extra passado ao template:**

| Variável | Tipo | Conteúdo |
|---|---|---|
| `progresso_pct` | int | Percentual da barra (2–100) |
| `cor_barra` | str | Classe Tailwind da cor |
| `tempo_decorrido` | str | Texto legível ("3h 20min", "2 dias e 5h", etc.) |
| `encerrado` | bool | `True` se status fechado ou resolvido |

**Dashboard:** adicionado card roxo "Pendentes" à linha de métricas. Layout alterado de 4 para 5 colunas (`md:grid-cols-5`). Badge roxo adicionado à tabela de chamados recentes para o novo status.

---

---

### Implementação 12 — Gestão Completa de Usuários (Editar e Excluir)

**Motivação:** A lista de usuários exibia apenas leitura. O admin precisava poder corrigir dados de usuários existentes (cargo, contatos, cliente vinculado) e remover usuários inativos.

**Form `UsuarioEditForm` (em `core/forms.py`):**

```python
class UsuarioEditForm(forms.ModelForm):
    email      = forms.EmailField(required=False)
    first_name = forms.CharField(required=False, label='Nome')
    last_name  = forms.CharField(required=False, label='Sobrenome')
    role       = forms.ChoiceField(choices=PerfilUsuario.ROLE_CHOICES, label='Cargo')
    telefone   = forms.CharField(required=False)
    celular    = forms.CharField(required=False)
    cliente    = forms.ModelChoiceField(queryset=Cliente.objects.all().order_by('nome'),
                     required=False, empty_label='— Nenhum (usuário interno) —')

    class Meta:
        model  = User
        fields = ['username', 'email', 'first_name', 'last_name']

    field_order = ['username','email','first_name','last_name','role','cliente','telefone','celular']
```

O método `__init__` pré-popula `role`, `telefone`, `celular` e `cliente` a partir do `PerfilUsuario` vinculado. O método `save()` persiste todos esses campos de volta ao perfil.

**Views adicionadas:**

| View | Método | Proteção |
|---|---|---|
| `usuario_edit` | GET/POST | Somente admin |
| `usuario_delete` | POST | Somente admin |

**URLs adicionadas:**
```python
path('usuarios/<int:pk>/editar/', views.usuario_edit, name='usuario_edit'),
path('usuarios/<int:pk>/excluir/', views.usuario_delete, name='usuario_delete'),
```

**Template `usuario_edit.html`:** cards radio visuais de cargo (mesmo JS de `cadastro.html`), seção de contatos com placeholder para celular/telefone, campo select para Cliente, botão "Salvar Alterações" + cancelar para `usuarios_list`.

**`usuarios_list.html` atualizado:** adicionada coluna Cliente (entre Usuário e Cargo) e coluna Ações com botões Editar/Excluir. `colspan` atualizado para 8.

---

### Implementação 13 — Revisão ITIL4 de Notificações por E-mail

**Problema:** A lógica de envio de e-mail tinha 6 falhas identificadas:
1. Helpers de limpeza de HTML e de destinatários ausentes
2. `criado_por` não recebia e-mail na abertura nem na reabertura
3. Cliente vinculado não estava incluído nos destinatários
4. E-mails com corpo sem contexto (mensagem genérica para todos os status)
5. Novo responsável não era notificado quando o chamado era atribuído a ele
6. `user_role` não passado ao contexto de `chamado_detail`

**Solução em 3 etapas autorizadas:**

#### Etapa 1 — Helpers e destinatários

**`_strip_html(texto)`** — limpa HTML do CKEditor antes de enviar no corpo do e-mail:
```python
def _strip_html(texto):
    if not texto:
        return ''
    return _unescape(strip_tags(texto)).strip()
```

**`_build_destinatarios(chamado, extras=None)`** — centraliza e deduplica destinatários:
```python
def _build_destinatarios(chamado, extras=None):
    candidatos = []
    if chamado.criado_por and chamado.criado_por.email:
        candidatos.append(chamado.criado_por.email)
    if chamado.responsavel and chamado.responsavel.email:
        candidatos.append(chamado.responsavel.email)
    if chamado.projeto.cliente and chamado.projeto.cliente.email:
        candidatos.append(chamado.projeto.cliente.email)
    if extras:
        candidatos.extend(e for e in extras if e)
    # deduplica preservando ordem
    vistos, resultado = set(), []
    for email in candidatos:
        if email not in vistos:
            vistos.add(email); resultado.append(email)
    return resultado
```

#### Etapa 2 — Mensagens contextuais por status

`chamado_update` passou a enviar assunto e corpo distintos de acordo com o status resultante:

| Status salvo | Assunto | Destinatários |
|---|---|---|
| `em_progresso` | "Chamado em Atendimento — #N" | Todos (criador + responsável + cliente) |
| `pendente` | "Ação Necessária — Chamado #N Pendente" | Todos |
| `resolvido` | "Chamado Resolvido — Confirme o Encerramento" | Todos |
| `fechado` | "Chamado Encerrado — #N" | Todos |
| outros | "Chamado Atualizado — #N" | Todos |

#### Etapa 3 — Notificação de atribuição

Quando o responsável muda, o **novo responsável** recebe e-mail de atribuição independente do e-mail de status:

```python
responsavel_anterior = chamado.responsavel   # capturado antes do form.save()
# ... form.save() ...
if chamado.responsavel and chamado.responsavel != responsavel_anterior:
    if chamado.responsavel.email:
        disparar_email(
            f'Chamado Atribuído a Você — #{chamado.id}',
            f'...',
            [chamado.responsavel.email]
        )
```

---

### Implementação 14 — CPF/CNPJ no Cadastro de Cliente

**Motivação:** Clientes precisam ser identificáveis por CPF (pessoa física) ou CNPJ (pessoa jurídica), dado essencial para emissão de documentos na empresa de contabilidade.

**Campo adicionado ao modelo `Cliente`:**

```python
cpf_cnpj = models.CharField(
    max_length=18, blank=True, null=True, unique=True,
    verbose_name='CPF / CNPJ'
)
```

**Migração:** `0012_cliente_cpf_cnpj.py` — `AddField` manual.

**Validação e formatação em `ClienteForm`:**

```python
import re

def clean_cpf_cnpj(self):
    valor = self.cleaned_data.get('cpf_cnpj') or ''
    digitos = re.sub(r'\D', '', valor)
    if not digitos:
        return None
    if len(digitos) == 11:   # CPF
        return f'{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}'
    if len(digitos) == 14:   # CNPJ
        return f'{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:]}'
    raise forms.ValidationError('Informe um CPF válido (11 dígitos) ou CNPJ válido (14 dígitos).')
```

O campo é **opcional** (blank/null). A entrada pode conter pontos, traços ou barras — `re.sub(r'\D', '')` remove tudo antes de contar os dígitos e formata na saída padronizada.

**`clientes_list.html`:** adicionada coluna CPF/CNPJ com fonte mono (`font-mono text-xs`). `colspan` atualizado para 7.

---

### Implementação 15 — Editar e Excluir Cliente

**Views adicionadas:**

| View | Método | Proteção |
|---|---|---|
| `cliente_update` | GET/POST | Admin, Gestor, Dev |
| `cliente_delete` | POST | Somente admin |

**URLs:**
```python
path('clientes/<int:pk>/editar/', views.cliente_update, name='cliente_update'),
path('clientes/<int:pk>/excluir/', views.cliente_delete, name='cliente_delete'),
```

**Comportamento de exclusão em cascata:** ao excluir um Cliente, todos os Projetos vinculados e, por consequência, todos os Chamados desses projetos são deletados. O `confirm()` no template avisa explicitamente sobre a cascata. O Django realiza o cascade automaticamente via `on_delete=models.CASCADE` nas FKs.

---

### Implementação 16 — Vinculação de Usuário a Cliente

**Motivação:** Usuários externos (clientes) precisam estar associados a um Cliente cadastrado para que as notificações de e-mail os incluam e para facilitar o filtro de chamados por cliente no futuro.

**Campo adicionado ao modelo `PerfilUsuario`:**

```python
cliente = models.ForeignKey(
    'Cliente', on_delete=models.SET_NULL,
    null=True, blank=True,
    related_name='usuarios', verbose_name='Cliente'
)
```

`SET_NULL` garante que excluir um cliente não remove o usuário, apenas desvincula.

**Migração:** `0013_perfilusuario_cliente.py` — `AddField` manual.

**Formulários atualizados (`UserRegisterForm` e `UsuarioEditForm`):**

```python
cliente = forms.ModelChoiceField(
    queryset=Cliente.objects.all().order_by('nome'),
    required=False,
    empty_label='— Nenhum (usuário interno) —'
)
```

O campo foi inserido em `field_order` após `role`. O método `save()` persiste `perfil.cliente` nos dois forms.

**`cadastro.html`:** adicionado `{% elif field.html_name == 'cliente' %}` no loop de campos para renderizar o `<select>` com estilo consistente.

---

### Implementação 17 — Editar e Excluir Projeto

**Views adicionadas:**

| View | Método | Proteção |
|---|---|---|
| `projeto_update` | GET/POST | Admin, Gestor, Dev |
| `projeto_delete` | POST | Somente admin |

**URLs:**
```python
path('projetos/<int:pk>/editar/', views.projeto_update, name='projeto_update'),
path('projetos/<int:pk>/excluir/', views.projeto_delete, name='projeto_delete'),
```

**`projetos_list.html`:** adicionada coluna Ações com botões Editar (todos os roles) e Excluir (admin only). `confirm()` avisa sobre cascata de chamados.

---

### Implementação 18 — Editar e Excluir Chamado

**Views adicionadas:**

| View | Método | Proteção |
|---|---|---|
| `chamado_delete` | POST | Somente admin |

**URL:**
```python
path('chamados/<int:pk>/excluir/', views.chamado_delete, name='chamado_delete'),
```

**Pontos de acesso ao Excluir:**
- `chamado_detail.html` — botão "Excluir" visível apenas para `user_role == 'admin'`, posicionado antes do bloco de Reabrir
- `dashboard.html` — botão Excluir na coluna de ações da tabela de chamados recentes (admin only)

---

### Implementação 19 — Lista Completa de Chamados com Filtros e Paginação

**Motivação:** O dashboard exibia apenas os 10 chamados mais recentes. Era necessária uma página dedicada que permitisse ver e filtrar todos os chamados.

**View `chamados_list` em `core/views.py`:**

```python
@login_required(login_url='login')
def chamados_list(request):
    role = _role(request.user)
    qs = (
        Chamado.objects.filter(criado_por=request.user)
        if role == 'usuario'
        else Chamado.objects.all()
    )
    status_f     = request.GET.get('status', '')
    prioridade_f = request.GET.get('prioridade', '')
    q            = request.GET.get('q', '').strip()

    if status_f:     qs = qs.filter(status=status_f)
    if prioridade_f: qs = qs.filter(prioridade=prioridade_f)
    if q:
        qs = qs.filter(
            Q(titulo__icontains=q) |
            Q(projeto__nome__icontains=q) |
            Q(projeto__cliente__nome__icontains=q)
        )

    qs = qs.select_related('projeto__cliente', 'responsavel', 'sistema').order_by('-criado_em')
    total = qs.count()
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'core/chamados_list.html', {
        'chamados': page_obj, 'page_obj': page_obj,
        'user_role': role, 'status_filter': status_f,
        'prioridade_filter': prioridade_f, 'q': q,
        'status_choices': Chamado.STATUS_CHOICES,
        'prioridade_choices': Chamado.PRIORIDADE_CHOICES,
        'total': total,
    })
```

**RBAC na listagem:** usuário com role `usuario` vê apenas os próprios chamados; demais roles veem tudo.

**Template `chamados_list.html`:**
- Barra de filtros com campo de busca (título/projeto/cliente), select de status, select de prioridade
- Botão "Limpar" aparece apenas quando há algum filtro ativo
- Tabela com colunas: ID, Título, Projeto, **Cliente** (novo), Prioridade, Status, Responsável, Data, Ações
- Ações: Detalhar (sempre), Editar (admin/gestor/dev/criador), Excluir (admin only)
- Todos os filtros persistem nos links de paginação via query string

**URL:**
```python
path('chamados/', views.chamados_list, name='chamados_list'),
```

**Paginação:** 20 registros por página com botões «/» (primeira/última), ‹/› (anterior/próxima) e numeração ±2 ao redor da página atual.

**Navbar:** link "Chamados" adicionado após "Dashboard", visível para **todos** os usuários autenticados.

**Dashboard:** link "Ver todos →" adicionado ao cabeçalho da tabela de chamados recentes.

---

### Implementação 20 — Paginação no Dashboard

**Motivação:** Com a lista de chamados paginada, o dashboard também precisava navegar além dos 10 primeiros registros.

**`dashboard` view atualizada:**

```python
paginator = Paginator(chamados, 10)
page_obj  = paginator.get_page(request.GET.get('page'))
context   = { 'chamados': page_obj, 'page_obj': page_obj, ... }
```

**`dashboard.html` atualizado:** bloco de paginação inserido no rodapé interno do card da tabela (dentro do `<div>` branco, abaixo da `<table>`), com estilo compacto: "Página X de Y" à esquerda, botões ‹/› e numerados à direita.

---

### Implementação 21 — Link Ativo na Navbar e Melhorias Visuais

**Problema:** Não havia indicação visual de qual página o usuário estava navegando.

**Solução:** `{% with url_name=request.resolver_match.url_name %}` ao redor da `<nav>` para capturar o nome da view atual sem custo de processamento extra.

Cada link da nav recebe classes condicionais:
```html
{% if url_name == 'chamados_list' or url_name == 'chamado_detail' ... %}
    bg-slate-700 text-white
{% else %}
    text-slate-300 hover:text-white hover:bg-slate-800
{% endif %}
```

**Mapeamento de sub-páginas para item ativo:**

| Item da nav | Views que o ativam |
|---|---|
| Chamados | `chamados_list`, `chamado_detail`, `chamado_create`, `chamado_update`, `chamado_reopen` |
| Clientes | `clientes_list`, `cliente_create`, `cliente_update` |
| Projetos | `projetos_list`, `projeto_create`, `projeto_update` |
| Sistemas | `sistemas_list`, `sistema_create`, `sistema_update` |
| Usuários | `usuarios_list`, `usuario_edit`, `cadastro` |
| E-mail SMTP | `configurar_email` |

**Melhorias de espaçamento na navbar:**
- `space-x-4 ml-10` → `space-x-0.5 ml-6` — itens mais compactos
- `px-3 py-2` → `px-2.5 py-1.5` — padding horizontal reduzido
- `whitespace-nowrap` em todos os links — impede quebra em telas médias
- Botão "Entrar" removido (nunca exibido — toda interação começa na tela de login)

---

### Implementação 22 — Paginação em Clientes, Projetos e Usuários + Correção de Botão Cortado

**Problema:** As três listas não tinham paginação. Em Usuários, o botão "Excluir" aparecia cortado na borda direita do card.

**Causa do corte:** O container `div.rounded-2xl` usava `overflow-hidden` (necessário para os cantos arredondados), mas a tabela com 8 colunas ultrapassava a largura disponível e o conteúdo era simplesmente clipado sem oferecer scroll.

**Solução adotada:** Em vez de adicionar `overflow-x-auto` (que introduzia barra de rolagem horizontal indesejada), as células foram compactadas para caber dentro da largura disponível:

| Template | Ajuste |
|---|---|
| `usuarios_list.html` | `px-6 py-4` → `px-4 py-3`; nome, e-mail, cliente e cargo com `max-w + truncate`; avatar `w-8` → `w-7`; `whitespace-nowrap` em status, data e ações |
| `clientes_list.html` | `px-6 py-4` → `px-4 py-3`; nome e e-mail com `truncate`; data sem horário |
| `projetos_list.html` | `px-6 py-4` → `px-4 py-3`; nome, cliente e descrição com `truncate`; cabeçalho "Chamados Abertos" → "Abertos"; data sem horário |

**Views atualizadas com `Paginator` (20/pág):**

```python
# clientes_list
qs = Cliente.objects.all().annotate(num_projetos=Count('projetos')).order_by('nome')
paginator = Paginator(qs, 20)
page_obj  = paginator.get_page(request.GET.get('page'))

# projetos_list
qs = Projeto.objects.select_related('cliente').annotate(
    num_chamados_abertos=Count('chamados', filter=Q(chamados__status='aberto'))
).order_by('cliente__nome', 'nome')

# usuarios_list
qs = User.objects.select_related('perfil', 'perfil__cliente').order_by('first_name', 'username')
```

`projetos_list` ganhou também `select_related('cliente')` (antes não tinha) e `usuarios_list` ganhou `select_related('perfil__cliente')` para evitar N+1 na coluna Cliente.

Cada template recebeu o bloco padrão de paginação no rodapé do card: "Página X de Y · N registros" + botões «/‹/números/›/».

---

### Implementação 23 — Paginação em Sistemas

**View `sistemas_list` atualizada:**

```python
qs = Sistema.objects.all().order_by('nome')
paginator = Paginator(qs, 20)
page_obj  = paginator.get_page(request.GET.get('page'))
```

**`sistemas_list.html`:** botão "Editar" padronizado para o mesmo estilo visual das outras listas (ícone SVG + texto, mesmo padrão `bg-slate-100 hover:bg-blue-50`). Bloco de paginação adicionado no rodapé do card.

---

### Implementação 24 — Redesign dos Cards de Indicadores + Atualização em Tempo Real

**Motivação:** Os cards do dashboard eram visualmente discretos e dependiam de F5 para refletir novos chamados.

**Redesign visual dos cards:**
- Gradiente colorido forte (ex.: `from-amber-500 to-orange-600`) substituindo os fundos lavados `bg-amber-50/50`
- Números em `text-5xl font-black text-white` — impacto visual imediato
- Ícone SVG Heroicons em cada card dentro de pill `bg-white/20`
- Círculos decorativos absolutos `bg-white/10` como elemento gráfico de fundo
- Sombra colorida por card (`shadow-amber-500/30` etc.) para separação visual
- Legenda descritiva abaixo do número ("aguardando", "em atendimento", etc.)

**Paleta dos cards:**

| Card | Gradiente |
|---|---|
| Total | `from-slate-700 to-slate-900` |
| Abertos | `from-amber-500 to-orange-600` |
| Em Progresso | `from-blue-500 to-blue-700` |
| Pendentes | `from-purple-500 to-violet-700` |
| Resolvidos | `from-emerald-500 to-green-700` |

**Atualização em tempo real (sem reload):**

**Endpoint JSON `dashboard_stats` em `views.py`:**
```python
@login_required(login_url='login')
def dashboard_stats(request):
    role = _role(request.user)
    qs = (
        Chamado.objects.filter(criado_por=request.user)
        if role == 'usuario'
        else Chamado.objects.all()
    )
    return JsonResponse({
        'total': qs.count(), 'abertos': ..., 'em_progresso': ...,
        'pendentes': ..., 'resolvidos': ...,
    })
```

**URL adicionada:**
```python
path('api/dashboard-stats/', views.dashboard_stats, name='dashboard_stats'),
```

**JavaScript de polling em `dashboard.html`:**
- `fetch('/api/dashboard-stats/')` a cada 15 s via `setInterval`
- Primeira chamada após 5 s (evita requisição desnecessária na carga)
- `setVal()` compara valor atual com novo antes de atualizar — anima apenas quando há mudança
- Animação `stat-pop` (`@keyframes scale 1→1.12→1` em 0.35 s) ao atualizar número
- Badge "ao vivo" com dot verde pulsante (`animate-ping`) aparece após primeira resposta
- Exibe horário da última atualização ("Atualizado às HH:MM:SS")
- Falhas de rede são silenciadas — não quebra a UI

**Relógio e data em tempo real** (Impl. 27/28 — bloco IIFE separado, sem rede):
- `#live-date` (data `dd/mm/aaaa`) + `#last-updated` (hora `HH:MM:SS`) dentro do `#live-badge`
- `live-badge` sempre visível (`inline-flex`) — não depende mais do primeiro poll
- `setInterval` de 1 s com `new Date()` — `toLocaleDateString` e `toLocaleTimeString` pt-BR
- `poll()` simplificado: não reescreve mais o horário nem manipula visibilidade do badge
- Fonte do horário: S.O. do navegador — ver Impl. 28 para estudo de migração ao horário do servidor

**RBAC preservado:** o endpoint respeita o mesmo filtro da view `dashboard` (usuário vê só os próprios chamados).

---

### Implementação 25 — Observadores de Chamado

**Motivação:** Stakeholders que precisam acompanhar um chamado mas não têm permissão para editá-lo (diretores, analistas de outros projetos, clientes internos) precisavam de visibilidade sem ganhar poder de edição.

#### Etapa 1 — Modelo e Migração

Campo adicionado ao modelo `Chamado`:

```python
observadores = models.ManyToManyField(
    User, blank=True,
    related_name='chamados_observados',
    verbose_name='Observadores'
)
```

Migração: `0014_chamado_observadores.py` — cria a tabela intermediária `core_chamado_observadores`. Campo `blank=True` garante zero impacto em chamados existentes.

#### Etapa 2 — Formulário

**`ObservadorChoiceField`** em `core/forms.py` — subclasse de `ModelMultipleChoiceField` com `label_from_instance` que exibe `"Nome Completo (username)"`:

```python
class ObservadorChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        nome = obj.get_full_name()
        return f"{nome} ({obj.username})" if nome else obj.username
```

`ChamadoForm` atualizado:
- `observadores` adicionado a `fields`
- Widget: `CheckboxSelectMultiple` com classe `obs-checkbox`
- Queryset ordenado por `first_name, username`

`chamado_form.html` — UI de acordeão recolhível para `observadores`:

**Barra de toggle** (sempre visível):
- Ícone de olho + label "Observadores" + chevron animado (roda 180° ao abrir)
- Badge numérico azul (`bg-blue-100 text-blue-700`) aparece na barra quando há observadores selecionados — visível mesmo com o painel fechado
- Hint "opcional — receberão notificações por e-mail" na borda direita

**Painel recolhível** (oculto por padrão):
- Campo de busca com filtro em tempo real (JS vanilla) — filtra por `data-name` do item
- Lista scrollável (`max-h-52`, `divide-y`) com avatar `bg-blue-500 text-white` + nome completo — contraste garantido em dark e light mode
- Item selecionado recebe `bg-blue-50 border-l-2 border-blue-500` para destaque visual
- Rodapé com contador dinâmico "N observadores selecionados"

**Comportamento inteligente:**
- Painel **fechado** ao criar chamado novo
- Painel **aberto automaticamente** ao editar chamado que já possui observadores (`preChecked > 0`)

**Correção crítica:** `form.save_m2m()` adicionado após `chamado.save()` em `chamado_create` e `chamado_update`. Sem essa chamada, o Django descarta silenciosamente todos os campos M2M quando `commit=False` é usado.

#### Etapa 3 — Visibilidade

| View | Regra anterior | Regra atual |
|---|---|---|
| `chamado_detail` | `criado_por == user` | `criado_por == user OR user in observadores` |
| `chamado_update` | `criado_por == user` | sem mudança — observador não edita |
| `chamados_list` | `filter(criado_por=user)` | `Q(criado_por=user) \| Q(observadores=user)` + `.distinct()` |
| `dashboard` | idem | idem |
| `dashboard_stats` | idem | idem |

`.distinct()` obrigatório: o JOIN do M2M duplica linhas quando um chamado tem múltiplos observadores.

`chamado_detail` passa `is_observador` (bool) ao contexto do template.

#### Etapa 4 — Notificações por E-mail

`_build_destinatarios` atualizado — bloco adicionado após o cliente:

```python
for obs in chamado.observadores.all():
    if obs.email:
        candidatos.append(obs.email)
```

A deduplicação existente garante que um observador que também é responsável ou criador não recebe e-mail duplicado. Observadores passam a receber todos os e-mails do ciclo de vida: abertura, atualização de status, atribuição de responsável e reabertura.

#### Etapa 5 — Exibição no Detail

`chamado_detail.html` — duas adições visuais + correção de dark mode:

**Badge no cabeçalho** (visível apenas para o próprio observador):
- Chip `bg-blue-50 text-blue-600 border border-blue-100` com ícone de olho SVG
- Exibido inline ao lado da linha "Projeto: …" via `{% if is_observador %}`

**Seção "Observadores" no painel lateral** (abaixo de "Criado por"):
- Lista vertical: avatar circular com inicial + nome completo truncado com `title` para tooltip
- Estado vazio: "Nenhum" em itálico

**Correção de dark mode — classes CSS explícitas:**

As classes Tailwind `bg-blue-100 text-blue-700 text-slate-700` sumiam no fundo escuro padrão do Digiana. Substituídas por classes CSS com regras duais no bloco `<style>` do template:

| Classe | Dark mode (padrão) | Light mode (`html.light-mode`) |
|---|---|---|
| `.obs-avatar` | `rgba(59,130,246,0.2)` / texto `#93c5fd` | `#dbeafe` / texto `#1d4ed8` |
| `.obs-nome` | `#cbd5e1` (slate-300) | `#334155` (slate-700) |
| `.obs-row` | `rgba(255,255,255,0.04)` | `#f8fafc` |

Resultado: avatares e nomes dos observadores são legíveis nos dois temas sem depender de overrides do Tailwind.

---

### Implementação 26 — Rótulos Enriquecidos e Permissões Avançadas por Responsável

**Motivação:** A lista de responsáveis e observadores exibia apenas o username, dificultando identificar quem é quem em empresas com muitos usuários. Simultaneamente, a regra de fechar e excluir chamados precisava ser restringida ao responsável atribuído — não deveria ser uma ação de qualquer dev ou admin, mas de quem efetivamente atendeu o chamado.

#### Etapa 1 — Rótulos `Nome — Perfil — Empresa`

**`core/forms.py` — novas construções:**

```python
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
        empresa    = obj.perfil.cliente.nome if obj.perfil.cliente else ''
    except Exception:
        role_label = '—'
        empresa    = ''
    if empresa:
        return f"{nome} — {role_label} — {empresa}"
    return f"{nome} — {role_label}"

class ResponsavelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return _label_usuario(obj)
```

`ObservadorChoiceField` atualizado para usar `_label_usuario()` (antes usava `"Nome (username)"`).

**`ChamadoForm` atualizado:**

| Campo | Antes | Depois |
|---|---|---|
| `responsavel` | Widget simples no `Meta.widgets` | Campo explícito `ResponsavelChoiceField` com queryset filtrado |
| Queryset responsável | Todos os usuários | `perfil__role__in=['dev', 'analista']`, sem superusuário, `select_related('perfil__cliente')` |
| Queryset observadores | `User.objects.all()` | Todos os roles exceto superusuário, `select_related('perfil__cliente')` |
| Label responsável | Username ou nome | `"Carlos — Dev — Odonton System"` ou `"Carlos — Dev"` se sem cliente |
| Label observador | `"Carlos (carlos)"` | `"Amanda — System — Odonton System"` ou `"Amanda — System"` se sem cliente |

`select_related('perfil__cliente')` em ambos os querysets — elimina N+1 ao renderizar a lista.

A empresa vem de `perfil.cliente.nome` — o campo `nome` do cadastro de Clientes (razão social, nome fantasia, CPF ou o que estiver registrado). Se não houver cliente vinculado, o segmento `— Empresa` é simplesmente omitido — sem valor padrão fictício.

Regra de negócio: Admin (`diretor_ti`) não aparece em nenhuma das duas listas — `is_superuser=False` no queryset, e `diretor_ti` via `_ADMIN_ROLES` define `is_staff=True` na criação. Superusuários são excluídos pelo filtro `is_superuser=False`.

---

#### Etapa 2 — Fechar e Excluir: Exclusivo do Responsável

**Regra implementada:** Somente o `chamado.responsavel` ou o `admin` podem fechar (status `fechado`) ou excluir um chamado.

**`_status_permitido(status_novo, user, chamado=None)` atualizado:**

```python
def _status_permitido(status_novo, user, chamado=None):
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
```

**`_aplicar_restricoes_usuario(form, user, chamado=None)` atualizado:**

```python
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
```

A opção `fechado` é removida das choices antes de o formulário chegar ao browser — usuário não-responsável/não-admin não vê nem consegue submeter o status.

**`chamado_delete` atualizado:**

```python
chamado   = get_object_or_404(Chamado, pk=pk)
role      = _role(request.user)
is_resp   = chamado.responsavel_id == request.user.pk
if role != 'admin' and not is_resp:
    messages.error(request, "Acesso negado. Somente o responsável ou o administrador pode excluir este chamado.")
    return redirect('chamado_detail', pk=pk)
```

Antes: somente `admin`. Agora: `admin` ou `responsavel` do chamado.

**Contexto `is_responsavel` adicionado:**
- `chamado_detail` passa `is_responsavel` (bool) ao template
- `chamado_update` e `chamado_form.html` também recebem `is_responsavel`
- `chamado_detail.html`: botão Excluir exibido para `user_role == 'admin' or is_responsavel`

---

#### Etapa 3 — Restrição de Edição para Gestor como Observador

**Regra implementada:** `gestor` (Diretor, Coordenador) passa a seguir a mesma regra de `usuario` para editar chamados — só pode editar se for `criado_por` ou `responsavel`. Antes, podia editar qualquer chamado pela role.

Justificativa: Entre os observadores, apenas `diretor_ti`, `analista` e `dev` (roles `admin` e `dev`) têm autoridade de edição irrestrita. `Diretor` e `Coordenador` como meros observadores devem ter acesso somente leitura.

**`chamado_update` — guarda de acesso:**

```python
# antes
if role == 'usuario' and chamado.criado_por != request.user and not is_responsavel:
    return redirect('dashboard')

# depois
if role not in ('admin', 'dev') and chamado.criado_por != request.user and not is_responsavel:
    return redirect('chamado_detail', pk=pk)
```

**`chamado_detail.html` — botão Editar:**

```html
<!-- antes -->
{% if user_role == 'admin' or user_role == 'gestor' or user_role == 'dev' %}
    <a ...>Editar Chamado</a>
{% elif user_role == 'usuario' and chamado.criado_por == request.user %}
    <a ...>Editar Chamado</a>
{% endif %}

<!-- depois -->
{% if user_role == 'admin' or user_role == 'dev' or chamado.criado_por == request.user or is_responsavel %}
    <a ...>Editar Chamado</a>
{% endif %}
```

**Matriz de permissões atualizada (completa após Impls. 25 e 26):**

| Ação | Admin | Dev / Analista | Diretor / Coord. | Usuário |
|---|:---:|:---:|:---:|:---:|
| Ver chamado | ✅ | ✅ | ✅ | ✅ (criador ou observador) |
| Editar chamado | ✅ | ✅ | ✅ se criador/responsável | ✅ se criador/responsável |
| Fechar chamado (status `fechado`) | ✅ | ✅ **se responsável** | ❌ | ❌ |
| Excluir chamado | ✅ | ✅ **se responsável** | ❌ | ❌ |
| Atribuir responsável | ✅ | ✅ | ❌ | ❌ |
| Marcar Pendente | ✅ | ✅ | ❌ | ❌ |
| Reabrir chamado | ✅ | ✅ | ✅ | ✅ **se criador** |

---

### Implementação 27 — Relógio e Data em Tempo Real no Dashboard

**Motivação:** O topo do dashboard não exibia data/hora em tempo real. O usuário queria ver horário e data sempre atualizados, sem recarregar a página.

**Estado final após correção (Impl. 28):**

Durante o desenvolvimento foi identificado que a implementação inicial criava dois elementos de tempo simultâneos (`#relogio` e `#last-updated`), aparecendo como dois relógios lado a lado. A correção unificou tudo em um único grupo visual.

**HTML resultante** (topo do dashboard, antes do botão "Novo Chamado"):

```html
<span id="live-badge" class="inline-flex items-center gap-2 text-sm font-medium text-slate-400">
    <span class="relative flex h-2 w-2">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
        <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
    </span>
    <span id="live-date" class="select-none"></span>
    <span class="text-slate-500/60">|</span>
    <span id="last-updated" class="font-mono tabular-nums select-none"></span>
</span>
```

- `live-badge` começa como `inline-flex` (sempre visível, não depende mais do primeiro poll)
- `live-date` — exibe `dd/mm/aaaa`
- separador `|` visual entre data e hora
- `last-updated` — exibe `HH:MM:SS` com `tabular-nums` (dígitos largura fixa, sem "pulo" visual)

**JS — IIFE do relógio** (bloco próprio, antes do bloco de polling):

```javascript
(function () {
    const elHora = document.getElementById('last-updated');
    const elData = document.getElementById('live-date');
    function tick() {
        const now = new Date();
        elHora.textContent = now.toLocaleTimeString('pt-BR', {
            hour: '2-digit', minute: '2-digit', second: '2-digit'
        });
        elData.textContent = now.toLocaleDateString('pt-BR', {
            day: '2-digit', month: '2-digit', year: 'numeric'
        });
    }
    tick();                  // preenche imediatamente na carga
    setInterval(tick, 1000); // atualiza a cada 1 segundo
})();
```

**JS — IIFE do polling** (bloco separado, a cada 15 s): removidas as linhas que atualizavam `lastUpdated` e manipulavam a visibilidade do badge — responsabilidades separadas.

**Layout resultante:**

```
Dashboard              🟢  09/06/2026  |  14:35:22   [+ Novo Chamado]
Acompanhe e gerencie...
```

**Fonte do horário:** S.O. do navegador do usuário via `new Date()` — sem requisição de rede. Ver Impl. 28 para análise completa e plano de migração para horário do servidor.

---

### Implementação 28 — Correção do Relógio Duplo + Data + Estudo de Horário do Servidor

**Correções aplicadas:**

1. Removido `<span id="relogio">` (elemento duplicado criado na Impl. 27 inicial)
2. `live-badge` passou de `hidden` para `inline-flex` — visível desde o carregamento, sem depender do primeiro poll
3. Data `dd/mm/aaaa` adicionada ao lado do horário via `#live-date`
4. `poll()` simplificado — não reescreve mais o horário nem manipula visibilidade do badge

**Estudo: horário do cliente (`new Date()`) vs horário do servidor**

| Critério | `new Date()` — S.O. do cliente | Horário do servidor |
|---|---|---|
| Requisição de rede | Nenhuma | A cada tick (1 s) ou a cada poll (15 s) |
| Precisão | Depende do relógio do S.O. do usuário | Sempre correto (servidor sincronizado via NTP) |
| Risco de erro | S.O. desatualizado ou com fuso errado exibe hora/data errada | Nenhum — independe do cliente |
| Complexidade | Mínima — puro JS | Requer campo extra no endpoint ou endpoint dedicado |
| Custo de infraestrutura | Zero | Leve (campo string no JSON já existente) |

**Quando o risco do cliente é real:**
- Dispositivos móveis antigos com sincronização NTP desativada
- Computadores corporativos com política de GPO que bloqueia sincronização automática
- Fusos horários configurados incorretamente no S.O.
- Usuários em múltiplos países acessando o mesmo sistema

**Plano de migração para horário do servidor (quando autorizado):**

*Etapa 1 — Backend:* adicionar campo `"now"` ao endpoint `dashboard_stats`:

```python
from django.utils import timezone

@login_required(login_url='login')
def dashboard_stats(request):
    # ... (lógica existente) ...
    return JsonResponse({
        'total':        qs.count(),
        'abertos':      qs.filter(status='aberto').count(),
        'em_progresso': qs.filter(status='em_progresso').count(),
        'pendentes':    qs.filter(status='pendente').count(),
        'resolvidos':   qs.filter(status='resolvido').count(),
        'now':          timezone.localtime().strftime('%d/%m/%Y|%H:%M:%S'),
    })
```

`timezone.localtime()` respeita `TIME_ZONE = 'America/Sao_Paulo'` do `settings.py` — sempre retorna o horário correto de Brasília independente do fuso do cliente.

*Etapa 2 — Frontend:* substituir o `setInterval` de 1 s por atualização a cada poll (15 s):

```javascript
// substituir o IIFE do tick por esta lógica dentro do poll():
.then(function (data) {
    // ... setVal dos cards ...
    if (data.now) {
        const partes = data.now.split('|');
        document.getElementById('live-date').textContent    = partes[0];
        document.getElementById('last-updated').textContent = partes[1];
    }
})
```

*Trade-off da migração:* o relógio passaria a atualizar a cada 15 s (intervalo do poll) em vez de a cada 1 s — os segundos deixariam de contar em tempo real. Para manter os segundos, seria necessário um endpoint dedicado de 1 s ou um `setInterval` local que apenas incrementa os segundos entre polls usando o tempo recebido como âncora.

**Decisão atual:** manter `new Date()` (client-side) pela simplicidade e ausência de custo de rede. Migrar para horário do servidor se houver relatos de divergência por parte dos usuários.

---

### Implementação 29 — Melhorias no Sistema de E-mail (Etapas 1 a 4)

#### Etapa 1 — Notificação Obrigatória ao Excluir Chamado

**Motivação:** A exclusão de um chamado era silenciosa. Nenhum stakeholder era notificado e não havia exigência de justificativa, tornando exclusões rastreáveis apenas via log de servidor.

**Regra implementada:** Exclusão exige campo `motivo` preenchido. Após `chamado.delete()`, todos os stakeholders (criador, responsável, cliente, observadores) recebem e-mail com os dados do chamado e o motivo.

**Dados coletados ANTES da exclusão** (após o delete, o objeto ORM perde os relacionamentos):

```python
chamado_id       = chamado.id
titulo           = chamado.titulo
projeto_nome     = chamado.projeto.nome
criado_por_nome  = chamado.criado_por.get_full_name() or chamado.criado_por.username
responsavel_nome = chamado.responsavel.get_full_name() ... if chamado.responsavel else 'Não atribuído'
destinatarios    = _build_destinatarios(chamado)
chamado.delete()
# só então envia o e-mail com os dados salvos acima
```

**`chamado_delete` — permissão expandida:** antes somente `admin`; agora `admin` ou `responsavel` do chamado. O botão Excluir na `chamado_detail.html` foi substituído por um toggle que revela um painel recolhível com `<textarea>` para o motivo e botões Confirmar / Cancelar. A lista `chamados_list.html` mantém um campo compacto `<input type="text" name="motivo" required>` inline no form de exclusão.

**Feedback de falha SMTP:** se o envio falhar após a exclusão, exibe `messages.warning`.

---

#### Etapa 2 — Correção do E-mail Duplicado ao Atribuir Responsável

**Problema:** Ao salvar um chamado com novo responsável, ele recebia dois e-mails: o e-mail personalizado "Atribuído a Você" e o e-mail geral de atualização de status — que incluía o mesmo endereço via `_build_destinatarios`.

**Solução — flag `email_atribuicao_enviado`:**

```python
email_atribuicao_enviado = False
if novo_responsavel and novo_responsavel != responsavel_anterior and novo_responsavel.email:
    ok = disparar_email(...)    # e-mail personalizado
    if ok:
        email_atribuicao_enviado = True
    else:
        messages.warning(request, "... e-mail de atribuição não enviado ...")

destinatarios = _build_destinatarios(chamado)
if email_atribuicao_enviado and novo_responsavel and novo_responsavel.email:
    destinatarios = [e for e in destinatarios if e != novo_responsavel.email]
# agora o e-mail geral não inclui o responsável que já recebeu o e-mail individual
```

---

#### Etapa 3 — Feedback Visual de Falha no Envio de E-mail

**Problema:** Todas as chamadas a `disparar_email()` descartavam o retorno silenciosamente. Se o SMTP estivesse mal configurado, o chamado era salvo mas o usuário não sabia que nenhuma notificação foi enviada.

**Solução:** Verificação do valor de retorno em todos os pontos de disparo:

| View | Momento | Mensagem exibida em caso de falha |
|---|---|---|
| `chamado_create` | Após criar | `messages.warning`: chamado salvo, e-mail não enviado |
| `chamado_update` — atribuição | Ao atribuir responsável | `messages.warning`: chamado salvo, e-mail de atribuição não enviado |
| `chamado_update` — status | Após salvar | `messages.warning`: chamado salvo, e-mail de notificação não enviado |
| `chamado_reopen` | Após reabrir | `messages.warning`: chamado reaberto, e-mail não enviado |
| `chamado_delete` | Após excluir | `messages.warning`: chamado excluído, e-mail não enviado |

---

#### Etapa 4 — Flag `email_verificar` + E-mail de Boas-Vindas com Senha Temporária

**Motivação:** Ao cadastrar um usuário, o administrador precisava fornecer uma senha manualmente. Não havia verificação de que o e-mail informado era válido. Usuários com e-mail errado ficavam sem credenciais acessíveis.

**Novo campo no modelo `PerfilUsuario`:**

```python
email_verificar = models.BooleanField(default=False, verbose_name='E-mail a verificar')
```

**Migração:** `0015_perfilusuario_email_verificar.py` — `AddField`.

**`UserRegisterForm` — remoção dos campos de senha:**

- Herança alterada de `UserCreationForm` para `forms.ModelForm`
- `password1` e `password2` removidos de `field_order` e do formulário
- `import UserCreationForm` removido de `forms.py`
- `save()` chama `user.set_unusable_password()` antes de `user.save()` — a senha real é definida na view

**`UsuarioEditForm` — novo campo `email_verificar`:**

```python
email_verificar = forms.BooleanField(
    required=False, label="E-mail a verificar",
    widget=forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded border-slate-300 text-orange-500 ...'}),
)
```

Adicionado a `field_order`, `__init__` (leitura do perfil) e `save()` (gravação no perfil).

**`cadastro_view` — geração de senha temporária e boas-vindas:**

```python
import secrets, string

_alphabet = string.ascii_letters + string.digits + '!@#$'
temp_password = ''.join(secrets.choice(_alphabet) for _ in range(12))
user.set_password(temp_password)
user.save()

ok_email = disparar_email(
    f"[Digiana] Bem-vindo, {nome_completo}! Seu acesso foi criado.",
    f"Login: {user.username}\nSenha temporária: {temp_password}\n...",
    [user.email],
) if user.email else False

if not ok_email:
    user.perfil.email_verificar = True
    user.perfil.save()
    messages.warning(request, "Usuário cadastrado. E-mail não enviado — marcado como 'E-mail a verificar'.")
else:
    messages.success(request, "Usuário cadastrado e e-mail de boas-vindas enviado!")

return redirect('usuarios_list')   # antes redirecionava para dashboard
```

O fluxo de `must_change_password = True` (default do modelo) já garante que no primeiro login o usuário é obrigado a trocar a senha temporária.

**`usuarios_list.html` — badge laranja "E-mail a verificar":**

A coluna Status agora pode exibir dois badges empilhados: o badge de senha ("Troca pendente" âmbar ou "OK" verde) e, se `email_verificar = True`, um badge laranja "E-mail a verificar" abaixo dele.

**`usuario_edit.html` — branch dedicado para `email_verificar`:**

```html
{% elif field.html_name == 'email_verificar' %}
<div class="pt-2 border-t border-slate-100">
    <label class="inline-flex items-center gap-3 cursor-pointer select-none">
        {{ field }}
        <span class="text-sm font-semibold text-slate-700">{{ field.label }}</span>
    </label>
    <p class="text-xs text-slate-400 mt-1 ml-8">Marque se o e-mail informado não foi confirmado...</p>
</div>
```

**`cadastro.html` — nota informativa:**

Caixa azul antes dos botões de submit:

> "Uma **senha temporária aleatória** será gerada e enviada por e-mail ao usuário. No primeiro acesso, o sistema exigirá a troca de senha."

---

### Implementação 30 — Correção do Botão "Salvar Chamado" (novalidate)

**Problema:** O botão "Salvar Chamado" em `chamado_form.html` não fazia nada ao ser clicado.

**Causa raiz:** O CKEditor substitui o `<textarea id="id_descricao">` pelo seu editor rico e o oculta com `display: none`. O navegador executa a validação HTML5 *antes* do evento `submit`. Como o textarea está oculto e vazio (`required`), o browser detecta falha de validação, tenta exibir o tooltip de erro em um elemento invisível, falha silenciosamente e bloqueia o envio. O handler `submit` que sincroniza o conteúdo do CKEditor para o textarea nunca chega a rodar — círculo vicioso.

**Solução:** Adicionado atributo `novalidate` ao `<form>` de `chamado_form.html`. O Django já realiza toda a validação no servidor; a validação HTML5 nativa é redundante e incompatível com editores ricos que escondem o campo original.

```html
<!-- antes -->
<form method="POST" enctype="multipart/form-data" class="space-y-5" id="chamado-form">

<!-- depois -->
<form method="POST" enctype="multipart/form-data" novalidate class="space-y-5" id="chamado-form">
```

**Arquivo alterado:** `templates/core/chamado_form.html` — linha do `<form>`.

---

### Implementação 31 — Tela Unificada: Detalhe + Edição em Uma Única Página

**Motivação:** Existiam dois botões separados na listagem — "Detalhar" e "Editar" — levando a duas telas distintas. O atendente precisava abrir o detalhe para ler o chamado e depois navegar para outra tela para editar. A tela de detalhe já tinha todas as informações necessárias; a separação criava fricção sem benefício.

**Decisão de design:** `chamado_detail` passa a ser a tela de trabalho única. Usuários com permissão de edição enxergam campos editáveis inline; usuários sem permissão (observadores puros, usuários fora do chamado) enxergam apenas a visualização read-only — sem alteração de acesso.

#### O que mudou em `core/views.py` — `chamado_detail`

A view passou a aceitar `POST` além de `GET`. O bloco POST incorpora toda a lógica que estava em `chamado_update`:

```python
can_edit = (
    role in ('admin', 'dev')
    or chamado.criado_por == request.user
    or is_responsavel
)

if request.method == 'POST' and can_edit:
    status_anterior      = chamado.get_status_display()
    responsavel_anterior = chamado.responsavel
    form = ChamadoForm(request.POST, instance=chamado)
    _aplicar_restricoes_usuario(form, request.user, chamado)
    if form.is_valid():
        obj = form.save(commit=False)
        if not _status_permitido(obj.status, request.user, chamado):
            obj.status = chamado.status
        chamado = obj
        chamado.save()
        form.save_m2m()
        _salvar_anexos(request, chamado)
        # ... notificações de atribuição e status (lógica idêntica ao chamado_update) ...
        messages.success(request, "Chamado atualizado com sucesso!")
        return redirect('chamado_detail', pk=chamado.pk)
else:
    form = ChamadoForm(instance=chamado)
    _aplicar_restricoes_usuario(form, request.user, chamado)
```

Novo contexto adicionado: `form` (instância do `ChamadoForm`) e `can_edit` (bool).

Todas as regras RBAC são preservadas integralmente — `_aplicar_restricoes_usuario` e `_status_permitido` continuam como guards duplos (UI + server-side).

#### O que mudou em `chamado_detail.html`

O template foi reescrito para comportar dois modos via `{% if can_edit %}`:

| Elemento | Modo read-only (`can_edit=False`) | Modo edição (`can_edit=True`) |
|---|---|---|
| Título | `<h1>` estático | `<input type="text" name="titulo">` inline, sem borda até hover |
| Descrição | `<div class="chamado-descricao">{{ descricao\|safe }}</div>` | `<textarea id="id_descricao">` + CKEditor completo |
| Status | Badge colorido estático | `<select name="status">` com choices filtradas pelo RBAC |
| Prioridade | Badge colorido estático | `<select name="prioridade">` |
| Responsável | Texto estático | Widget `ResponsavelChoiceField` (rótulo `Nome — Perfil — Empresa`) |
| Observadores | Lista de avatares com nomes | Acordeão com busca e contador (mesmo padrão do `chamado_form.html`) |
| Anexos novos | — | Input `type="file" multiple` abaixo da descrição |
| Botão principal | — | "Salvar Alterações" no cabeçalho |
| CKEditor | Não carregado | CSS + JS do CDN carregados via `{% block extra_head %}` |

**Campos obrigatórios que não aparecem visualmente** (`projeto`, `sistema`) são enviados como `<input type="hidden">` para que o `ChamadoForm` valide sem erro:

```html
<input type="hidden" name="projeto" value="{{ chamado.projeto.pk }}">
<input type="hidden" name="sistema" value="{{ chamado.sistema.pk|default:'' }}">
```

O `<form>` envolve toda a página com `novalidate` (mesma razão da Impl. 30 — CKEditor oculta o textarea).

**Botão "Editar Chamado"** foi removido do cabeçalho — não existe mais como ação separada.

#### O que mudou nas listas

- `chamados_list.html` — bloco `{% if ... %}<a href="chamado_update">Editar</a>{% endif %}` removido
- `dashboard.html` — idem

A URL `/chamados/<pk>/editar/` e a view `chamado_update` continuam existindo no código (não foram removidas) mas nenhum template aponta mais para elas. Podem ser removidas em iteração futura.

**Por que manter `chamado_update`?** Remoção imediata exigiria também apagar a entrada em `urls.py` e garantir que nenhum bookmark ou link externo aponte para a rota. Manter a rota viva sem links é inofensivo e seguro — a view ainda aplica todas as proteções RBAC se acessada diretamente.

---

### Implementação 32 — Correção "Salvar Alterações" (forms aninhados)

**Problema:** O botão "Salvar Alterações" na tela `chamado_detail` não fazia nada ao ser clicado. Nenhuma mensagem de erro, nenhum redirecionamento — a página simplesmente recarregava sem salvar.

**Causa raiz:** O `<form id="detail-form">` envolvia toda a página. Dentro dele estavam o form de reabrir (`<form method="POST" action=".../reabrir/">`) e o form de exclusão (`<form method="POST" action=".../excluir/">`). O HTML5 proíbe forms aninhados: ao encontrar o primeiro `<form>` filho, o parser do browser **fecha implicitamente** o `<form>` pai. Na prática, o `detail-form` era encerrado logo na abertura do primeiro form auxiliar. Todos os campos que vinham depois — `descricao`, `status`, `prioridade`, `responsavel`, `observadores` — ficavam **fora** do form efetivo no DOM. O Django recebia um POST incompleto, `form.is_valid()` falhava (campos obrigatórios ausentes), e a view recarregava sem salvar e sem exibir erro (o caminho de falha silencioso de `is_valid()`).

**Solução — três mudanças estruturais em `chamado_detail.html`:**

1. **Forms auxiliares movidos para fora do `detail-form`** — o form de reabrir e o form de exclusão foram posicionados como elementos irmãos, *antes* da abertura do `<form id="detail-form">`. Nenhum form fica mais aninhado dentro de outro.

2. **Atributo `form="detail-form"` nos campos do cabeçalho** — o campo `titulo` (input inline no header) e o botão "Salvar Alterações" estão no cabeçalho, fora da posição DOM do `<form id="detail-form">`. O atributo HTML5 `form="<id>"` associa qualquer input ou button a um form pelo id, independentemente de onde estejam no DOM:

```html
<!-- título no header, fora da tag <form>, associado via form= -->
<input type="text" name="titulo" form="detail-form" ...>

<!-- botão salvar no header -->
<button type="submit" form="detail-form" ...>Salvar Alterações</button>
```

3. **`form.fields.status` em vez de `form.status` no template** — a condição `{% if can_edit and form.status %}` foi corrigida para `{% if can_edit and form.fields.status %}`. O accessor `form.status` retorna um `BoundField` que nunca é falsy mesmo quando o campo foi removido de `form.fields` pelo `_aplicar_restricoes_usuario`. A lookup explícita em `form.fields` (dicionário) retorna `KeyError`/`None` corretamente quando o campo foi removido.

**Por que não houve mensagem de erro?** O fluxo `POST` na view caia em `form.is_valid() == False` e entrava no branch `else: form = ChamadoForm(instance=chamado)` — reconstruindo o form a partir da instância, re-renderizando a página. Visualmente idêntico a um GET normal. Sem `messages.error`, o usuário não recebia nenhum feedback.

---

### Implementação 33 — Sistema de Respostas Encadeadas

**Motivação:** A tela de detalhe exibia apenas a descrição original do chamado. Não havia mecanismo para atendente e solicitante trocarem mensagens dentro do contexto do chamado — a comunicação acontecia fora do sistema. A feature implementa uma "conversa" encadeada diretamente no detalhe, com histórico cronológico, citação de resposta pai e transição automática de status.

#### Modelo `Resposta` (`core/models.py`)

Novo modelo adicionado antes de `_anexo_upload_path`:

```python
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
```

Campo `resposta` adicionado ao modelo `Anexo` (nullable FK):

```python
resposta = models.ForeignKey(Resposta, on_delete=models.CASCADE, null=True, blank=True, related_name='anexos')
```

- Anexos de chamado (sem resposta associada): `resposta=None`
- Anexos de uma resposta específica: `resposta=<Resposta>`
- O filtro `chamado.anexos.filter(resposta__isnull=True)` isola os anexos do chamado; `resposta.anexos.all()` isola os de uma resposta.

#### Migração `0016_auto_20260610_0954.py`

Gerada com `python manage.py makemigrations` e aplicada com `python manage.py migrate`. Operações:
- `CreateModel` — cria tabela `core_resposta`
- `AddField` — adiciona coluna `resposta_id` (nullable) em `core_anexo`

#### URL `chamado_responder` (`core/urls.py`)

```python
path('chamados/<int:pk>/responder/', views.chamado_responder, name='chamado_responder'),
```

Adicionada antes de `chamado_reopen`.

#### Helper `_salvar_anexos_resposta` (`core/views.py`)

Adicionado após `_salvar_anexos`. Persiste arquivos do `request.FILES['anexos']` ligados a uma instância de `Resposta`:

```python
def _salvar_anexos_resposta(request, chamado, resposta):
    MAX = 20 * 1024 * 1024
    for arquivo in request.FILES.getlist('anexos'):
        if arquivo.size > MAX:
            messages.warning(request, f"Arquivo '{arquivo.name}' ignorado: excede 20 MB.")
            continue
        Anexo.objects.create(
            chamado=chamado, resposta=resposta,
            arquivo=arquivo, nome_original=arquivo.name,
            tipo_mime=arquivo.content_type or '', criado_por=request.user,
        )
```

#### View `chamado_responder` (`core/views.py`)

```python
@login_required(login_url='login')
def chamado_responder(request, pk):
    chamado = get_object_or_404(Chamado, pk=pk)
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
    # Resolve resposta pai (para citação)
    resposta_pai = None
    pai_id = request.POST.get('resposta_pai_id', '').strip()
    if pai_id:
        try:
            resposta_pai = Resposta.objects.get(pk=int(pai_id), chamado=chamado)
        except (Resposta.DoesNotExist, ValueError):
            pass
    resposta = Resposta.objects.create(
        chamado=chamado, autor=request.user,
        conteudo=conteudo, resposta_pai=resposta_pai,
    )
    _salvar_anexos_resposta(request, chamado, resposta)
    # Auto-transição: pendente + criado_por responde → em_progresso
    if chamado.status == 'pendente' and chamado.criado_por == request.user:
        chamado.status = 'em_progresso'
        chamado.save()
        messages.info(request, "Status alterado para Em Progresso — interação do solicitante.")
    # E-mail de notificação (excluindo o próprio autor da resposta)
    destinatarios = _build_destinatarios(chamado)
    if request.user.email:
        destinatarios = [e for e in destinatarios if e != request.user.email]
    if destinatarios:
        autor_nome = request.user.get_full_name() or request.user.username
        link = request.build_absolute_uri(f'/chamados/{chamado.pk}/')
        preview = _strip_html(conteudo)[:200]
        if not disparar_email(
            f"[Digiana] Nova Resposta — Chamado #{chamado.id}: {chamado.titulo}",
            f"Olá,\n\n{autor_nome} adicionou uma resposta ao chamado abaixo.\n\nChamado: #{chamado.id} — {chamado.titulo}\nProjeto: {chamado.projeto.nome}\n\nResposta:\n{preview}\n\nAcesse o chamado: {link}",
            destinatarios,
        ):
            messages.warning(request, "Resposta salva. E-mail de notificação não pôde ser enviado.")
    messages.success(request, "Resposta enviada com sucesso!")
    return redirect('chamado_detail', pk=pk)
```

#### Contexto adicionado em `chamado_detail` (`core/views.py`)

```python
respostas = (
    chamado.respostas
    .select_related('autor', 'autor__perfil', 'resposta_pai', 'resposta_pai__autor')
    .prefetch_related('anexos')
)
chamado_anexos = chamado.anexos.filter(resposta__isnull=True).select_related('criado_por')

return render(request, 'core/chamado_detail.html', {
    ...demais chaves...,
    'respostas':      respostas,
    'chamado_anexos': chamado_anexos,
})
```

#### Seção "Conversa" em `chamado_detail.html`

Adicionada após o card de anexos existentes. Estrutura:

```
┌─ Conversa ─────────────────────────────────────────────────────┐
│  [Bolha — mensagem original do chamado]  [Botão "Responder"]   │
│                                                                  │
│  [Bolha resposta 1] (autor externo)      [Botão "Responder"]   │
│  [Bolha resposta 2] (autor próprio)                            │
│    └ banner de citação: "Em resposta a Fulano: …"              │
│  ...                                                            │
│                                                                  │
│  ┌─ Área de resposta (hidden por padrão) ─────────────────────┐ │
│  │  Banner "Em resposta a <autor>" (se citação ativa)         │ │
│  │  [CKEditor lazy]                                           │ │
│  │  [Input file]  [Botão Enviar]  [Botão Cancelar]            │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**CKEditor lazy init:** o editor da conversa não é instanciado no carregamento da página. A instância é criada na primeira vez que o usuário clica em qualquer botão "Responder" — após a criação a instância é reutilizada:

```javascript
var _replyEditor = null;
var _editorReady = false;

function initEditor() {
    if (_editorReady) return Promise.resolve(_replyEditor);
    return ClassicEditor.create(replyTA, { /* toolbar config */ }).then(function(editor) {
        _replyEditor = editor;
        _editorReady = true;
        replyForm.addEventListener('submit', function() { replyTA.value = editor.getData(); });
        return editor;
    });
}

function openReplyForm(paiId, paiAutor, paiPreview) {
    formArea.classList.remove('hidden');
    paiInput.value = (paiId && paiId !== '0') ? paiId : '';
    // exibe/oculta banner de citação
    initEditor().then(function(editor) {
        if (editor) editor.focus();
        formArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });
}
```

**Upload de imagens no CKEditor de resposta** reutiliza o endpoint `/upload/imagem/` já existente (csrf_exempt, mesmo handler do form de criação).

---

## Implementação 34 — Foto de Perfil (Upload pelo Admin)

**Objetivo:** permitir que o admin cadastre ou edite um usuário já com uma foto de perfil. A foto substitui o círculo com inicial em todos os pontos do sistema onde o avatar é exibido.

### Dependência

`Pillow==12.2.0` adicionado a `requirements.txt` (obrigatório para `ImageField`). Instalado no virtualenv do projeto via `venv/Scripts/pip.exe install Pillow`.

### Modelo

Campo `foto` adicionado a `PerfilUsuario` em `core/models.py`:

```python
foto = models.ImageField(
    upload_to='avatares/', blank=True, null=True,
    verbose_name='Foto de perfil'
)
```

Arquivos são gravados em `MEDIA_ROOT/avatares/` (configurado via `MEDIA_ROOT = BASE_DIR / 'media'` e `MEDIA_URL = '/media/'` em `settings.py`).

### Migração

`core/migrations/0017_perfilusuario_foto.py` — gerada automaticamente por `makemigrations`; adiciona a coluna `foto` à tabela `core_perfilusuario`.

### Forms

`UserRegisterForm` e `UsuarioEditForm` em `core/forms.py` receberam:

```python
foto = forms.ImageField(
    required=False, label="Foto de perfil",
    widget=forms.FileInput(attrs={'class': 'sr-only', 'id': 'id_foto', 'accept': 'image/*'}),
)
```

`'foto'` foi incluído em `field_order` de ambos os forms.

`UserRegisterForm.save()`:
```python
foto = self.cleaned_data.get('foto')
if foto:
    perfil.foto = foto
    perfil.save()
```

`UsuarioEditForm.save()`:
```python
foto = self.cleaned_data.get('foto')
if foto:
    perfil.foto = foto
perfil.save()
```

### Views

`cadastro_view` e `usuario_edit` em `core/views.py` passam `request.FILES` ao instanciar o form:

```python
form = UserRegisterForm(request.POST, request.FILES)   # cadastro_view
form = UsuarioEditForm(request.POST, request.FILES, instance=usuario)  # usuario_edit
```

### Templates

**`cadastro.html`** — `enctype="multipart/form-data"` no `<form>`; seção de upload inserida antes do loop de campos:

```html
<div class="flex flex-col items-center gap-3 pb-2">
    <div id="foto-preview-wrap"
         class="w-20 h-20 rounded-full overflow-hidden bg-blue-100 text-blue-600
                flex items-center justify-center text-2xl font-bold select-none">
        <span id="foto-inicial">?</span>
    </div>
    <label for="id_foto" class="cursor-pointer text-sm font-semibold text-blue-600 hover:text-blue-700 transition">
        Adicionar foto de perfil
        <span class="font-normal text-slate-400">(opcional)</span>
    </label>
    <input type="file" name="foto" id="id_foto" accept="image/*" class="sr-only">
</div>
```

JavaScript exibe preview circular imediato e mostra a inicial do `first_name` até que uma imagem seja selecionada.

**`usuario_edit.html`** — mesma estrutura; mostra foto atual (`usuario.perfil.foto.url`) se já existir, caso contrário mostra inicial. JavaScript atualiza o preview ao trocar o arquivo.

**`usuarios_list.html`** — célula de avatar:
```html
{% if u.perfil and u.perfil.foto %}
<img src="{{ u.perfil.foto.url }}" alt="" class="w-9 h-9 rounded-full object-cover flex-shrink-0">
{% else %}
<div class="w-9 h-9 rounded-full bg-blue-100 text-blue-600 font-bold text-xs
            flex items-center justify-center flex-shrink-0 uppercase">
    {{ u.first_name|first|default:u.username|first }}
</div>
{% endif %}
```

**`chamado_detail.html`** — quatro pontos atualizados com o mesmo padrão foto-ou-inicial:

| Spot | Tamanho | Cor de fallback |
|---|---|---|
| `chamado.criado_por` (cabeçalho da mensagem original) | `w-11 h-11` | âmbar |
| `resp.autor` (cada resposta na conversa) | `w-8 h-8` | azul |
| `request.user` (área do form de resposta) | `w-11 h-11` | azul |
| Observadores (painel lateral — leitura e seleção) | `w-8 h-8` | azul |

Para o spot de observadores, o prefetch foi atualizado em `chamado_detail` (view) para evitar N+1:

```python
chamado = get_object_or_404(
    Chamado.objects.prefetch_related(
        Prefetch('observadores', queryset=User.objects.select_related('perfil'))
    ),
    pk=pk
)
```

**Fallback garantido:** em todos os spots, se `perfil.foto` for falsy (campo vazio ou perfil inexistente) o círculo com inicial é exibido — comportamento idêntico ao anterior à implementação.

---

## Implementação 35 — Foto de Perfil (Upload pelo Próprio Usuário via Navbar)

**Objetivo:** qualquer usuário autenticado pode trocar sua própria foto clicando no avatar circular na navbar (ao lado do toggle dark/light), sem recarregar a página. A foto nova aparece imediatamente no navbar e nas próximas navegações em todos os pontos do sistema.

### View

`perfil_foto_view` adicionada a `core/views.py`:

```python
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
    perfil.foto = foto
    perfil.save()
    return JsonResponse({'ok': True, 'url': perfil.foto.url})
```

Retorna `{'ok': True, 'url': '...'}` em caso de sucesso ou `{'ok': False, 'erro': '...'}` em caso de erro.

### URL

`core/urls.py`:
```python
path('perfil/foto/', views.perfil_foto_view, name='perfil_foto'),
```

Rota: `POST /perfil/foto/` — protegida por `@login_required`.

### Template — `base.html`

Avatar clicável na navbar (substitui o texto "Olá, username"):

```html
<button id="btn-avatar-nav" type="button"
        title="Clique para alterar sua foto de perfil"
        class="relative rounded-full ring-2 ring-transparent
               hover:ring-blue-400 focus:outline-none focus:ring-blue-400
               transition-all shrink-0">
    {% if user.perfil.foto %}
    <img id="nav-avatar-img" src="{{ user.perfil.foto.url }}"
         class="w-8 h-8 rounded-full object-cover">
    {% else %}
    <div id="nav-avatar-ini"
         class="w-8 h-8 rounded-full bg-blue-500 text-white
                flex items-center justify-center text-sm font-bold select-none">
        {{ user.get_full_name|default:user.username|slice:":1"|upper }}
    </div>
    {% endif %}
</button>
<input type="file" id="nav-foto-input" accept="image/*" class="sr-only">
```

JavaScript (injetado antes de `{% block extra_js %}`):

```javascript
(function () {
    var btn   = document.getElementById('btn-avatar-nav');
    var input = document.getElementById('nav-foto-input');
    if (!btn || !input) return;
    btn.addEventListener('click', function () { input.click(); });
    input.addEventListener('change', function () {
        var file = this.files[0];
        if (!file) return;
        var fd = new FormData();
        fd.append('foto', file);
        fd.append('csrfmiddlewaretoken', '{{ csrf_token }}');
        btn.style.opacity = '0.5';
        fetch('{% url "perfil_foto" %}', { method: 'POST', body: fd })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                btn.style.opacity = '1';
                if (!data.ok) return;
                var url = data.url + '?t=' + Date.now();
                btn.innerHTML = '<img id="nav-avatar-img" src="' + url +
                                '" class="w-8 h-8 rounded-full object-cover">';
            })
            .catch(function () { btn.style.opacity = '1'; });
    });
})();
```

**Cache-busting:** `?t=Date.now()` é adicionado à URL retornada pela API para forçar o browser a baixar a nova imagem mesmo que o nome do arquivo seja igual ao anterior.

**Opacidade durante upload:** `btn.style.opacity = '0.5'` fornece feedback visual enquanto o arquivo é enviado; restaurado para `1` após resposta (sucesso ou erro).

---

### Implementação 36 — Backend SMTP Compatível com Python 3.12

**Arquivo criado:** `core/email_backend.py`

**Problema:** O Django 3.2 passa os parâmetros `keyfile` e `certfile` para `smtplib.SMTP_SSL` mesmo quando são `None`. O Python 3.12 removeu esses parâmetros e lança `TypeError` ao recebê-los.

**Solução:** Subclasse `Py312SMTPEmailBackend` que sobrescreve `open()` e só repassa `keyfile`/`certfile` quando não são `None`:

```python
class Py312SMTPEmailBackend(EmailBackend):
    def open(self):
        if self.connection:
            return False
        params = {'local_hostname': DNS_NAME.get_fqdn()}
        if self.timeout is not None:
            params['timeout'] = self.timeout
        if self.use_ssl:
            if self.ssl_keyfile:
                params['keyfile'] = self.ssl_keyfile
            if self.ssl_certfile:
                params['certfile'] = self.ssl_certfile
        try:
            klass = smtplib.SMTP_SSL if self.use_ssl else smtplib.SMTP
            self.connection = klass(self.host, self.port, **params)
            if not self.use_ssl and self.use_tls:
                self.connection.ehlo()
                starttls_params = {}
                if self.ssl_keyfile:
                    starttls_params['keyfile'] = self.ssl_keyfile
                if self.ssl_certfile:
                    starttls_params['certfile'] = self.ssl_certfile
                self.connection.starttls(**starttls_params)
                self.connection.ehlo()
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except OSError:
            if not self.fail_silently:
                raise
```

`disparar_email` foi atualizado para usar `backend='core.email_backend.Py312SMTPEmailBackend'` em vez do backend padrão do Django.

**`disparar_email` — novo retorno:** A função passou a retornar uma **tupla `(bool, str)`** em vez de apenas `bool`. O segundo elemento é a mensagem de erro (string vazia em caso de sucesso), permitindo que as views exibam o motivo exato da falha ao usuário via `messages.warning`.

```python
def disparar_email(assunto, mensagem, destinatarios):
    # ...
    try:
        # ... envio ...
        return True, ''
    except Exception as e:
        erro = str(e) or f'{type(e).__name__} (sem mensagem)'
        logger.error("Falha ao enviar e-mail para %s — %s", destinatarios, erro)
        return False, erro
```

Todas as chamadas a `disparar_email` foram atualizadas de `ok = disparar_email(...)` para `ok, erro = disparar_email(...)`.

---

### Implementação 37 — Campos de Contato e Migração de Anexos e Contatos

**Migrações novas (anteriormente marcadas como "intermediária"):**

| Migração | Conteúdo real |
|---|---|
| `0010_anexo.py` | `CreateModel Anexo` — cria tabela `core_anexo` com FK para `Chamado`, `User` e campos `arquivo`, `nome_original`, `tipo_mime`, `criado_em` |
| `0011_perfilusuario_contatos.py` | `AddField` de `celular`, `whatsapp` e `telefone_fixo` (CharField, max 20, nullable) ao `PerfilUsuario` |

**Campos adicionados ao modelo `PerfilUsuario`:**

```python
celular       = models.CharField(max_length=20, blank=True, null=True)
whatsapp      = models.CharField(max_length=20, blank=True, null=True)
telefone_fixo = models.CharField(max_length=20, blank=True, null=True)
```

**Forms atualizados:**

`UserRegisterForm` e `UsuarioEditForm` incluem os três campos com `_FONE_ATTRS` / `_FIXO_ATTRS` (placeholders de formatação telefônica), em `field_order` e no `save()` de ambos os forms. Valores em branco são convertidos para `None` no banco.

---

### Implementação 38 — Reset de Senha pelo Admin

**Motivação:** O admin precisava redefinir a senha de um usuário sem precisar compartilhar a senha atual. O fluxo de reset gera uma nova senha temporária, envia por e-mail e força a troca no próximo login.

**View `usuario_reset_senha` em `core/views.py`:**

```python
@login_required(login_url='login')
def usuario_reset_senha(request, pk):
    # Somente admin
    # Não pode resetar própria conta nem superusuário
    _alphabet = string.ascii_letters + string.digits + '!@#$'
    temp_password = ''.join(secrets.choice(_alphabet) for _ in range(12))
    usuario.set_password(temp_password)
    usuario.save()
    perfil.must_change_password = True
    perfil.save()
    ok_email, erro_email = disparar_email(
        f"[Digiana] Sua senha foi redefinida — {nome_completo}",
        f"Login: {usuario.username}\nSenha temporária: {temp_password}\n...",
        [usuario.email],
    )
    # Se falhar → marca email_verificar=True + messages.warning com motivo
    return redirect('usuarios_list')
```

**Proteções:**
- Não pode resetar a própria conta
- Não pode resetar superusuário
- Se o usuário não tiver e-mail: `(False, "Usuário sem e-mail cadastrado.")`
- Se SMTP falhar: marca `email_verificar=True` e exibe aviso com erro

**URL adicionada:**
```python
path('usuarios/<int:pk>/resetar-senha/', views.usuario_reset_senha, name='usuario_reset_senha'),
```

---

### Implementação 39 — Teste de Configuração SMTP

**Motivação:** Ao trocar de servidor SMTP (ex.: de Zoho Mail para Brevo), o admin precisava validar a configuração antes de depender dela para notificações reais.

**View `testar_email_view` em `core/views.py`:**

```python
@login_required(login_url='login')
def testar_email_view(request):
    # Somente admin, somente POST
    # Destinatário: campo 'destinatario' do POST ou request.user.email
    diagnostico = {
        'servidor': config.servidor_smtp,
        'porta': config.porta,
        'usuario': config.usuario,
        'ssl': config.use_ssl,
        'tls': config.use_tls,
        'senha_configurada': bool(config.senha),
    }
    ok, erro = disparar_email('[Digiana] Teste de Configuração SMTP', '...', [destinatario])
    if ok:
        return JsonResponse({'ok': True, 'destinatario': destinatario, 'diagnostico': diagnostico})
    return JsonResponse({'ok': False, 'erro': erro, 'diagnostico': diagnostico})
```

Retorna JSON com o diagnóstico completo (servidor, porta, ssl/tls, senha configurada) independentemente do resultado, permitindo ao admin identificar exatamente qual parâmetro está errado. O `template configurar_email.html` chama este endpoint via `fetch` e exibe o resultado inline na página.

**URL adicionada:**
```python
path('configuracao-email/testar/', views.testar_email_view, name='testar_email'),
```

---

### Implementação 40 — Barra de Tempo em Horas Úteis

**Motivação:** A barra de tempo calculava horas de calendário (wall-clock), o que distorcia chamados abertos no fim de semana ou à noite. O tempo relevante para SLA é o tempo em que a equipe estava disponível para atender.

**Novos helpers em `core/views.py`:**

```python
_HORA_INICIO_UTIL = 8   # 08:00
_HORA_FIM_UTIL    = 18  # 18:00

def _horas_uteis(dt_inicio, dt_fim):
    """Soma apenas os segundos que caem em seg–sex, 08h–18h (horário local)."""
    # ... itera dia a dia, acumula interseção com janela útil ...
    return total / 3600

def _horas_extra(dt_inicio, dt_fim):
    """Soma o tempo total decorrido em sábados e domingos no intervalo."""
    # ... itera dia a dia, acumula dias de fim de semana ...
    return total / 3600
```

**Escala de cores atualizada (em horas úteis):**

| Horas úteis decorridas | Cor | Tailwind |
|---|---|---|
| < 10 h (~ 1 dia útil) | Verde | `bg-emerald-500` |
| 10 h – 30 h (~1–3 dias úteis) | Azul | `bg-blue-500` |
| 30 h – 70 h (~3–7 dias úteis) | Âmbar | `bg-amber-500` |
| > 70 h (> 7 dias úteis) | Vermelho | `bg-rose-500` |

A referência de 100% da barra continua em 240 h (mas agora são 240 h úteis, equivalente a ~30 dias úteis).

**Contexto adicional em `chamado_detail`:**

| Variável nova | Conteúdo |
|---|---|
| `horas_extra` | Float — horas de fim de semana no período |
| `tempo_extra` | String legível — ex.: "1 dia e 3h" (fins de semana) |

O template exibe `tempo_extra` como informação secundária ("+ X em fins de semana") abaixo da barra de tempo.

**Formato de texto da barra:**

| Situação | Exibição |
|---|---|
| < 60 min | `"45 min"` |
| < 10 h | `"3h 20min"` |
| < 10 dias úteis | `"2h"` (horas com resto) |
| ≥ 1 dia útil | `"1 dia útil"` / `"2 dias úteis e 3h"` |

---

### Implementação 41 — Helper `_build_link` e Correção de `_build_destinatarios`

**`_build_link(request, path)` — novo helper em `core/views.py`:**

```python
def _build_link(request, path):
    """Retorna URL absoluta usando SITE_URL do settings quando configurado."""
    from django.conf import settings as _s
    base = getattr(_s, 'SITE_URL', '').rstrip('/')
    if base:
        return base + path
    return request.build_absolute_uri(path)
```

**Motivação:** `request.build_absolute_uri()` em produção no Railway gerava URLs com `http://` ou com o host interno do container em vez da URL pública. `SITE_URL` é definida em `settings.py` como `https://<RAILWAY_PUBLIC_DOMAIN>` quando em produção, garantindo que todos os links nos e-mails apontem para a URL correta. Em desenvolvimento, cai no fallback `build_absolute_uri`.

**`_build_destinatarios` — remoção do e-mail do cliente cadastrado:**

A função foi alterada para incluir **apenas usuários com login no sistema** (criador + responsável + observadores). O e-mail do `chamado.projeto.cliente` (entidade jurídica) foi removido dos destinatários.

```python
# Antes: incluía chamado.projeto.cliente.email
# Depois: apenas criador, responsável e observadores

def _build_destinatarios(chamado, extras=None):
    candidatos = []
    if chamado.criado_por and chamado.criado_por.email:
        candidatos.append(chamado.criado_por.email)
    if chamado.responsavel and chamado.responsavel.email:
        candidatos.append(chamado.responsavel.email)
    for obs in chamado.observadores.all():
        if obs.email:
            candidatos.append(obs.email)
    # ... deduplicação ...
```

**Motivo:** O e-mail do `Cliente` é o e-mail da empresa/pessoa jurídica do cadastro, que pode não ser a caixa correta para receber notificações de chamados. Usuários externos da empresa cliente já têm contas no sistema com `perfil.cliente` vinculado — eles são incluídos como `observadores` quando necessário, garantindo notificação sem envio para caixas genéricas de empresa.

---

## Estado Atual dos Arquivos

### `core/email_backend.py`

Arquivo: `core/email_backend.py` — backend SMTP customizado.

Classe `Py312SMTPEmailBackend(EmailBackend)` — corrige incompatibilidade do Django 3.2 com Python 3.12: evita passar `keyfile`/`certfile=None` para `smtplib.SMTP_SSL`, que rejeitava esses parâmetros a partir do Python 3.12. Registrado em `disparar_email` via `backend='core.email_backend.Py312SMTPEmailBackend'`.

---

### `core/models.py`

Oito modelos:

| Modelo | Campos principais |
|---|---|
| `Sistema` | `nome`, `descricao`, `ativo`, `criado_em` |
| `Cliente` | `nome`, `cpf_cnpj`, `email`, `telefone`, `criado_em` |
| `Projeto` | `cliente` (FK), `nome`, `descricao`, `criado_em` |
| `Chamado` | `projeto`, `sistema` (FK, opcional), `titulo`, `descricao`, `status`, `prioridade`, `responsavel`, `observadores` (M2M), `criado_por`, `criado_em`, `atualizado_em` |
| `PerfilUsuario` | `user` (OneToOne), `role`, `must_change_password`, `cliente` (FK, opcional), `celular`, `whatsapp`, `telefone_fixo`, `email_verificar`, `foto` (ImageField, opcional) |
| `ConfigurarEmail` | `servidor_smtp`, `porta`, `usuario`, `senha`, `use_tls`, `use_ssl`, `atualizado_em` |
| `Resposta` | `chamado` (FK), `autor` (FK nullable), `conteudo`, `criado_em`, `resposta_pai` (FK self, nullable) |
| `Anexo` | `chamado` (FK), `resposta` (FK nullable), `arquivo`, `nome_original`, `tipo_mime`, `criado_em`, `criado_por` (FK nullable) |

### `core/views.py`

**Helpers privados (sem URL):**

| Helper | Descrição |
|---|---|
| `_role(user)` | Retorna o nível de acesso (`admin / gestor / dev / usuario`) via `PerfilUsuario.role_for` |
| `_horas_uteis(dt_inicio, dt_fim)` | Soma horas seg–sex 08h–18h no intervalo (usado em `chamado_detail`) |
| `_horas_extra(dt_inicio, dt_fim)` | Soma horas de sábado e domingo no intervalo |
| `_strip_html(texto)` | Remove tags HTML (CKEditor) + decodifica entidades para texto plano |
| `_build_destinatarios(chamado, extras)` | Monta lista deduplicada de e-mails: criador + responsável + observadores — **não inclui e-mail do `Cliente` cadastrado** |
| `_build_link(request, path)` | Retorna URL absoluta usando `SITE_URL` do settings (produção) ou `request.build_absolute_uri` (dev) |
| `_aplicar_restricoes_usuario(form, user, chamado=None)` | Remove `status`/`responsavel` para gestor/usuario; remove opção `fechado` das choices para não-admin/não-responsável |
| `_status_permitido(status_novo, user, chamado=None)` | Guard server-side: impede `pendente` para não-admin/dev; impede `fechado` para não-admin/não-responsável |
| `_salvar_anexos(request, chamado)` | Persiste arquivos do `request.FILES['anexos']` como objetos `Anexo` de chamado (máx 20 MB, `resposta=None`) |
| `_salvar_anexos_resposta(request, chamado, resposta)` | Persiste arquivos do `request.FILES['anexos']` como objetos `Anexo` vinculados a uma `Resposta` específica (máx 20 MB) |
| `disparar_email(assunto, mensagem, destinatarios)` | Envia e-mail via `ConfigurarEmail` singleton via `Py312SMTPEmailBackend`; retorna **tupla `(bool, str)`** — `(True, '')` ou `(False, mensagem_erro)` |

**Views com URL:**

| View | Método | Proteção |
|---|---|---|
| `login_view` | GET/POST | Pública |
| `logout_view` | GET | Autenticado |
| `cadastro_view` | GET/POST | Somente admin — gera senha temporária, envia e-mail de boas-vindas, seta `email_verificar` se SMTP falhar |
| `dashboard` | GET | Autenticado (paginado 10/pág) |
| `dashboard_stats` | GET | Autenticado — retorna JSON com contadores para polling em tempo real |
| `clientes_list` | GET | Admin, Gestor, Dev (paginado 20/pág) |
| `cliente_create` | GET/POST | Admin, Gestor, Dev |
| `cliente_update` | GET/POST | Admin, Gestor, Dev |
| `cliente_delete` | POST | Somente admin |
| `projetos_list` | GET | Admin, Gestor, Dev (paginado 20/pág) |
| `projeto_create` | GET/POST | Admin, Gestor, Dev |
| `projeto_update` | GET/POST | Admin, Gestor, Dev |
| `projeto_delete` | POST | Somente admin |
| `chamados_list` | GET | Todos (usuário: criados por si + observados, paginado 20/pág) |
| `chamado_create` | GET/POST | Todos autenticados |
| `chamado_detail` | GET/POST | Todos (usuário: criados por si + observados) — GET: visualização; POST: salva edição se `can_edit=True` |
| `chamado_update` | GET/POST | Admin e dev: qualquer chamado; gestor/usuario: só se criador ou responsável — **sem links de template; mantida apenas como rota legacy** |
| `chamado_responder` | POST | Todos autenticados com acesso ao chamado; usuário: só se `criado_por` ou observador — cria `Resposta`, salva anexos, auto-transição pendente→em_progresso, envia e-mail |
| `chamado_reopen` | POST | Todos (usuário: só próprios) |
| `chamado_delete` | POST | Admin ou responsável do chamado |
| `sistemas_list` | GET | Somente admin (paginado 20/pág) |
| `sistema_create` | GET/POST | Somente admin |
| `sistema_update` | GET/POST | Somente admin |
| `alterar_senha_view` | GET/POST | Autenticado |
| `usuarios_list` | GET | Somente admin (paginado 20/pág) |
| `usuario_edit` | GET/POST | Somente admin |
| `usuario_delete` | POST | Somente admin |
| `usuario_reset_senha` | POST | Somente admin — gera senha temporária, envia e-mail, força `must_change_password=True` |
| `configurar_email_view` | GET/POST | Somente admin |
| `testar_email_view` | POST | Somente admin — envia e-mail de teste; retorna JSON `{ok, erro, diagnostico}` |
| `perfil_foto_view` | POST | Autenticado — salva foto em `media/avatares/`; retorna JSON `{ok, url}` |
| `upload_imagem_view` | POST | Autenticado — `@csrf_exempt`, salva imagem em `media/ckeditor/YYYY/MM/` |

### `core/forms.py`

| Form / Helper | Modelo | Descrição |
|---|---|---|
| `UserRegisterForm` | `User` + `PerfilUsuario` | `username`, `email`, `first_name`, `last_name`, `role`, `cliente`, `celular`, `whatsapp`, `telefone_fixo`, `foto` — **sem password** (gerada na view) |
| `UsuarioEditForm` | `User` + `PerfilUsuario` | `first_name`, `last_name`, `email`, `role`, `cliente`, `celular`, `whatsapp`, `telefone_fixo`, `email_verificar`, `foto` |
| `ClienteForm` | `Cliente` | `nome`, `cpf_cnpj`, `email`, `telefone` |
| `ProjetoForm` | `Projeto` | `cliente`, `nome`, `descricao` |
| `_ROLE_LABEL` | — | Dict `perfil.role → rótulo curto` (`'analista'→'System'`, `'dev'→'Dev'`, etc.) |
| `_label_usuario(obj)` | — | Função que retorna `"Nome — Perfil — Empresa"` para qualquer usuário |
| `ResponsavelChoiceField` | — | `ModelChoiceField` com `label_from_instance` usando `_label_usuario()`; queryset: `dev`+`analista`, sem superusuário |
| `ObservadorChoiceField` | — | `ModelMultipleChoiceField` com `label_from_instance` usando `_label_usuario()`; queryset: todos os roles, sem superusuário |
| `ChamadoForm` | `Chamado` | `projeto`, `sistema` (campo explícito, `required=False`, `empty_label='— Nenhum sistema —'`), `titulo`, `descricao`, `status`, `prioridade`, `responsavel` (campo explícito), `observadores` |
| `SistemaForm` | `Sistema` | `nome`, `descricao`, `ativo` |
| `ConfigurarEmailForm` | `ConfigurarEmail` | `servidor_smtp`, `porta`, `usuario`, `senha`, `use_ssl`, `use_tls` |

### `core/urls.py`

```
# Autenticação
/login/                          → login_view
/logout/                         → logout_view
/cadastro/                       → cadastro_view
/alterar-senha/                  → alterar_senha_view

# Usuários (admin only)
/usuarios/                       → usuarios_list
/usuarios/<pk>/editar/           → usuario_edit
/usuarios/<pk>/excluir/          → usuario_delete

# Dashboard
/ (raiz)                         → dashboard

# Clientes (admin, gestor, dev)
/clientes/                       → clientes_list
/clientes/novo/                  → cliente_create
/clientes/<pk>/editar/           → cliente_update
/clientes/<pk>/excluir/          → cliente_delete        (admin only)

# Projetos (admin, gestor, dev)
/projetos/                       → projetos_list
/projetos/novo/                  → projeto_create
/projetos/<pk>/editar/           → projeto_update
/projetos/<pk>/excluir/          → projeto_delete        (admin only)

# Chamados (todos autenticados)
/chamados/                       → chamados_list
/chamados/novo/                  → chamado_create
/chamados/<pk>/                  → chamado_detail
/chamados/<pk>/editar/           → chamado_update
/chamados/<pk>/responder/        → chamado_responder
/chamados/<pk>/reabrir/          → chamado_reopen
/chamados/<pk>/excluir/          → chamado_delete        (admin ou responsável)

# Sistemas (admin only)
/sistemas/                       → sistemas_list
/sistemas/novo/                  → sistema_create
/sistemas/<pk>/editar/           → sistema_update

# Configuração
/configuracao-email/             → configurar_email_view (admin only)
/configuracao-email/testar/      → testar_email_view     (POST, JSON, admin only)

# Foto de perfil (qualquer usuário autenticado)
/perfil/foto/                    → perfil_foto_view      (POST, JSON, @login_required)

# Upload de mídia
/upload/imagem/                  → upload_imagem_view    (CKEditor, csrf_exempt)

# API interna — tempo real
/api/dashboard-stats/            → dashboard_stats       (JSON, polling)
```

### `setup/settings.py` — Configurações relevantes

```python
INSTALLED_APPS = [..., 'core']

MIDDLEWARE = [
    ...
    'core.middleware.ForcePasswordChangeMiddleware',  # último na lista
]

TEMPLATES = [{
    ...
    'context_processors': [
        ...,
        'core.context_processors.role_context',  # injeta user_role
    ]
}]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
```

---

## Migrações

| Arquivo | Conteúdo |
|---|---|
| `0001_initial.py` | Cria `Cliente`, `Projeto`, `Chamado` |
| `0002_configuraremail.py` | Cria `ConfigurarEmail` |
| `0003_...` | Adiciona `use_ssl`, ajusta `porta` default, etc. |
| `0004_perfilusuario.py` | Cria `PerfilUsuario` |
| `0005_alter_perfilusuario_role.py` | Ajusta choices de role |
| `0006_alter_perfilusuario_role.py` | Ajusta choices de role (adição de gestor) |
| `0007_perfilusuario_must_change_password.py` | Adiciona campo `must_change_password` |
| `0008_auto_20260608_1806.py` | Cria `Sistema`, adiciona FK `sistema` ao `Chamado` |
| `0009_alter_chamado_status.py` | Adiciona status `pendente` ao `Chamado` |
| `0010_anexo.py` | `CreateModel Anexo` — cria tabela `core_anexo` com FK para `Chamado`, `User`; campos `arquivo`, `nome_original`, `tipo_mime`, `criado_em`, `criado_por` |
| `0011_perfilusuario_contatos.py` | `AddField` de `celular`, `whatsapp` e `telefone_fixo` (CharField max 20, nullable) ao `PerfilUsuario` |
| `0012_cliente_cpf_cnpj.py` | Adiciona campo `cpf_cnpj` ao `Cliente` |
| `0013_perfilusuario_cliente.py` | Adiciona FK `cliente` ao `PerfilUsuario` |
| `0014_chamado_observadores.py` | Adiciona M2M `observadores` ao `Chamado` — tabela `core_chamado_observadores` |
| `0015_perfilusuario_email_verificar.py` | Adiciona campo `email_verificar` ao `PerfilUsuario` |
| `0016_auto_20260610_0954.py` | Cria modelo `Resposta`; adiciona campo `resposta` (FK nullable) ao `Anexo` |
| `0017_perfilusuario_foto.py` | Adiciona campo `foto` (ImageField, `upload_to='avatares/'`) ao `PerfilUsuario` |

---

## Navbar — Links por Nível de Acesso

| Link | Admin | Gestor | Dev | Usuário |
|---|:---:|:---:|:---:|:---:|
| Dashboard | ✅ | ✅ | ✅ | ✅ |
| Chamados *(novo)* | ✅ | ✅ | ✅ | ✅ |
| Clientes | ✅ | ✅ | ✅ | ❌ |
| Projetos | ✅ | ✅ | ✅ | ❌ |
| Sistemas *(borda verde)* | ✅ | ❌ | ❌ | ❌ |
| Usuários *(borda azul)* | ✅ | ❌ | ❌ | ❌ |
| ⚙ E-mail SMTP *(borda âmbar)* | ✅ | ❌ | ❌ | ❌ |

**Link ativo:** o item correspondente à página atual recebe `bg-slate-700 text-white`. Sub-páginas (editar, detalhar, criar) ativam o item pai correspondente via `request.resolver_match.url_name`.

---

## Decisões de Arquitetura

**Por que não usar PostgreSQL?** O SQLite do Django é suficiente para o volume interno esperado e elimina dependência de servidor de banco de dados. Pode ser migrado futuramente alterando apenas o `DATABASES` em `settings.py`.

**Por que Tailwind via CDN sem build?** Reduz complexidade de setup. O projeto não exige tree-shaking agressivo; o CDN gera as classes sob demanda em tempo de execução no browser.

**Por que middleware para troca de senha e não decorador em cada view?** O middleware intercepta globalmente, eliminando o risco de esquecer de proteger uma rota nova.

**Por que `role_for()` como classmethod em vez de propriedade de instância?** Permite chamar sem instância (`PerfilUsuario.role_for(user)`) e encapsula o fallback para superusuários sem perfil.

**Por que `sistema` é `null=True, blank=True` no `Chamado`?** Para não quebrar chamados já existentes na migração e para permitir que o campo seja opcional (nem todos os chamados precisam indicar um sistema).

**Por que view separada para reabrir (`chamado_reopen`) em vez de edição normal?** A edição normal para usuários e gestores não expõe o campo `status`, logo não haveria como reabrir via form. Uma view dedicada com POST explícito é mais segura e intencionalmente clara.

**Por que `_status_permitido()` como guard separado e não apenas no form?** A remoção do campo `status` via `_aplicar_restricoes_usuario` já impede gestor e usuário de submeter status pela UI, mas não protege contra requisições POST forjadas. O guard em `views.py` garante que mesmo uma requisição artesanal não consegue setar `pendente` sem ser dev ou admin — defesa em profundidade.

**Por que a barra de tempo usa `atualizado_em` como proxy de encerramento?** O modelo não possui campo `fechado_em` dedicado; adicionar um exigiria migração e lógica extra de preenchimento. O `atualizado_em` é suficientemente preciso enquanto não houver SLA formal, pois a última atualização de um chamado fechado/resolvido coincide com a ação de encerramento na esmagadora maioria dos casos.

**Por que referência de 10 dias (240 h) para a barra atingir 100 %?** Sem SLA definido, qualquer referência é convencional. 10 dias é um prazo razoável para um chamado interno de software; a partir daí a barra fica vermelha e em 100 %, sinalizando urgência sem travar visualmente em casos extremos. Quando o SLA for implementado, basta substituir `240` pelo valor calculado em horas.

**Por que `cpf_cnpj` é `null=True, unique=True`?** O campo é opcional (nem todo cliente precisa ter CPF/CNPJ cadastrado no momento do lançamento). `unique=True` impede duplicidade quando preenchido; `null=True` permite múltiplos registros sem o campo sem violar a constraint de unicidade — o banco trata `NULL != NULL`.

**Por que `PerfilUsuario.cliente` usa `SET_NULL` em vez de `CASCADE`?** Excluir um cliente não deve remover o usuário do sistema — apenas desvincula a relação. O usuário continua operando como interno sem cliente associado.

**Por que `_build_destinatarios` e não apenas concatenar listas?** Vários stakeholders podem compartilhar o mesmo e-mail (ex.: responsável e criador são a mesma pessoa) ou um e-mail pode estar vazio. A função deduplica preservando ordem e filtra vazios em um único lugar, evitando spam acidental e erros de envio.

**Por que `_strip_html` usa `strip_tags` + `unescape` em sequência?** O `strip_tags` do Django remove as tags HTML mas preserva entidades como `&amp;` e `&nbsp;`. O `html.unescape` do Python converte essas entidades para o caractere Unicode correspondente, produzindo texto limpo e legível no corpo do e-mail.

**Por que a lista de chamados tem 20 registros por página e o dashboard tem 10?** O dashboard é uma visão rápida de contexto; 10 itens cabem na tela sem scroll e reforçam a mensagem "veja o resumo, clique para ver tudo". A lista de chamados é uma ferramenta de trabalho; 20 registros reduzem a quantidade de cliques em sessões de triagem sem sobrecarregar a página.

**Por que `request.resolver_match.url_name` e não uma variável de contexto injetada por view?** O `url_name` está disponível em qualquer template sem nenhuma adição nas views — é uma propriedade do request já presente no contexto Django. Usar uma variável de contexto exigiria que todas as views passassem `'active_nav': 'chamados'` etc., criando acoplamento. O `{% with %}` no template é autocontido e não polui nenhuma view.

**Por que `_label_usuario()` como função livre e não método do modelo?** Os rótulos são necessidade de formulário (apresentação), não de domínio. Colocar no modelo violaria separação de responsabilidades e tornaria o modelo dependente da apresentação. Como função em `forms.py`, é reutilizável nos dois campos (`ResponsavelChoiceField` e `ObservadorChoiceField`) sem duplicação.

**Por que omitir a empresa quando o usuário não tem cliente vinculado?** A empresa no rótulo vem do cadastro de Clientes — pode ser razão social de uma empresa ou até um CPF de pessoa física. Inventar um valor padrão (como o nome da empresa desenvolvedora) seria impreciso para usuários de outras organizações sem cliente registrado. Omitir o segmento torna o rótulo `"Carlos — Dev"` limpo e honesto: mostra apenas o que está efetivamente cadastrado.

**Por que admin (`diretor_ti`) não aparece nas listas de responsável e observador?** O admin é o perfil de configuração e gestão do sistema, não de atendimento. Aparecer nas listas confunde o formulário e cria expectativa de que o admin vai atender o chamado. O filtro `is_superuser=False` aliado ao fato de `diretor_ti` resultar em `is_staff=True` na criação do usuário garante a exclusão sem exigir lógica extra.

**Por que `fechar` restrito ao responsável e não ao dev em geral?** O fechamento formal é um ato de confirmação de que o problema foi resolvido por quem o tratou. Permitir que qualquer dev feche qualquer chamado abriria caminho para fechamentos indevidos. O responsável é quem tem contexto completo do atendimento; apenas ele (ou o admin) deve ter autoridade de encerrar formalmente.

**Por que remover a opção `fechado` das choices do form para não-responsável, além do guard no backend?** A remoção no form é UX: o usuário não-responsável simplesmente não vê a opção `Fechado` no select — evita confusão sobre "por que cliquei em Fechado e não funcionou". O guard no `_status_permitido` é a camada de segurança contra POST forjado. As duas camadas juntas seguem o princípio de defesa em profundidade.

**Por que `gestor` passou a ser restrito como observador (não pode mais editar chamados alheios)?** A regra estabelecida foi: entre observadores, somente `diretor_ti`, `analista` e `dev` têm autoridade de edição. `Diretor` e `Coordenador` (gestor) têm papel de acompanhamento, não de execução técnica. Antes da Impl. 26, o gestor podia editar qualquer chamado pela role — essa liberdade era uma inconsistência com o modelo de responsabilidade definido.

**Por que `novalidate` no form e não remover o atributo `required` do textarea?** O `required` no textarea é gerado automaticamente pelo Django a partir da definição do modelo (`TextField()` sem `blank=True`). Removê-lo exigiria sobrescrever o widget no `ChamadoForm` apenas para contornar o CKEditor — acoplamento artificial entre camadas. O `novalidate` desativa a validação HTML5 nativa do browser para o form inteiro, que é o comportamento correto: toda validação já acontece no servidor via `form.is_valid()`. A validação client-side nativa nunca foi necessária neste projeto.

**Por que o HTML5 `form="<id>"` e não reorganizar o DOM para evitar forms aninhados?** Reorganizar o DOM exigiria duplicar o header (uma versão dentro do form, outra fora) ou mover o `<form>` para envolver apenas o grid central, deixando o header desconectado. O atributo `form="<id>"` é a solução nativa do HTML5 exatamente para esse cenário: associa inputs e botões a um form por id, independentemente de posição no DOM. Compatibilidade: todos os browsers modernos.

**Por que FK self-referencial (`resposta_pai`) e não uma tabela de hierarquia separada?** Um nível de aninhamento (resposta → pai) é suficiente para o caso de uso: o atendente cita a mensagem anterior para contexto, não para construir árvores arbitrariamente profundas. A FK self-referencial resolve isso com uma única coluna nullable, sem JOIN extra. Se futuramente for necessário suporte a threads multi-nível, o campo já está no lugar e a query recursiva pode ser adicionada.

**Por que renderizar todas as respostas em lista plana com banner de citação, e não como árvore aninhada visualmente?** A árvore aninhada (estilo e-mail com indentação por nível) fica ilegível com mais de 3 níveis e complica o CSS. A lista cronológica plana com banner "Em resposta a X: …" é o padrão usado por ferramentas como Slack e Linear: preserva o contexto da citação sem sacrificar a legibilidade do fluxo temporal.

**Por que inicializar o CKEditor da conversa de forma lazy (na primeira interação) e não no carregamento da página?** A tela de detalhe já carrega um CKEditor para a descrição editável (quando `can_edit=True`). Inicializar um segundo CKEditor imediatamente dobraria o tempo de inicialização de JS na maioria das visitas — a grande maioria das visualizações de chamado não resulta em resposta. O lazy init elimina esse custo: o editor é criado apenas quando o usuário clica em "Responder", e a partir daí a instância é reutilizada sem recriação.

**Por que a auto-transição `pendente → em_progresso` se aplica apenas ao `criado_por` e não a qualquer resposta?** O status `pendente` é definido pelo atendente para sinalizar que está aguardando retorno do solicitante. Uma resposta do próprio atendente não deve desfazer esse status — ele mesmo colocou pendente. Apenas uma interação do solicitante (`criado_por`) confirma que o retorno esperado chegou, justificando a retomada do progresso. Respostas de admins, devs e observadores não alteram o status.

**Por que mesclar detalhe e edição em uma única view/template ao invés de redirecionar o botão "Editar" para o detalhe?** O redirecionamento seria uma solução cosmética — o atendente clicaria em "Editar" e chegaria na mesma tela de detalhe. A mesclagem real elimina a rotas, os botões duplicados e o contexto mental de "agora estou editando" versus "agora estou visualizando". Na prática, quem pode editar sempre edita; quem só observa só lê — a separação não refletia um caso de uso distinto.

**Por que `projeto` e `sistema` são enviados como `<input type="hidden">` e não como campos editáveis no detalhe?** Alterar o projeto de um chamado em andamento é uma ação de refatoração administrativa, não de atendimento. Expor esses campos no detalhe criaria superfície para erros acidentais (mover chamado para projeto errado). A edição de projeto/sistema fica restrita ao fluxo de criação ou a uma eventual view administrativa dedicada.

---

## Estudo de Responsividade — Smartphones e Tablets

### Premissa Estratégica

O sistema tem dois perfis de uso distintos por dispositivo:

| Perfil | Dispositivo | Páginas acessadas |
|---|---|---|
| **Admin** (`diretor_ti`, superuser) | Desktop — sempre | Todas, incluindo Usuários, Sistemas, E-mail SMTP |
| **Não-admin** (`usr`, `dev`, `analista`, `gestor`) | Smartphone / Tablet / Desktop | Dashboard, Chamados, Clientes\*, Projetos\* |

\*Clientes e Projetos: visíveis para `dev`, `analista`, `gestor`. O perfil `usr` vê somente Dashboard e Chamados.

**Consequência direta**: as páginas `usuarios_list`, `sistemas_list` e `configurar_email` são admin-only — desktop exclusivo, fora do escopo de adaptação mobile. O esforço se concentra exatamente nas páginas que os perfis de campo acessam.

---

### Mapa de Escopo

```
MOBILE/TABLET (adaptar)          DESKTOP ONLY (não tocar)
─────────────────────────        ────────────────────────
base.html  (navegação)           usuarios_list.html
dashboard.html                   sistemas_list.html
chamados_list.html               configurar_email.html
chamado_detail.html              usuario_edit.html
chamado_form.html                cadastro.html (admin cria usuários)
clientes_list.html  (dev/gestor)
projetos_list.html  (dev/gestor)
```

---

### Diagnóstico por Página

#### `base.html` — Shell / Navegação

**CRÍTICO**: Navegação completamente oculta em smartphones — `base.html:307` — `<nav class="hidden md:flex ...">` sem fallback. Abaixo de 768px (smartphones e tablets menores) a barra de navegação desaparece. Não existe hambúrguer, drawer ou qualquer rota alternativa entre páginas. O usuário fica preso.

Os links dentro do nav já usam condicionais de role (`{% if user_role == 'admin' %}`). O hambúrguer mobile pode reutilizar a mesma lógica: para `usr` mostraria Dashboard e Chamados; para `dev`/`gestor` adicionaria Clientes e Projetos; o bloco admin (Sistemas, Usuários, SMTP) permanece invisível no mobile porque esses perfis usam desktop.

**MODERADO**: Header direito apertado em smartphones — `base.html:343-359` — `flex items-center space-x-4`. Em 360px: ícone de tema + "Olá, **username**" + botão "Senha" + botão "Sair" numa linha de ~280px. A saudação pode ser ocultada com `hidden sm:inline` sem perda funcional.

**Funciona ✓**: `max-w-7xl px-4 sm:px-6 lg:px-8` no container principal e no `<main>`.

---

#### `dashboard.html` — Todos os perfis

**MODERADO**: Topo não empilha no mobile — `dashboard.html:18` — `flex justify-between items-center`. O relógio ao vivo + botão "Novo Chamado" dividem a mesma linha. Em 360px o botão fica comprimido contra o relógio. Sem `flex-col sm:flex-row`.

**Funciona ✓**: Cards de métricas usam `grid grid-cols-2 md:grid-cols-5 gap-4` — empilha em 2 colunas no mobile.

---

#### `chamados_list.html` — Todos os perfis

**MODERADO**: Cabeçalho não empilha — `chamados_list.html:9` — `flex justify-between items-center` sem wrapping.

**MODERADO**: Filtros transbordam em telas estreitas — `chamados_list.html:23-68`. Largura mínima acumulada `min-w-48 + min-w-40 + min-w-40` ≈ 550px numa tela de 360px. O `flex-wrap` empilha os campos mas cada um tenta ocupar sua largura mínima causando overflow horizontal.

**Funciona ✓**: Tabela envolve corretamente com `<div class="overflow-x-auto">` em `chamados_list.html:74`. A tabela de 9 colunas rola horizontalmente sem recortar.

---

#### `chamado_detail.html` — Todos os perfis

**A página mais bem adaptada do projeto.**

**Funciona ✓**:
- Cabeçalho: `flex flex-col md:flex-row justify-between items-start md:items-center gap-4`
- Botões de ação: `flex flex-wrap gap-3`
- Conteúdo principal: `grid grid-cols-1 md:grid-cols-3`
- Barra de tempo: funcional em telas até 360px

---

#### `chamado_form.html` — Todos os perfis

**MENOR**: Padding fixo `p-8` — em 360px deixa 296px para o formulário. Funciona mas apertado.

**MENOR**: CKEditor com toolbar densa (14 botões) distribui-se em 2–3 linhas no mobile, consumindo espaço vertical. Comportamento interno do CKEditor, não do Digiana.

**Funciona ✓**: `max-w-2xl mx-auto`, painel de observadores recolhível com `overflow-y-auto`, hint de observadores com `hidden sm:block`.

---

#### `clientes_list.html` — `dev`, `analista`, `gestor`

**CRÍTICO**: Tabela recorta ao invés de rolar — `clientes_list.html:17`. O `overflow-hidden` no wrapper recorta as 7 colunas. Colunas além da largura da tela ficam invisíveis e não há scroll horizontal. Contraste: `chamados_list.html` tem `<div class="overflow-x-auto">` interno — esse padrão está correto e falta aqui.

**MODERADO**: Cabeçalho não empilha — `clientes_list.html:7`.

---

#### `projetos_list.html` — `dev`, `analista`, `gestor`

**CRÍTICO**: Tabela recorta ao invés de rolar — `projetos_list.html:17`. Mesmo problema de `clientes_list`: `overflow-hidden` sem `overflow-x-auto` interno. 6 colunas recortadas no mobile.

**MODERADO**: Cabeçalho não empilha — `projetos_list.html:7`.

---

### Tabela-Resumo de Problemas

| # | Página | Linha | Problema | Severidade | Perfis afetados |
|---|---|---|---|---|---|
| 1 | `base.html` | 307 | Nav `hidden md:flex` sem hambúrguer | Crítico | Todos (mobile) |
| 2 | `clientes_list.html` | 17 | Tabela recorta — sem `overflow-x-auto` | Crítico | dev, analista, gestor |
| 3 | `projetos_list.html` | 17 | Tabela recorta — sem `overflow-x-auto` | Crítico | dev, analista, gestor |
| 4 | `base.html` | 343 | Header direito apertado | Moderado | Todos (mobile) |
| 5 | `dashboard.html` | 18 | Topo não empilha | Moderado | Todos |
| 6 | `chamados_list.html` | 9 | Cabeçalho não empilha | Moderado | Todos |
| 7 | `chamados_list.html` | 23 | Filtros com `min-w-*` transbordam | Moderado | Todos |
| 8 | `clientes_list.html` | 7 | Cabeçalho não empilha | Moderado | dev, analista, gestor |
| 9 | `projetos_list.html` | 7 | Cabeçalho não empilha | Moderado | dev, analista, gestor |
| 10 | `chamado_form.html` | 98 | `p-8` fixo, apertado em 360px | Menor | Todos |
| 11 | `chamado_form.html` | — | CKEditor toolbar densa no mobile | Menor | Todos |

**Fora do escopo** (admin-only, desktop): `usuarios_list`, `sistemas_list`, `configurar_email`, `usuario_edit`, `cadastro`.

---

### O que já funciona corretamente ✓

| Elemento | Arquivo:linha | Detalhe |
|---|---|---|
| Viewport meta | `base.html:5` | `width=device-width, initial-scale=1.0` |
| Container principal | `base.html:299,400` | `px-4 sm:px-6 lg:px-8` |
| Cards de métricas | `dashboard.html:44` | `grid-cols-2 md:grid-cols-5` |
| Cabeçalho do detalhe | `chamado_detail.html:97` | `flex-col md:flex-row` |
| Grid do detalhe | `chamado_detail.html:195` | `grid-cols-1 md:grid-cols-3` |
| Tabela de chamados | `chamados_list.html:74` | `overflow-x-auto` presente |
| Botões de ação do detalhe | `chamado_detail.html:118` | `flex flex-wrap gap-3` |
| Formulário de chamado | `chamado_form.html:97` | `max-w-2xl mx-auto` |
| Painel de observadores | `chamado_form.html:139,146` | Recolhível + scroll interno |
| Hint de observadores | `chamado_form.html:130` | `hidden sm:block` |

---

### Etapas de Implementação Recomendadas

| Etapa | O que fazer | Arquivos | Prioridade | Esforço |
|---|---|---|---|---|
| **A** | Menu hambúrguer para navegação mobile — reutiliza condicionais de role existentes | `base.html` | Crítica | Médio (~50 linhas HTML+JS) |
| **B** | `overflow-x-auto` nas tabelas de Clientes e Projetos | `clientes_list.html`, `projetos_list.html` | Crítica | Mínimo (1 linha cada) |
| **C** | Cabeçalhos das listas empilham no mobile (`flex-col sm:flex-row`) | `dashboard.html`, `chamados_list.html`, `clientes_list.html`, `projetos_list.html` | Moderada | Baixo (1 classe por arquivo) |
| **D** | Header direito: saudação "Olá," oculta no mobile | `base.html` | Moderada | Mínimo (1 classe) |
| **E** | Filtros de chamados fluidos — remover `min-w-*`, usar `flex-col sm:flex-row` | `chamados_list.html` | Moderada | Baixo |
| **F** | Padding de formulários `p-4 sm:p-8` | `chamado_form.html` | Menor | Mínimo |

---

### Garantia de Não-Regressão em Desktop

Todas as correções usam exclusivamente os prefixos `sm:` (≥ 640px) e `md:` (≥ 768px) do Tailwind. Nenhuma alteração toca o comportamento em telas ≥ 768px. O layout desktop, incluindo todas as páginas admin-only, permanece idêntico ao estado atual.

---

## Deploy Railway — Histórico e Decisões

### Infraestrutura atual (produção)

| Item | Valor |
|---|---|
| Plataforma | Railway (`railway.app`) |
| URL pública | `https://digiana-chamados-production.up.railway.app` |
| Python | 3.11 (pinado via `.python-version`) |
| Build | Railpack v0.27+ |
| WSGI | Gunicorn |
| Banco de dados | PostgreSQL (serviço Railway separado) |
| Arquivos estáticos | WhiteNoise |
| Branch deploy | `main` |

### Variáveis de ambiente Railway (serviço Django)

| Variável | Valor | Observação |
|---|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | Referência ao serviço PostgreSQL |

O Railway também injeta automaticamente `RAILWAY_PUBLIC_DOMAIN`, `RAILWAY_ENVIRONMENT_NAME`, `PGHOST`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`, `PGPORT`.

### Lógica de banco em `settings.py`

1. Tenta `DATABASE_URL` (variável manual ou referência Railway)
2. Fallback: constrói URL a partir de `PGHOST` / `PGUSER` / `PGPASSWORD` / `PGDATABASE` / `PGPORT` (injetados automaticamente)
3. Fallback final: SQLite local (apenas desenvolvimento)

### Dados iniciais — `fixtures_inicial.json`

Arquivo na raiz do projeto com 14 registros exportados do SQLite local:
- `auth.user` — admin, Edilsonmn
- `core.perfilusuario` — perfis dos dois usuários
- `core.sistema`, `core.cliente`, `core.projeto`
- `core.chamado`, `core.resposta`, `core.anexo`
- `core.configuraremail`

O Procfile carrega o fixture automaticamente no startup **se o banco estiver vazio** (sem usuários), evitando perda de acesso após redeploys.

### Procfile

```
web: mkdir -p static staticfiles && python manage.py collectstatic --noinput && python manage.py migrate && python manage.py shell -c "from django.contrib.auth.models import User; User.objects.exists() or __import__('os').system('python manage.py loaddata fixtures_inicial.json')" && gunicorn setup.wsgi --bind 0.0.0.0:$PORT
```

### Problemas resolvidos durante o deploy

| Problema | Causa | Solução |
|---|---|---|
| Python 3.13 incompatível | `cgi` module removido no 3.13; Django 3.2 usa `cgi` | `.python-version` com `3.11` |
| Attestation failure do mise | mise v2026 exige attestations para versões patch exatas | Usar versão minor `3.11` sem patch |
| `dj-database-url` conflito | versão 2.x e 3.x exigem Django ≥ 4.2 | Remover lib; parsear `DATABASE_URL` com `urllib.parse` nativo |
| `ALLOWED_HOSTS` ignorado | Variáveis manuais não estavam sendo aplicadas | Usar `RAILWAY_PUBLIC_DOMAIN` injetado automaticamente |
| Dados perdidos a cada redeploy | `DATABASE_URL` não resolvido → SQLite apagado no container | Fallback `PGHOST`/`PGUSER` + auto-loaddata no Procfile |
| Worker timeout ao testar e-mail | Conexão SMTP travada (sem timeout) derrubava o Gunicorn | `timeout=15` no `get_connection()` |

---

## Estudo — E-mail SMTP em Produção (Railway)

### Problema identificado

O envio de e-mail via `smtp.zoho.com:465` funciona perfeitamente no ambiente de desenvolvimento local mas **falha em produção no Railway** com worker timeout do Gunicorn.

**Diagnóstico:** A conexão TCP para `smtp.zoho.com:465` **trava indefinidamente** sem receber resposta (nem recusa, nem erro). O Zoho bloqueia silenciosamente ranges de IP de provedores cloud (AWS, Railway, GCP, Azure) para evitar spam. Em produção com Railway (infraestrutura AWS US-West), os pacotes são descartados pelo firewall do Zoho sem retorno.

**Evidência no log:**
```
[CRITICAL] WORKER TIMEOUT (pid:37)   ← worker morto após 5 min tentando conectar ao SMTP
```

**Por que funciona local:** IP residencial/comercial é aceito pelo Zoho. IP de cloud é bloqueado.

### O que foi tentado / descartado

| Tentativa | Resultado |
|---|---|
| Senha de aplicativo Zoho | Descartado — credenciais estão corretas (funciona local) |
| IMAP/SMTP habilitado na conta | Descartado — mesma razão |
| Políticas da organização Zoho | Descartado — mesma razão |
| Porta 465 SSL → 587 TLS | Não testado (mesmo range de IP, provável mesmo bloqueio) |

### Solução pendente — Zoho ZeptoMail

O **Zoho ZeptoMail** é o produto da própria Zoho criado especificamente para envio de e-mail transacional a partir de aplicações/servidores hospedados em cloud. Usa infraestrutura diferente do Zoho Mail pessoal/corporativo e não sofre o bloqueio de IP.

| Item | Valor |
|---|---|
| Produto | Zoho ZeptoMail |
| Site | `zeptomail.zoho.com` |
| Plano gratuito | 10.000 e-mails/mês |
| Servidor SMTP | `smtp.zeptomail.com` |
| Porta | 587 (TLS) |
| Autenticação | Token de API gerado no painel ZeptoMail |

**Passos para implementar:**
1. Criar conta em `zeptomail.zoho.com` (gratuito)
2. Adicionar e verificar o domínio `anagma.com.br`
3. Gerar o token SMTP
4. Atualizar a configuração SMTP no sistema: servidor `smtp.zeptomail.com`, porta `587`, TLS habilitado, usuário e senha gerados pelo ZeptoMail
5. Atualizar `fixtures_inicial.json` com a nova configuração

**Alternativa:** Brevo (antigo Sendinblue) — 300 e-mails/dia grátis, SMTP `smtp-relay.brevo.com:587`, funciona em cloud sem restrição.

---

## Implementação 29 — Multi-SMTP com Toggle de Ativação (Zoho + Brevo)

### O que foi construído

- Múltiplas configurações SMTP cadastradas no banco com campo `ativo` para exclusividade
- Toggle iOS-style na coluna Status da tabela de configurações (ativa/desativa com clique)
- Campo `nome` para identificar cada configuração (ex: "Zoho Mail", "Brevo Produção")
- Campo `remetente` separado do `usuario` — o "De:" pode ser diferente do login SMTP
- Botões Editar e Excluir sempre visíveis para qualquer configuração (ativa ou não)

### Migrações

| Migration | Campo adicionado |
|---|---|
| `0019_configuraremail_remetente` | `remetente` (e-mail que aparece no "De:") |
| `0020_alter_configuraremail_senha` | Amplia `max_length` do campo `senha` |
| `0021_configuraremail_usar_api` | `usar_api` (modo API HTTP Brevo) |

### View de toggle (exclusividade)

```python
@login_required(login_url='login')
def configurar_email_toggle(request, pk):
    if _role(request.user) != 'admin':
        return redirect('dashboard')
    config = get_object_or_404(ConfigurarEmail, pk=pk)
    if config.ativo:
        config.ativo = False
        config.save()
    else:
        ConfigurarEmail.objects.all().update(ativo=False)
        config.ativo = True
        config.save()
    return redirect('configurar_email')
```

### URL adicionada

```python
path('configuracao-email/<int:pk>/toggle/', views.configurar_email_toggle, name='configurar_email_toggle'),
```

---

## Implementação 30 — Envio de E-mail via API HTTP do Brevo

### Contexto e problema

Após migrar de Zoho SMTP para Brevo, o envio via SMTP (portas 465 e 587) também dava **timeout** no Railway — a porta SMTP de saída estava bloqueada pelo provedor de hospedagem. A solução definitiva foi abandonar SMTP e usar a **API HTTP do Brevo** na porta 443 (HTTPS), que nunca é bloqueada.

**Log de erro SMTP (timeout):**
```
[CRITICAL] WORKER TIMEOUT (pid:37)
```

### Campo `usar_api` no modelo

```python
# core/models.py
usar_api = models.BooleanField(
    default=False,
    verbose_name='Usar API HTTP',
    help_text='Envia via API HTTP (ignora SMTP). Use quando a porta SMTP estiver bloqueada pelo provedor.'
)
```

### Função `disparar_email` com modo API

```python
def disparar_email(assunto, mensagem, destinatarios):
    import requests as _req
    config = ConfigurarEmail.objects.filter(ativo=True).first()
    if not config:
        return False, "Nenhuma configuração de e-mail ativa."
    if not config.senha:
        return False, "Senha / chave de API não configurada."

    if config.usar_api:
        try:
            api_key  = (config.senha or '').strip()
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
            return False, erro
        except Exception as e:
            return False, str(e) or f'{type(e).__name__}'

    # fallback: envio SMTP convencional
    try:
        connection = get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host=config.servidor_smtp, port=config.porta,
            username=config.usuario, password=config.senha,
            use_tls=config.use_tls, use_ssl=config.use_ssl,
            timeout=15,
        )
        remetente = (config.remetente or config.usuario or '').strip()
        EmailMessage(assunto, mensagem, remetente, destinatarios, connection=connection).send()
        return True, ''
    except Exception as e:
        return False, str(e) or f'{type(e).__name__}'
```

### `requirements.txt` — dependência adicionada

```
requests==2.32.3
```

---

## Passo a Passo Correto — Brevo API HTTP no Railway

Este é o processo exato, na ordem correta, para que o envio de e-mail funcione em produção via Brevo.

### 1. Criar Chave API no Brevo

1. Acesse [app.brevo.com](https://app.brevo.com)
2. Menu: **SMTP & API → aba "Chaves API e MCP"**
3. Clique em **"+ Gere uma nova chave API"**
4. Nome sugerido: `Digiana Produção`
5. Clique em **Gerar**
6. **Copie a chave imediatamente** — ela começa com `xkeysib-` e só é exibida uma vez

> ⚠️ **Não confundir com a Chave SMTP** — a aba "Chaves SMTP" gera chaves `xsmtpsib-` que **não funcionam** na API HTTP. É obrigatório usar a aba **"Chaves API e MCP"** para obter a chave `xkeysib-`.

### 2. Descobrir o IP de saída do Railway

O Brevo bloqueia por padrão chamadas de IPs não autorizados. O Railway usa um IP de saída diferente do IP do seu domínio.

**Como descobrir:** tente enviar um e-mail de teste pelo Digiana — se a chave API estiver correta mas o IP ainda não autorizado, o Brevo retorna:

```
HTTP 401 — {"code":"unrecognised IP address","message":"...,IP: 52.9.19.232"}
```

O IP aparece na própria mensagem de erro. No Railway, o IP de saída é **`52.9.19.232`**.

> ⚠️ **Não confundir com o IP do domínio** — o IP `191.6.208.38` é o IP de entrada do domínio `anagma.com.br` (servidor de e-mail). O IP de saída do Railway (`52.9.19.232`) é diferente e é o que precisa ser autorizado.

### 3. Autorizar o IP no Brevo

1. Acesse **Brevo → Configurações → Segurança → aba "IPs autorizados"**
2. Clique em **"Autorizar endereços IP"**
3. Adicione: **`52.9.19.232`**
4. Salve

### 4. Verificar o remetente no Brevo

1. Acesse **Brevo → Configurações → Remetentes, Domínios e IPs**
2. Adicione e verifique o e-mail ou domínio que será usado como remetente
3. Use e-mail do domínio próprio (ex: `noreply@anagma.com.br`) — remetentes Gmail tendem a cair em spam ou ser rejeitados por SPF

### 5. Configurar no Digiana

Acesse **Configurações de E-mail → Nova Configuração** e preencha:

| Campo | Valor |
|---|---|
| Nome | `Brevo Produção` |
| **Usar API HTTP** | ✅ ativado |
| Servidor SMTP | `smtp-relay.brevo.com` *(ignorado no modo API)* |
| Porta | `587` *(ignorado no modo API)* |
| Usuário / Login SMTP | `ae6030001@smtp-brevo.com` *(ignorado no modo API)* |
| **E-mail remetente** | e-mail verificado no Brevo (ex: `noreply@anagma.com.br`) |
| **Senha** | chave API `xkeysib-...` copiada no passo 1 |
| SSL | ❌ |
| TLS | ❌ |

Após salvar, ative a configuração pelo **toggle de Status** na lista e clique em **Enviar Teste**.

### 6. Resultado esperado

```
✓ E-mail enviado com sucesso!
Modo: API HTTP · Chave: xkeysib-... (11 chars)
```

---

## Erros Comuns e Diagnóstico

| Erro | Causa | Solução |
|---|---|---|
| `WORKER TIMEOUT` | Provedor bloqueia porta SMTP 465 ou 587 | Ativar modo **Usar API HTTP** |
| `HTTP 401 — Key not found` | Usando chave SMTP (`xsmtpsib-`) no campo Senha | Criar Chave API na aba **"Chaves API e MCP"** — obtém `xkeysib-` |
| `HTTP 401 — unrecognised IP address 52.9.19.232` | IP do Railway não autorizado no Brevo | Adicionar o IP em Brevo → Configurações → Segurança → IPs autorizados |
| `HTTP 401 — unrecognised IP address 152.55.176.243` | Railway mudou o IP de saída em novo deploy | Adicionar o novo IP no Brevo (IP aparece na mensagem de erro) |
| E-mail enviado mas não chega | Remetente Gmail rejeitado por SPF/DKIM | Usar remetente de domínio próprio verificado no Brevo |
| E-mail não chega para @anagma.com.br | Domínio não verificado no Brevo — SPF falha no Zoho | Verificar domínio `anagma.com.br` no Brevo + adicionar registros DNS *(pendente)* |
| `No migrations to apply` + aviso de mudanças | Migration criada localmente mas não commitada | `git add core/migrations/0021_*.py && git commit` antes do deploy |

---

## Estudo — IP Estático no Railway (plano Trial/Hobby)

### Problema

O Railway usa um **pool rotativo de IPs de saída** — o IP pode mudar a cada redeploy ou reinício do container. Isso é incompatível com a lista de IPs autorizados do Brevo, que exige que o IP seja conhecido previamente.

IPs de saída observados até agora:
- `52.9.19.232` — primeiro deploy
- `152.55.176.243` — deploy seguinte

### Tentativa de solução — IP estático no Railway

Acessamos **Railway → Digiana-Chamados → Settings → Networking** e verificamos as opções disponíveis:

| Opção encontrada | O que faz |
|---|---|
| Custom Domain | Configura domínio próprio para acesso HTTP de entrada |
| TCP Proxy | Cria proxy TCP para conexões de **entrada** (não resolve IP de saída) |
| Private Networking | Comunicação interna entre serviços Railway |
| Outbound IPv6 | Toggle para habilitar saída em IPv6 |
| **Static Outbound IP** | **Não disponível** — requer plano Pro |

### Por que não foi possível

O Railway **não oferece IP estático de saída no plano Trial/Hobby**. A opção "Static Outbound IP" só existe no plano **Pro ($20/mês)**. No plano gratuito/trial, o IP de saída faz parte de um pool compartilhado entre vários usuários e pode mudar sem aviso.

### Soluções possíveis

| Solução | Custo | Complexidade |
|---|---|---|
| Upgrade Railway para plano Pro | $20/mês | Baixa — 1 clique + adicionar 1 IP no Brevo |
| Manter IP manualmente no Brevo | Gratuito | Baixa — adicionar o novo IP quando o erro aparecer |
| Verificar domínio `anagma.com.br` no Brevo | Gratuito | Média — configuração DNS *(resolve @anagma.com.br mas não o IP rotativo)* |

### Decisão atual

Manutenção manual do IP no Brevo: quando um novo IP aparecer na mensagem de erro `HTTP 401 — unrecognised IP address X.X.X.X`, basta adicionar esse IP em **Brevo → Configurações → Segurança → IPs autorizados**.

---

## Informações de Referência — Ambiente de Produção

| Item | Valor |
|---|---|
| Hospedagem | Railway (plano Trial → Hobby) |
| IP de entrada (domínio `anagma.com.br`) | `191.6.208.38` |
| **IPs de saída do Railway (rotativos)** | `52.9.19.232`, `152.55.176.243` |
| Login SMTP Brevo | `ae6030001@smtp-brevo.com` |
| Endpoint API Brevo | `https://api.brevo.com/v3/smtp/email` |
| Tipo de chave necessário | API (`xkeysib-`) — **não** SMTP (`xsmtpsib-`) |
| Modo de envio ativo | API HTTP (porta 443) |
| Plano Brevo | Gratuito — 300 e-mails/dia |
| Plano Railway | Trial/Hobby — sem IP estático de saída |
