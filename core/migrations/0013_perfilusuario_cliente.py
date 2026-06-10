import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_cliente_cpf_cnpj'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfilusuario',
            name='cliente',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='usuarios',
                to='core.cliente',
                verbose_name='Cliente',
            ),
        ),
    ]
