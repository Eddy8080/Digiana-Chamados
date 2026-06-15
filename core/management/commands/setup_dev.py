import os
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = 'Prepara o ambiente local de desenvolvimento sem sobrescrever dados existentes.'

    def handle(self, *args, **options):
        is_railway = bool(os.environ.get('RAILWAY_ENVIRONMENT_NAME'))
        db_engine = connection.settings_dict['ENGINE']

        if is_railway:
            raise CommandError('setup_dev não pode ser executado no Railway.')

        if 'sqlite' not in db_engine:
            raise CommandError(
                'setup_dev é permitido apenas com SQLite local. '
                'Use setup_inicial ou comandos idempotentes específicos para produção.'
            )

        fixture_path = Path(settings.BASE_DIR) / 'fixtures_inicial.json'
        if not fixture_path.exists():
            raise CommandError(f'Fixture de desenvolvimento não encontrado: {fixture_path}')

        self.stdout.write('Aplicando migrations locais...')
        call_command('migrate', interactive=False, verbosity=options.get('verbosity', 1))

        if User.objects.exists():
            self.stdout.write(
                'Usuários já existem — fixture de desenvolvimento não carregado para preservar dados locais.'
            )
            return

        self.stdout.write('Banco local vazio — carregando fixtures_inicial.json...')
        call_command('loaddata', str(fixture_path), verbosity=options.get('verbosity', 1))
        self.stdout.write(self.style.SUCCESS('Ambiente de desenvolvimento preparado com sucesso.'))
