# Digiana — Sistema de Abertura de Chamados

Sistema web interno para registro e acompanhamento de chamados de suporte a sistemas de software, desenvolvido para uma empresa de contabilidade.

---

## Tecnologias

- **Python 3.x** + **Django 3.2.25**
- **SQLite** (banco de dados local via Django ORM)
- **Tailwind CSS** via CDN (sem build step)
- **E-mail** via Zoho Mail SMTP (configurável pelo painel admin)

---

## Pré-requisitos

- Python 3.9 ou superior
- pip

---

## Instalação

```bash
# 1. Clone o repositório
git clone <url-do-repositorio>
cd chamados

# 2. Crie e ative o ambiente virtual
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute as migrações
python manage.py migrate

# 5. Crie o superusuário (primeiro acesso)
python manage.py createsuperuser

# 6. Inicie o servidor
python manage.py runserver
```

Acesse em: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## Estrutura do Projeto

```
chamados/
├── setup/              # Configurações Django (settings, urls, wsgi)
├── core/               # App principal
│   ├── models.py       # Modelos de dados
│   ├── views.py        # Views e lógica de negócio
│   ├── forms.py        # Formulários
│   ├── urls.py         # Rotas do app
│   ├── admin.py        # Django Admin
│   ├── middleware.py   # Troca obrigatória de senha
│   └── context_processors.py
├── templates/          # Templates HTML
│   ├── base.html       # Layout base (navbar, dark/light mode)
│   └── core/           # Templates das telas
├── static/
├── db.sqlite3
├── manage.py
└── requirements.txt
```

---

## Funcionalidades

### Autenticação
- Login e logout
- Troca obrigatória de senha no primeiro login (novos usuários recebem senha temporária)
- Alteração de senha a qualquer momento

### Controle de Acesso (4 níveis)

| Nível | Cargos | Acesso |
|---|---|---|
| **Admin** | Diretor de Tecnologia | Tudo, incluindo usuários, sistemas e e-mail SMTP |
| **Gestor** | Diretor, Coordenador | Dashboard, clientes, projetos, chamados (sem fechar/atribuir) |
| **Dev** | Analista e Dev de Sistemas, Analista de Sistema | Dashboard, clientes, projetos, chamados completo |
| **Usuário** | Usuário | Somente seus próprios chamados |

### Chamados
- Abertura de chamado vinculado a projeto e sistema
- Edição, acompanhamento de status e prioridade
- Atribuição de responsável (Admin e Dev)
- Reabertura de chamados resolvidos ou fechados

### Clientes e Projetos
- Cadastro de clientes com e-mail e telefone
- Cadastro de projetos vinculados a clientes

### Sistemas
- Cadastro de sistemas de software (Admin)
- Sistemas ficam disponíveis como opção na abertura de chamados

### Notificações por E-mail
- E-mail automático ao abrir, atualizar e reabrir chamados
- Destinatários: responsável pelo chamado e e-mail do cliente do projeto

### Configuração de E-mail (Admin)
- Painel para configurar servidor SMTP (padrão: Zoho Mail)
- Suporte a SSL (porta 465) e TLS/STARTTLS (porta 587)

---

## Interface

- **Dark mode** como padrão, com alternância para light mode
- Transição animada entre temas (efeito circular ripple via View Transitions API)
- Logo "Dig**IA**na" com efeito glow neon ciano pulsante no trecho "IA"
- Layout responsivo com Tailwind CSS

---

## Configuração de E-mail

Acesse `/configuracao-email/` com uma conta Admin e preencha:

| Campo | Valor padrão |
|---|---|
| Servidor SMTP | `smtp.zoho.com` |
| Porta | `465` |
| E-mail remetente | `seu@zoho.com` |
| Senha | Senha de aplicativo do Zoho |
| SSL | ✅ Ativo (recomendado) |
| TLS | ❌ Inativo |

> SSL e TLS não podem ser ativados simultaneamente.

---

## Variáveis de Ambiente (Produção)

Para deploy em produção, mova as configurações sensíveis de `setup/settings.py` para variáveis de ambiente:

```env
SECRET_KEY=sua-secret-key-aqui
DEBUG=False
ALLOWED_HOSTS=seudominio.com
```

---

## Documentação Técnica

Consulte [`chamados.md`](chamados.md) para o histórico completo de implementações, decisões de arquitetura e estado atual de cada arquivo.
