from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('car', '0054_delete_repuestoenstock')]
    operations = [
        migrations.AddField(model_name='administraciontaller', name='tipo_taller',
            field=models.CharField(max_length=15, default='auto', choices=[
                ('auto', 'Automóviles'), ('moto', 'Motocicletas'),
                ('bici', 'Bicicletas'), ('maquinaria', 'Maquinaria y equipos')])),
        migrations.AddField(model_name='administraciontaller', name='mostrar_jerarquia',
            field=models.BooleanField(default=False)),
        migrations.AddField(model_name='administraciontaller', name='iconos_menu',
            field=models.JSONField(default=dict, blank=True)),
    ]
