# Generated manually on 2025-11-05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('car', '0042_trabajoaccion_cantidad_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='diagnosticocomponenteaccion',
            name='cantidad',
            field=models.IntegerField(default=1, help_text='Número de veces que se realizará esta acción (ej: cambiar 4 bujías)', verbose_name='Cantidad'),
        ),
        migrations.AlterField(
            model_name='diagnosticocomponenteaccion',
            name='precio_mano_obra',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Precio Unitario'),
        ),
    ]








