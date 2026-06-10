from django.contrib import admin
from .models import Cliente, Projeto, Chamado, ConfigurarEmail, PerfilUsuario, Sistema


@admin.register(Sistema)
class SistemaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo', 'criado_em')
    list_filter = ('ativo',)
    search_fields = ('nome',)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'telefone', 'criado_em')
    search_fields = ('nome', 'email')

@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cliente', 'criado_em')
    list_filter = ('cliente',)
    search_fields = ('nome',)

@admin.register(Chamado)
class ChamadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'projeto', 'status', 'prioridade', 'responsavel', 'criado_em')
    list_filter = ('status', 'prioridade', 'projeto')
    search_fields = ('titulo', 'descricao')

@admin.register(ConfigurarEmail)
class ConfigurarEmailAdmin(admin.ModelAdmin):
    list_display = ('servidor_smtp', 'porta', 'usuario', 'use_tls', 'atualizado_em')

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')


