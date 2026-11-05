from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('car', '0045_add_descuento_to_trabajo_adicional'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vehiculo',
            name='placa',
            field=models.CharField(max_length=10, unique=True),
        ),
        migrations.AddConstraint(
            model_name='vehiculo',
            constraint=models.UniqueConstraint(fields=('cliente', 'placa'), name='unique_vehiculo_cliente_placa'),
        ),
    ]



