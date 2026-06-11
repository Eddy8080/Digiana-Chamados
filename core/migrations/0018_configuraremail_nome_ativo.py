from django.db import migrations, models


def ativar_primeiro(apps, schema_editor):
    ConfigurarEmail = apps.get_model('core', 'ConfigurarEmail')
    primeiro = ConfigurarEmail.objects.first()
    if primeiro:
        primeiro.ativo = True
        primeiro.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_perfilusuario_foto'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuraremail',
            name='nome',
            field=models.CharField(default='Principal', max_length=100, verbose_name='Nome'),
        ),
        migrations.AddField(
            model_name='configuraremail',
            name='ativo',
            field=models.BooleanField(default=False, verbose_name='Ativo'),
        ),
        migrations.RunPython(ativar_primeiro, migrations.RunPython.noop),
    ]
