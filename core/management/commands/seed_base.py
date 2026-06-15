from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Cliente, Projeto, Sistema


class Command(BaseCommand):
    help = 'Cria cadastros base ausentes sem sobrescrever dados existentes.'

    def handle(self, *args, **options):
        with transaction.atomic():
            sistema, sistema_created = Sistema.objects.get_or_create(
                nome='Digiana Inteligência Artificial',
                defaults={
                    'descricao': 'Software de inteligência Artificial.',
                    'ativo': True,
                },
            )

            cliente = Cliente.objects.filter(cpf_cnpj='14.890.973/0001-58').first()
            cliente_created = False
            if cliente is None:
                cliente, cliente_created = Cliente.objects.get_or_create(
                    email='contato@anagma.com.br',
                    defaults={
                        'nome': 'Anagma Contabilidade',
                        'cpf_cnpj': '14.890.973/0001-58',
                        'telefone': '71-33211993',
                    },
                )

            projeto, projeto_created = Projeto.objects.get_or_create(
                cliente=cliente,
                nome='Digiana Inteligência Artificial',
                defaults={
                    'descricao': 'Projeto sendo construído para ser um auxiliar de contabilidade.',
                },
            )

        self._write_result('Sistema', sistema, sistema_created)
        self._write_result('Cliente', cliente, cliente_created)
        self._write_result('Projeto', projeto, projeto_created)
        self.stdout.write(self.style.SUCCESS('Seed base concluído sem sobrescrever dados existentes.'))

    def _write_result(self, label, obj, created):
        status = 'criado' if created else 'já existia'
        self.stdout.write(f'{label} {status}: {obj}')
