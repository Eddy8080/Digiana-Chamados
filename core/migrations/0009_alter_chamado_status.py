from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_auto_20260608_1806'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chamado',
            name='status',
            field=models.CharField(
                choices=[
                    ('aberto', 'Aberto'),
                    ('em_progresso', 'Em Progresso'),
                    ('pendente', 'Pendente'),
                    ('resolvido', 'Resolvido'),
                    ('fechado', 'Fechado'),
                ],
                default='aberto',
                max_length=20,
            ),
        ),
    ]
