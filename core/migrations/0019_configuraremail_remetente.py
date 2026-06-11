from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_configuraremail_nome_ativo'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuraremail',
            name='remetente',
            field=models.EmailField(blank=True, null=True, verbose_name='E-mail remetente', help_text='Aparece no "De:" das notificações. Se vazio, usa o Usuário.'),
        ),
        migrations.AlterField(
            model_name='configuraremail',
            name='usuario',
            field=models.EmailField(default='dev@anagma.com.br', verbose_name='Usuário / Login SMTP'),
        ),
    ]
