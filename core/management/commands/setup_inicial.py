import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import connection, transaction
from core.models import PerfilUsuario


class Command(BaseCommand):
    help = 'Cria superusuário inicial apenas em base vazia. Idempotente — nunca apaga dados existentes.'

    def handle(self, *args, **options):
        db_engine = connection.settings_dict['ENGINE']
        is_railway = bool(os.environ.get('RAILWAY_ENVIRONMENT_NAME'))

        if is_railway and 'sqlite' in db_engine:
            self.stderr.write(
                'ERRO CRITICO: Django está usando SQLite no Railway. '
                'DATABASE_URL ou PGHOST não está configurado. '
                'Os dados NAO serao persistidos entre deploys. '
                'Configure as variáveis de banco no painel do Railway.'
            )
            raise SystemExit(1)

        if User.objects.exists():
            self.stdout.write('Usuários já existem — setup inicial ignorado.')
            return

        username = os.environ.get('ADMIN_USERNAME', 'admin')
        email = os.environ.get('ADMIN_EMAIL', '')
        password = os.environ.get('ADMIN_PASSWORD', '')

        if not password:
            self.stderr.write(
                'Variável ADMIN_PASSWORD não definida. '
                'Configure ADMIN_PASSWORD nas variáveis de ambiente do Railway para criar o superusuário inicial.'
            )
            return

        with transaction.atomic():
            user = User.objects.create_superuser(username=username, email=email, password=password)
            PerfilUsuario.objects.create(
                user=user,
                role='diretor_ti',
                must_change_password=False,
            )

        self.stdout.write(f'Superusuário "{username}" criado com sucesso.')
