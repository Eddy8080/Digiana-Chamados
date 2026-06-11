from django.urls import path
from . import views

urlpatterns = [
    # Autenticação
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('cadastro/', views.cadastro_view, name='cadastro'),
    path('usuarios/', views.usuarios_list, name='usuarios_list'),
    path('usuarios/<int:pk>/editar/', views.usuario_edit, name='usuario_edit'),
    path('usuarios/<int:pk>/excluir/', views.usuario_delete, name='usuario_delete'),
    path('usuarios/<int:pk>/resetar-senha/', views.usuario_reset_senha, name='usuario_reset_senha'),
    path('alterar-senha/', views.alterar_senha_view, name='alterar_senha'),

    # Dashboard e Páginas principais
    path('', views.dashboard, name='dashboard'),
    
    # Clientes
    path('clientes/', views.clientes_list, name='clientes_list'),
    path('clientes/novo/', views.cliente_create, name='cliente_create'),
    path('clientes/<int:pk>/editar/', views.cliente_update, name='cliente_update'),
    path('clientes/<int:pk>/excluir/', views.cliente_delete, name='cliente_delete'),

    # Projetos
    path('projetos/', views.projetos_list, name='projetos_list'),
    path('projetos/novo/', views.projeto_create, name='projeto_create'),
    path('projetos/<int:pk>/editar/', views.projeto_update, name='projeto_update'),
    path('projetos/<int:pk>/excluir/', views.projeto_delete, name='projeto_delete'),

    # Chamados
    path('chamados/', views.chamados_list, name='chamados_list'),
    path('chamados/novo/', views.chamado_create, name='chamado_create'),
    path('chamados/<int:pk>/', views.chamado_detail, name='chamado_detail'),
    path('chamados/<int:pk>/editar/', views.chamado_update, name='chamado_update'),
    path('chamados/<int:pk>/responder/', views.chamado_responder, name='chamado_responder'),
    path('chamados/<int:pk>/reabrir/', views.chamado_reopen, name='chamado_reopen'),
    path('chamados/<int:pk>/excluir/', views.chamado_delete, name='chamado_delete'),

    # Sistemas
    path('sistemas/', views.sistemas_list, name='sistemas_list'),
    path('sistemas/novo/', views.sistema_create, name='sistema_create'),
    path('sistemas/<int:pk>/editar/', views.sistema_update, name='sistema_update'),

    # Configuração de E-mail
    path('configuracao-email/', views.configurar_email_view, name='configurar_email'),
    path('configuracao-email/nova/', views.configurar_email_create, name='configurar_email_create'),
    path('configuracao-email/testar/', views.testar_email_view, name='testar_email'),
    path('configuracao-email/<int:pk>/editar/', views.configurar_email_update, name='configurar_email_update'),
    path('configuracao-email/<int:pk>/ativar/', views.configurar_email_ativar, name='configurar_email_ativar'),
    path('configuracao-email/<int:pk>/excluir/', views.configurar_email_delete, name='configurar_email_delete'),

    # Foto de perfil (qualquer usuário autenticado)
    path('perfil/foto/', views.perfil_foto_view, name='perfil_foto'),

    # Upload de imagens (CKEditor)
    path('upload/imagem/', views.upload_imagem_view, name='upload_imagem'),

    # API interna — polling em tempo real
    path('api/dashboard-stats/', views.dashboard_stats, name='dashboard_stats'),
]
