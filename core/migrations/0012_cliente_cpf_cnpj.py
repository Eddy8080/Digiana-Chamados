from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_perfilusuario_contatos'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='cpf_cnpj',
            field=models.CharField(blank=True, max_length=18, null=True, unique=True, verbose_name='CPF / CNPJ'),
        ),
    ]
